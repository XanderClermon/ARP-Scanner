import asyncio
from scanner import ArpScanner
from storage import JsonStorage
from noti import WindowsNotifier, SilentNotifier
from NetDaemon import NetDaemon
from config import USE_NOTIFIER, IFACE, TARGET_NETWORK

def FactoryDaemon():

    notifier = WindowsNotifier() if USE_NOTIFIER else SilentNotifier()
    scanner = ArpScanner(target_network=TARGET_NETWORK, interface_name=IFACE)
    storage = JsonStorage()
    return NetDaemon(scanner, storage, notifier)

if __name__ == "__main__":
    daemon = FactoryDaemon()
    asyncio.run(daemon.run())