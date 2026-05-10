import asyncio
import logging
from typing import Dict, Any

from core.interfaces import BaseEnricherModule
from core.interfaces import DeviceInfo
from .base import BaseOSFingerprint
from .ttl_based import TTLBasedDetector
from .tcp_stack import TCPStackDetector

logger = logging.getLogger(__name__)


class OSDetector(BaseEnricherModule):
    """
    Главный композитный детектор.
    Использует несколько стратегий + выбирает лучший результат.
    """

    def __init__(self, tcp_port: int = 80, **kwargs):
        super().__init__(**kwargs)
        self.tcp_port = tcp_port
        self.detectors: list[BaseOSFingerprint] = [
            TTLBasedDetector(),
            TCPStackDetector(tcp_port=tcp_port),
        ]

    async def enrich(self, device: DeviceInfo) -> DeviceInfo:
        try:
            result = await self.fingerprint(device.ip)

            device.os_family = result.get("os_family")
            device.os_version = result.get("os_version")
            if "extra" not in device.extra:
                device.extra = {}
            device.extra["os_confidence"] = result.get("confidence", 0)
            device.extra["os_method"] = result.get("method")

            logger.debug(f"OS detected for {device.ip}: {device.os_family} "
                        f"(conf={result.get('confidence', 0)}%)")

        except Exception as e:
            logger.warning(f"OS detection failed for {device.ip}: {e}")
            if not device.os_family:
                device.os_family = "Unknown"

        return device

    async def fingerprint(self, ip: str) -> Dict[str, Any]:
        """Запускаем все детекторы параллельно и выбираем лучший."""
        tasks = [asyncio.create_task(d.fingerprint(ip)) for d in self.detectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        best = {"os_family": "Unknown", "os_version": None, "confidence": 0, "method": "none"}

        for res in results:
            if isinstance(res, dict) and res.get("confidence", 0) > best["confidence"]:
                best = res

        return best