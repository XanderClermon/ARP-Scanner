import asyncio
from config import IFACE, TARGET_NETWORK, PAUSE_TIME

from core.interfaces import ScanMode
from core.Storage import JsonStorage, RedisStorage
from core.Daemon import NetDaemon

from modules.GetAddress import ArpScanner
from modules.GetName import MdnsResolver
from modules.PortScanner import PortScanner
from modules.GetOS import OSDetector
from modules.GetDevice import DeviceClassifier


def FactoryDaemon():
    discovery = ArpScanner(target_network=TARGET_NETWORK, interface_name=IFACE)

    enrichers = [
        MdnsResolver(),  # Resolve Hostnames (passive/active)
        PortScanner(),  # Identify open ports (active only)
        OSDetector(),  # Detect OS family based on names/ports
        DeviceClassifier()  # Classify device type (PC, Mobile, etc.)
    ]

    storage = RedisStorage()

    return NetDaemon( discovery=discovery, storage=storage, enrichers=enrichers, mode=ScanMode.LEGACY, pause_time=PAUSE_TIME
    )


if __name__ == "__main__":
    daemon = FactoryDaemon()
    try:
        asyncio.run(daemon.run())
    except KeyboardInterrupt:
        print("\n[!] SmartSniffer stopped by user")