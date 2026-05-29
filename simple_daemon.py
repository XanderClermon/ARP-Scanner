# simple_daemon.py
import asyncio
import json
from pathlib import Path
from typing import List
import inspect

from config import IFACE, TARGET_NETWORK, PAUSE_TIME
from core.interfaces import ScanMode, DeviceInfo
from core.Storage import JsonStorage

# Импортируем модули
from modules.GetAddress import ArpScanner
from modules.GetName import MdnsResolver
from modules.PortScanner import PortScanner
from modules.GetOS import OSDetector
from modules.GetDevice import DeviceClassifier


class SimpleNetDaemon:
    """Простая версия демона для тестирования модулей без Redis"""

    def __init__(self):
        self.discovery = ArpScanner(target_network=TARGET_NETWORK, interface_name=IFACE)

        self.enrichers = [
            MdnsResolver(),
            PortScanner(),
            OSDetector(),
            DeviceClassifier()
        ]

        self.storage = JsonStorage(filename="devices_simple.json")
        self.mode = ScanMode.ACTIVE
        self.pause_time = PAUSE_TIME
        self._is_running = True

    async def _process_device(self, device: DeviceInfo):
        try:
            print(f"   [Process] Обработка {device.ip}...")  # ← добавил для дебага

            for enricher in self.enrichers:
                device = await enricher.enrich(device, self.mode)

            is_new = await self.storage.add_or_update(device)

            dev_type = device.extra.get("device_type", "Unknown")
            hostname = device.hostname or "—"
            os_name = device.os_family or "Unknown"

            status = "NEW" if is_new else "UP"
            print(f"[{status}] {device.ip:<15} | {os_name:<12} | {hostname:<20} | {dev_type}")

        except Exception as e:
            print(f"[!] Error processing {device.ip}: {e}")
            import traceback
            traceback.print_exc()  # ← покажет точную строку ошибки

    async def _scan_cycle(self):
        """Один цикл сканирования"""
        print(f"\n[*] Запуск цикла сканирования ({self.mode.value} mode)...")

        try:
            found_devices = await self.discovery.scan(self.mode)

            if not found_devices:
                print("[i] Устройств не найдено")
                return

            print(f"[+] Найдено устройств: {len(found_devices)}")

            tasks = [self._process_device(dev) for dev in found_devices]
            await asyncio.gather(*tasks)

        except Exception as e:
            print(f"[!] Ошибка в цикле сканирования: {e}")

    async def run(self):
        """Главный цикл"""
        print(f"[*] Simple SmartSniffer запущен в {self.mode.value} режиме")
        print(f"[*] Интерфейс: {IFACE}, сеть: {TARGET_NETWORK}")

        # Запускаем lifecycle модулей
        if hasattr(self.discovery, 'start') and inspect.iscoroutinefunction(self.discovery.start):
            await self.discovery.start()

        try:
            while self._is_running:
                await self._scan_cycle()
                await asyncio.sleep(self.pause_time)

        except asyncio.CancelledError:
            print("\n[!] Получен сигнал остановки...")
        except KeyboardInterrupt:
            print("\n[!] Остановлено пользователем")
        finally:
            # Очистка
            if hasattr(self.discovery, 'stop') and asyncio.iscoroutinefunction(self.discovery.stop):
                await self.discovery.stop()
            print("[*] Simple SmartSniffer остановлен")


if __name__ == "__main__":
    daemon = SimpleNetDaemon()
    try:
        asyncio.run(daemon.run())
    except KeyboardInterrupt:
        pass