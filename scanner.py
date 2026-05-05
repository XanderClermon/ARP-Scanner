import asyncio
from scapy.layers.l2 import ARP, Ether, srp
from interfaces import BaseScanner


class ArpScanner(BaseScanner):
    def __init__(self, target_network: str, interface_name: str):
        self.target_network = target_network
        self.interface_name = interface_name

    async def get_devices(self) -> list[dict]:
        return await asyncio.to_thread(self._run_scan)

    def _run_scan(self) -> list[dict]:
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        arp = ARP(pdst=self.target_network)

        answered, _ = srp(
            ether / arp,
            timeout=2,
            verbose=0,
            iface=self.interface_name
        )

        results = []
        for _, received in answered:
            results.append({'ip': received.psrc, 'mac': received.hwsrc})
        return results