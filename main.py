from config import IFACE, TARGET_NETWORK, PAUSE_TIME
from core.storage import JsonStorage, RedisStorage
from core.daemon import NetDaemon
from modules.arp_scan import ArpScanner
from modules.host_resolve import MdnsResolver
import asyncio
from modules.OS.combined import OSDetector

def FactoryDaemon():
    discovery = ArpScanner(target_network=TARGET_NETWORK, interface_name=IFACE)
    enrichers = [MdnsResolver(), OSDetector(tcp_port=80)]
    storage = JsonStorage()
    pause = PAUSE_TIME
    return NetDaemon(discovery,storage,enrichers,pause)

if __name__ == "__main__":
    daemon = FactoryDaemon()
    asyncio.run(daemon.run())