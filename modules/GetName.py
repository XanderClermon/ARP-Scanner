import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from zeroconf import ServiceStateChange, IPVersion
from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser, AsyncServiceInfo

from core.interfaces import BaseEnricherModule, DeviceInfo, ScanMode, ILifecycle


class MdnsResolver(BaseEnricherModule, ILifecycle):
    """
    mDNS Resolver for hostname discovery.
    Passive collection in Ghost mode, active probing in Legacy mode.
    """

    def __init__(self):
        super().__init__()
        self._zc: Optional[AsyncZeroconf] = None
        self._browser: Optional[AsyncServiceBrowser] = None
        self._cache: Dict[str, str] = {}  # IP -> Hostname

        self._service_types = [
            "_http._tcp.local.",
            "_airplay._tcp.local.",
            "_raop._tcp.local.",
            "_device-info._tcp.local.",
            "_workstation._tcp.local."
        ]

    # --- ILifecycle Interface ---
    async def start(self):
        """Starts background mDNS listening."""
        self._zc = AsyncZeroconf(ip_version=IPVersion.V4Only)
        self._browser = AsyncServiceBrowser(
            self._zc.zeroconf,
            self._service_types,
            handlers=[self._on_service_change]
        )

    async def stop(self):
        """Stops mDNS browser and closer zeroconf instance."""
        if self._browser:
            await self._browser.async_cancel()
        if self._zc:
            await self._zc.async_close()

    # --- Main Logic ---
    async def enrich(self, device: DeviceInfo, mode: ScanMode) -> DeviceInfo:
        if not device.ip:
            return device

        # 1. Try passive cache first (Ghost/Legacy)
        hostname = self._cache.get(device.ip)

        # 2. If Legacy mode and no hostname, perform active query
        if not hostname and mode == ScanMode.ACTIVE:
            hostname = await self._active_query(device.ip)

        if hostname:
            device.hostname = hostname

        return device

    async def _active_query(self, ip: str) -> Optional[str]:
        """Active mDNS query attempt (Legacy mode only)."""
        if not self._zc:
            return None

        # Trying to find service info by looking at workstation type
        # In a real local network, many devices respond to this
        tasks = [
            self._zc.async_get_service_info("_workstation._tcp.local.", f"{ip}.local.", timeout=1000)
            for _ in range(1)  # Could be expanded to more types
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for info in results:
            if isinstance(info, AsyncServiceInfo) and info.server:
                hostname = info.server.rstrip('.')
                self._cache[ip] = hostname
                return hostname
        return None

    def _on_service_change(self, zc, service_type, name, state_change):
        """Standard callback to process discovered mDNS services."""
        if state_change == ServiceStateChange.Added:
            # We use ensure_future because this callback is sync
            asyncio.ensure_future(self._update_cache(zc, service_type, name))

    async def _update_cache(self, zc, service_type, name):
        """Resolves service info and populates the internal IP->Hostname map."""
        try:
            info = await zc.async_get_service_info(service_type, name, timeout=2000)
            if info and info.parsed_addresses():
                hostname = (info.server or name).split('.')[0]
                for addr in info.parsed_addresses():
                    self._cache[addr] = hostname
        except Exception:
            pass