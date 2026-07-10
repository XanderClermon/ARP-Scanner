import asyncio
from config import IFACE, TARGET_NETWORK, PAUSE_TIME
from core.Storage import JsonStorage, RedisStorage
from Orchestrator.NetDaemon import NetDaemon
from modules.GetAddress import ArpScanner
from modules.GetName import MdnsResolver
from modules.PortScanner import PortScanner
from modules.GetOS import OSDetector
from modules.GetDevice import DeviceClassifier


def FactoryDaemon():

    discovery = ArpScanner(
        target_network=TARGET_NETWORK,
        interface_name=IFACE
    )

    enrichers = [
        MdnsResolver(),  # Hostname resolution
        PortScanner(),  # Open ports
        OSDetector(),  # OS detection
        DeviceClassifier()  # Device type classification
    ]

    # storage = RedisStorage()      # можно переключать
    storage = JsonStorage(filename="devices.json")

    return NetDaemon(
        discovery=discovery,
        enrichers=enrichers,
        storage=storage,
        redis_client=None  
    )


if __name__ == "__main__":
    daemon = FactoryDaemon()

    try:
        asyncio.run(daemon.start()) 
    except KeyboardInterrupt:
        print("\n[!] SmartSniffer stopped by user")
    except Exception as e:
        print(f"[!] Critical error: {e}")
