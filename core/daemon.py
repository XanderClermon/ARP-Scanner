import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List
from core.interfaces import BaseDiscoveryModule, BaseEnricherModule, BaseStorage


class NetDaemon:
    def __init__(self, discovery: BaseDiscoveryModule, storage: BaseStorage, enrichers: List[BaseEnricherModule], pause: float
    ):
        self.discovery = discovery
        self.storage = storage
        self.enrichers = enrichers
        self.pause_time = pause

        self._executor = ThreadPoolExecutor(max_workers=5)

    async def run(self):
        loop = asyncio.get_event_loop()
        print(f"--- NetDaemon запущен (Модулей обогащения: {len(self.enrichers)}) ---")

        while True:
            # 1. Поиск активных устройств (Discovery)
            found_devices = await self.discovery.scan()

            for device in found_devices:
                ip = device['ip']
                mac = device['mac']

                # Собираем данные от всех модулей обогащения в один словарь
                enriched_data = {}

                for enricher in self.enrichers:
                    # Запускаем каждый enricher (OS, Name и т.д.) в отдельном потоке
                    extra_info = await loop.run_in_executor(
                        self._executor,
                        enricher.enrich,
                        ip
                    )
                    enriched_data.update(extra_info)

                # 2. Сохраняем результат
                # Мы передаем все собранные данные (os, hostname и т.д.) через kwargs
                is_new = self.storage.add_device(
                    ip=ip,
                    mac=mac,
                    **enriched_data
                )

                # 3. Красивый лог
                status = "NEW" if is_new else "UP "
                os_label = enriched_data.get("os", "Unknown")
                name_label = enriched_data.get("hostname", "Unknown")

                print(f"[{status}] {ip: <15} | {os_label: <15} | {name_label}")

            await asyncio.sleep(self.pause_time)