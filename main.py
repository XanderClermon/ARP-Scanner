from config import IFACE, TARGET_NETWORK, PAUSE_TIME
from storage import JsonStorage
from NetDaemon import NetDaemon
from scanner import ArpScanner
from mDNS import MdnsResolver
import asyncio
from OS.detectors import BasicOSDetector
from OS.analyzer import OSAnalyzer

def FactoryDaemon():

    resolver = MdnsResolver()
    scanner = ArpScanner(target_network=TARGET_NETWORK, interface_name=IFACE)
    storage = JsonStorage()
    detector = BasicOSDetector(tcp_port=80)
    os_analyzer = OSAnalyzer()
    os_analyzer.detector = detector
    pause = PAUSE_TIME

    return NetDaemon(scanner, storage, resolver,os_analyzer, pause)

if __name__ == "__main__":
    daemon = FactoryDaemon()
    asyncio.run(daemon.run())