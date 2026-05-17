import asyncio
from typing import List, Dict
from scapy.all import ARP, Ether, srp, sniff, IPv6, ICMPv6ND_NS
from core.interfaces import BaseDiscoveryModule, DeviceInfo, ScanMode, ILifecycle


class ArpScanner(BaseDiscoveryModule, ILifecycle):

    def __init__(self, target_network: str, interface_name: str):
        super().__init__(target_network=target_network, interface_name=interface_name)
        self._passive_devices: Dict[str, DeviceInfo] = {}
        self._sniffer_task = None

    # --- ILifecycle Interface ---
    async def start(self):
        self._sniffer_task = asyncio.create_task(self._run_passive_sniffer())

    async def stop(self):
        if self._sniffer_task:
            self._sniffer_task.cancel()

    # --- Main Logic ---
    async def scan(self, mode: ScanMode) -> List[DeviceInfo]:
        if mode == ScanMode.GHOST:
            results = list(self._passive_devices.values())
            self._passive_devices.clear()
            return results

        # (IPv4 + IPv6)
        return await asyncio.to_thread(self._active_scan)

    def _active_scan(self) -> List[DeviceInfo]:
        """Active network probing (ARP + NDP)."""
        devices = []

        # 1. (IPv4)
        try:
            ans, _ = srp(
                Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=self.target_network),
                timeout=2, iface=self.interface_name, verbose=False
            )
            for _, rcv in ans:
                devices.append(DeviceInfo(ip=rcv.psrc, mac=rcv.hwsrc))
        except Exception as e:
            print(f"ARP Scan Error: {e}")

        # 2. (IPv6)
        try:
            ns_pkt = Ether(dst="33:33:00:00:00:01") / IPv6(dst="ff02::1") / ICMPv6ND_NS()
            ans, _ = srp(ns_pkt, timeout=1, iface=self.interface_name, verbose=False)
            for _, rcv in ans:
                devices.append(DeviceInfo(ip=rcv.src, mac=rcv.hwsrc))
        except Exception:
            pass

        return devices

    async def _run_passive_sniffer(self):

        def process_packet(pkt):
            if ARP in pkt and pkt[ARP].op in [1, 2]:
                ip, mac = pkt[ARP].psrc, pkt[ARP].hwsrc
            elif IPv6 in pkt and ICMPv6ND_NS in pkt:
                ip, mac = pkt[IPv6].src, pkt.src
            else:
                return

            self._passive_devices[ip] = DeviceInfo(ip=ip, mac=mac)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: sniff(
            iface=self.interface_name,
            filter="arp or (ip6 and (icmp6 proto 58))",
            prn=process_packet,
            store=0
        ))