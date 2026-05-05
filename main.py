import asyncio
from zeroconf import Zeroconf
from mDNS import MdnsResolver
from scanner import ArpScanner
from storage import JsonStorage
from NetDaemon import NetDaemon
from config import USE_NOTIFIER, IFACE, TARGET_NETWORK, PAUSE_TIME

def FactoryDaemon():

    resolver = MdnsResolver()
    zc = Zeroconf()
    scanner = ArpScanner(target_network=TARGET_NETWORK, interface_name=IFACE)
    storage = JsonStorage()
    pause = PAUSE_TIME
    return NetDaemon(scanner, storage, resolver, pause)

if __name__ == "__main__":
    daemon = FactoryDaemon()
    asyncio.run(daemon.run())