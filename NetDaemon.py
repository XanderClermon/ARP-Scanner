import asyncio
from scanner import ArpScanner
from storage import DeviceStorage, JsonStorage
from noti import WindowsNotifier, SilentNotifier
from interfaces import *

class NetDaemon:
    def __init__(self, scanner: BaseScanner, storage: BaseStorage, notifier: BaseNotifier):
        self.scanner = scanner
        self.storage = storage
        self.notifier = notifier

    async def run(self):
        print("--- Демон запущен и сканирует сеть ---")
        try:
            while True:
                found_devices = await self.scanner.get_devices()
                for device in found_devices:
                    is_new = self.storage.add_device(device['ip'], device['mac'])
                    if is_new:
                        print(f"[NEW] {device['ip']} -> {device['mac']}")
                        self.notifier.send(
                            title="Новое устройство!",
                            message=f"IP: {device['ip']}\nMAC: {device['mac']}"
                        )
                await asyncio.sleep(3)
        except KeyboardInterrupt:
            print("\nДемон остановлен.")