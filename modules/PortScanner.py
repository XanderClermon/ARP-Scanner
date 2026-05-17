import asyncio
from typing import List, Set
from core.interfaces import BaseEnricherModule, DeviceInfo, ScanMode


class PortScanner(BaseEnricherModule):
    """
    Asynchronous port scanner for service fingerprinting.
    Active only in Legacy mode.
    """

    def __init__(self, target_ports: List[int] = None):
        super().__init__()
        # Common ports to identify device type (HTTP, SSH, SMB, Apple, etc.)
        self.target_ports = target_ports or [
            80, 443, 21, 22, 23, 25, 53, 135, 139, 445,
            3306, 3389, 5000, 5353, 8080, 62078
        ]
        self.timeout = 1.0

    async def enrich(self, device: DeviceInfo, mode: ScanMode) -> DeviceInfo:
        """
        Scans device ports only in Legacy mode and only if not scanned before.
        """
        if mode != ScanMode.LEGACY:
            return device

        # To follow the 'only once' principle, we check if open_ports is empty
        # or implement a flag in device.extra
        if device.extra.get("ports_scanned"):
            return device

        open_ports = await self._scan_device_ports(device.ip)
        device.open_ports = open_ports
        device.extra["ports_scanned"] = True

        return device

    async def _check_port(self, ip: str, port: int) -> Optional[int]:
        """Attempts to connect to a specific port."""
        try:
            conn = asyncio.open_connection(ip, port)
            _, writer = await asyncio.wait_for(conn, timeout=self.timeout)
            writer.close()
            await writer.wait_closed()
            return port
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return None

    async def _scan_device_ports(self, ip: str) -> Set[int]:
        """Scans a list of ports concurrently."""
        tasks = [self._check_port(ip, port) for port in self.target_ports]
        results = await asyncio.gather(*tasks)

        # Filter out None results and return as a set
        return {port for port in results if port is not None}