import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List
from core.interfaces import BaseDiscoveryModule, BaseEnricherModule, BaseStorage
from core.manager import SignalManager

class NetDaemon:
    def __init__(self, discovery: BaseDiscoveryModule, storage: BaseStorage, enrichers: List[BaseEnricherModule], pause: float
    ):
        self.discovery = discovery
        self.storage = storage
        self.enrichers = enrichers
        self.pause_time = pause

        self._executor = ThreadPoolExecutor(max_workers=5)

    async def run(self):
        manager = SignalManager()
        is_active = True
        loop = asyncio.get_event_loop()
        print(f"--- NetDaemon запущен (Модулей обогащения: {len(self.enrichers)}) ---")

        while True:
            # 1. Сначала ПРОВЕРЯЕМ команды
            command = manager.get_latest_command()

            if command == "STOP":
                is_active = False
                print("🛑 Получена команда STOP. Сканирование приостановлено.")
            elif command == "START":
                is_active = True
                print("🚀 Получена команда START. Возобновляю работу.")

            # 2. Только если активны — делаем работу
            if is_active:
                # Сканируем ТОЛЬКО здесь
                found_devices = await self.discovery.scan()

                for device in found_devices:
                    ip = device['ip']
                    mac = device['mac']
                    enriched_data = {}

                    for enricher in self.enrichers:
                        extra_info = await loop.run_in_executor(
                            self._executor,
                            enricher.enrich,
                            ip
                        )
                        enriched_data.update(extra_info)

                    is_new = self.storage.add_device(ip=ip, mac=mac, **enriched_data)

                    status = "NEW" if is_new else "UP "
                    os_label = enriched_data.get("os", "Unknown")
                    name_label = enriched_data.get("hostname", "Unknown")
                    print(f"[{status}] {ip: <15} | {os_label: <15} | {name_label}")

                # Пауза после завершения полного цикла сканирования
                await asyncio.sleep(self.pause_time)
            else:
                # Если на паузе — просто ждем команду, не нагружая сеть сканером
                await asyncio.sleep(1)