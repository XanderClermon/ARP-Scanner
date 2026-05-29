# Orchestrator/NetDaemon.py
import asyncio
from typing import List

from core.interfaces import BaseService, DeviceInfo, BaseStorage
from .StateService import StateService
from .ScannerService import ScannerService
from .EnrichmentService import EnrichmentService
from .CommandService import CommandService


class NetDaemon:
    """
    Главный демон. Тонкий оркестратор.
    Не создаёт модули сам — получает всё через фабрику из main.py
    """

    def __init__(
            self,
            discovery,  # ArpScanner (или будущий ArpScannerV2)
            enrichers: List,  # [GetName, GetOS, PortScanner, GetDevice, ...]
            storage: BaseStorage,
            redis_client=None
    ):
        self.state = StateService()

        self.scanner = ScannerService(discovery=discovery, state=self.state)
        self.enricher = EnrichmentService(enrichers=enrichers, storage=storage, state=self.state)
        self.commands = CommandService(state=self.state, enricher=self.enricher, redis_client=redis_client)

        self._tasks = []

    async def start(self):
        """Запуск всех компонентов"""
        print("[NetDaemon] Запуск Smart Sniffer...")

        # Запускаем все сервисы
        await asyncio.gather(
            self.state.start(),
            self.scanner.start(),
            self.enricher.start(),
            self.commands.start(),
        )

        # Запускаем основные циклы
        self._tasks = [
            asyncio.create_task(self._scanning_loop()),
            # asyncio.create_task(self._health_check_loop())  # можно добавить позже
        ]

        print("[NetDaemon] Успешно запущен")

    async def stop(self):
        """Graceful shutdown"""
        print("[NetDaemon] Остановка...")

        # Останавливаем все сервисы
        await asyncio.gather(
            self.scanner.stop(),
            self.enricher.stop(),
            self.commands.stop(),
            self.state.stop(),
            return_exceptions=True
        )

        # Отменяем задачи
        for task in self._tasks:
            if not task.done():
                task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        print("[NetDaemon] Полностью остановлен")

    async def _scanning_loop(self):
        """Основной цикл сканирования"""
        while self.state.is_running:
            if self.state.is_paused:
                await asyncio.sleep(1)
                continue

            try:
                # 1. Сканируем сеть
                raw_devices: List[DeviceInfo] = await self.scanner.perform_scan()

                if not raw_devices:
                    await asyncio.sleep(self.state.scan_interval)
                    continue

                # 2. Обрабатываем каждое устройство
                for device in raw_devices:
                    await self.enricher.process(device)

            except Exception as e:
                print(f"[!] Критическая ошибка в scanning_loop: {e}")

            await asyncio.sleep(self.state.scan_interval)

    # Методы для управления из CommandService или тестов
    async def pause(self):
        await self.state.pause()

    async def resume(self):
        await self.state.resume()

    async def send_command(self, cmd_name: str, value=None):
        """Удобный метод для отправки команд"""
        await self.commands.send_test_command(cmd_name, value)