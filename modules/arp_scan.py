import asyncio
from typing import List
from scapy.all import ARP, Ether, srp

from core.interfaces import BaseDiscoveryModule
from core.interfaces import DeviceInfo   # ← используем dataclass


class ArpScanner(BaseDiscoveryModule):
    """ARP Scanner с использованием Scapy."""

    def __init__(self, target_network: str, interface_name: str):
        self.target_network = target_network
        self.interface_name = interface_name

    async def scan(self) -> List[DeviceInfo]:
        """Выполняет ARP-сканирование сети."""
        return await asyncio.to_thread(self._sync_scan)

    def _sync_scan(self) -> List[DeviceInfo]:
        """Синхронная часть сканирования."""
        devices = []

        try:
            arp = ARP(pdst=self.target_network)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether / arp

            result = srp(packet, timeout=3, iface=self.interface_name, verbose=False)[0]

            for sent, received in result:
                devices.append(
                    DeviceInfo(
                        ip=received.psrc,
                        mac=received.hwsrc,
                        last_seen=None  # будет заполнено автоматически
                    )
                )
        except Exception as e:
            print(f"[!] Ошибка при ARP-сканировании: {e}")

        return devices

    async def get_interface(self) -> str:
        """Реализация абстрактного метода."""
        return self.interface_name