import asyncio
from interfaces import *

class NetDaemon:
    def __init__(self, scanner: BaseScanner, storage: BaseStorage, resolver: BaseResolver ,pause: float):
        self.scanner = scanner
        self.storage = storage
        self.pause_time = pause
        self.resolver = resolver

    async def run(self):
        print(f"--- Демон запущен ---")
        while True:
            found_devices = await self.scanner.get_devices()
            for device in found_devices:
                name = self.resolver.get_name(device['ip'])
                is_new = self.storage.add_device(device['ip'], device['mac'], name)
                if is_new:
                    print(f"[NEW] {name: <15} | {device['ip']: <15} -> {device['mac']}")
                else:
                    print(f"[DEV] {name: <15} | {device['ip']: <15} -> {device['mac']}")
            await asyncio.sleep(self.pause_time)