# Orchestrator/CommandService.py
import asyncio
import json
from typing import Optional, Dict, Any

from core.interfaces import BaseService
from .StateService import StateService
from .EnrichmentService import EnrichmentService


class CommandService(BaseService):
    """
    Отвечает за приём и обработку команд из Redis Streams (или других источников).
    Пока реализована заглушка — легко подключается настоящий Redis.
    """

    def __init__(
            self,
            state: StateService,
            enricher: EnrichmentService,
            redis_client=None  # будет передаваться из Factory
    ):
        self.state = state
        self.enricher = enricher
        self.redis_client = redis_client
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        print("[CommandService] Запущен")

        if self.redis_client:
            self._task = asyncio.create_task(self._listen_redis())
            print("[CommandService] Слушаем Redis Streams...")
        else:
            print("[CommandService] Redis не подключён → работаем в тестовом режиме")

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("[CommandService] Остановлен")

    async def _listen_redis(self):
        """Основной цикл слушания Redis Streams"""
        try:
            while True:
                # Здесь будет настоящий код работы с Redis Streams
                # Пока заглушка для тестирования
                await asyncio.sleep(2)

                # Пример: можно вручную тестировать команды
                # await self._handle_command({"name": "pause"})

        except asyncio.CancelledError:
            print("[CommandService] Слушатель остановлен")
        except Exception as e:
            print(f"[!] Ошибка в CommandService: {e}")

    async def _handle_command(self, command: Dict[str, Any]):
        """Обработка одной команды"""
        cmd_name = command.get("name")
        value = command.get("value")

        print(f"[CommandService] Получена команда: {cmd_name} {value or ''}")

        try:
            if cmd_name == "pause":
                await self.state.pause()

            elif cmd_name == "resume":
                await self.state.resume()

            elif cmd_name == "set_mode":
                from core.interfaces import ScanMode
                mode = ScanMode.ACTIVE if value == "active" else ScanMode.GHOST
                await self.state.set_mode(mode)

            elif cmd_name == "set_interval":
                await self.state.set_scan_interval(int(value))

            elif cmd_name == "full_rescan":
                print("[CommandService] Запущен полный перескан по команде")
                self.state.mark_full_scan()  # заставит EnrichmentService делать full

            elif cmd_name == "status":
                print(f"[CommandService] Текущее состояние: paused={self.state.is_paused}, "
                      f"mode={self.state.scan_mode.value}")

            else:
                print(f"[!] Неизвестная команда: {cmd_name}")

        except Exception as e:
            print(f"[!] Ошибка при обработке команды {cmd_name}: {e}")

    # Для тестирования команд вручную
    async def send_test_command(self, command_name: str, value=None):
        """Удобный метод для тестирования"""
        await self._handle_command({"name": command_name, "value": value})