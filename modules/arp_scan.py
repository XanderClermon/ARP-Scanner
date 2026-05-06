from core.interfaces import BaseDiscoveryModule
from scapy.all import ARP, Ether, srp
from typing import List, Dict, Any


class ArpScanner(BaseDiscoveryModule):
    def __init__(self, target_network: str, interface_name: str):
        self.target_network = target_network
        self.interface_name = interface_name

    async def scan(self) -> List[Dict[str, Any]]:
        """Реализация метода scan для поиска устройств по ARP"""
        arp_request = ARP(pdst=self.target_network)
        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast / arp_request

        answered_list = srp(
            arp_request_broadcast,
            timeout=1,
            iface=self.interface_name,
            verbose=False
        )[0]

        result = []
        for element in answered_list:
            result.append({
                "ip": element[1].psrc,
                "mac": element[1].hwsrc
            })
        return result