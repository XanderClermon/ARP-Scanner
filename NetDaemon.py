import asyncio
from interfaces import *

class NetDaemon:
    def __init__(self, scanner: BaseScanner, storage: BaseStorage, pause: float):
        self.scanner = scanner
        self.storage = storage
        self.pause_time = pause

    async def run(self):
        while True:
            found_devices = await self.scanner.get_devices()
            for device in found_devices:
                if self.storage.add_device(device['ip'], device['mac']):
                    print(f"[NEW] {device['ip']} -> {device['mac']}")
                else:
                    print(f"[DEV] {device['ip']} -> {device['mac']}")
            await asyncio.sleep(self.pause_time)