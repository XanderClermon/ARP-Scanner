import asyncio
from interfaces import *
from concurrent.futures import ThreadPoolExecutor

class NetDaemon:
    def __init__(self, scanner: BaseScanner, storage: BaseStorage, resolver: BaseResolver ,os_analyzer, pause: float):
        self.scanner = scanner
        self.storage = storage
        self.pause_time = pause
        self.resolver = resolver
        self.os_analyzer = os_analyzer
        self._executor = ThreadPoolExecutor(max_workers=3)

    async def run(self):
        loop = asyncio.get_event_loop()
        print(f"--- Демон запущен ---")
        while True:
            found_devices = await self.scanner.get_devices()
            for device in found_devices:
                ip = device['ip']
                os_info = await loop.run_in_executor(self._executor, self.os_analyzer.analyze, ip, self.os_analyzer.detector)
                name = self.resolver.get_name(device['ip'])
                is_new = self.storage.add_device(device['ip'], device['mac'], name, os_info.os_name)
                if is_new: print(f"[NEW] {name} | {device['ip']} -> {device['mac']} ")
            await asyncio.sleep(self.pause_time)