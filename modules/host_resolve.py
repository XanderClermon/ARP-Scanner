from __future__ import annotations

import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

from zeroconf import Zeroconf, ServiceStateChange, IPVersion
from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser

from core.interfaces import BaseEnricherModule
from core.interfaces import DeviceInfo  # будем использовать dataclass, который предлагал раньше

logger = logging.getLogger(__name__)


class MdnsResolver(BaseEnricherModule):
    """
    mDNS Resolver (Zeroconf/Bonjour).
    Пассивно слушает объявления + может делать активные запросы.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cache: Dict[str, dict] = {}  # ip -> {"hostname": str, "expires": datetime}
        self._zc: Optional[AsyncZeroconf] = None
        self._browser: Optional[AsyncServiceBrowser] = None
        self._lock = asyncio.Lock()

        # Какие service types слушаем (можно расширять)
        self._service_types = [
            "_http._tcp.local.",
            "_https._tcp.local.",
            "_ssh._tcp.local.",
            "_workstation._tcp.local.",
            "_device-info._tcp.local.",
            # Добавляй свои
        ]

    async def start(self) -> None:
        """Запускает background listener (вызывать из Daemon/Manager)."""
        if self._zc is not None:
            return

        self._zc = AsyncZeroconf(ip_version=IPVersion.V4Only)

        listener = AsyncServiceListener(self._cache, self._lock)
        self._browser = AsyncServiceBrowser(
            self._zc.zeroconf,
            self._service_types,
            handlers=[listener.on_service_state_change]
        )
        logger.info("mDNS Resolver started (background listener)")

    async def stop(self) -> None:
        """Корректно останавливаем."""
        if self._browser:
            await self._browser.async_cancel()
        if self._zc:
            await self._zc.async_close()
        self._zc = None
        self._browser = None

    async def enrich(self, device: DeviceInfo) -> DeviceInfo:
        """Обогащаем hostname через mDNS."""
        if not device.ip:
            return device

        hostname = await self._resolve_hostname(device.ip)

        if hostname and hostname != "Unknown":
            device.hostname = hostname
            # Можно добавить в extra больше данных при необходимости

        return device

    async def _resolve_hostname(self, ip: str) -> str:
        """Сначала кэш, потом активный запрос."""
        async with self._lock:
            cached = self._cache.get(ip)
            if cached and cached.get("expires", datetime.min) > datetime.now():
                return cached["hostname"]

        # Активный запрос, если в кэше нет или истёк
        hostname = await self._active_query(ip)

        if hostname and hostname != "Unknown":
            async with self._lock:
                self._cache[ip] = {
                    "hostname": hostname,
                    "expires": datetime.now() + timedelta(minutes=30)
                }
            return hostname

        return "Unknown"

    async def _active_query(self, ip: str) -> str:
        """Активный запрос hostname по IP через mDNS."""
        if not self._zc:
            await self.start()

        try:
            # Запрашиваем PTR запись для reverse lookup
            name = f"{ip[::-1].replace('.', '-')}.in-addr.arpa.local."
            info = await self._zc.async_get_service_info("_workstation._tcp.local.", name, timeout=1500)

            if info and info.server:
                return info.server.rstrip('.')

            # Альтернатива: попробовать несколько типов
            for service_type in self._service_types:
                # Можно попробовать получить info по разным типам...
                pass

        except Exception as e:
            logger.debug(f"mDNS active query failed for {ip}: {e}")

        return "Unknown"


class AsyncServiceListener:
    """Отдельный listener для соблюдения Single Responsibility."""

    def __init__(self, cache: Dict, lock: asyncio.Lock):
        self.cache = cache
        self.lock = lock

    def on_service_state_change(self, zc: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange):
        """Callback от Zeroconf (вызывается в отдельном потоке!)."""
        asyncio.create_task(self._handle_state_change(zc, service_type, name, state_change))

    async def _handle_state_change(self, zc: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange):
        if state_change != ServiceStateChange.Added:
            return

        try:
            info = await zc.async_get_service_info(service_type, name, timeout=1500)
            if info and info.parsed_addresses():
                for addr in info.parsed_addresses(IPVersion.V4Only):
                    hostname = (info.server or name).strip('.')
                    async with self.lock:
                        self.cache[addr] = {
                            "hostname": hostname,
                            "expires": datetime.now() + timedelta(minutes=45)
                        }
                    logger.debug(f"mDNS cache updated: {addr} -> {hostname}")
        except Exception as e:
            logger.debug(f"Failed to process mDNS service {name}: {e}")