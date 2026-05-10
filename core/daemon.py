import asyncio
import logging
from typing import List
from datetime import datetime

from core.interfaces import (
    BaseDiscoveryModule,
    BaseEnricherModule,
    BaseStorage,
    DeviceInfo
)
from core.manager import SignalManager

# Для поддержки модулей с жизненным циклом
from modules.OS.combined import OSDetector
from modules.host_resolve import MdnsResolver   # если у тебя уже есть

logger = logging.getLogger(__name__)


class NetDaemon:
    """
    Главный оркестратор демона.
    """

    def __init__(
        self,
        discovery: BaseDiscoveryModule,
        storage: BaseStorage,
        enrichers: List[BaseEnricherModule],
        pause_time: float = 60.0,
    ):
        self.discovery = discovery
        self.storage = storage
        self.enrichers = enrichers
        self.pause_time = pause_time

        self._signal_manager = SignalManager()
        self._is_active = True

        # Специальные модули, требующие управления жизненным циклом
        self._mdns_resolver: MdnsResolver | None = None
        self._os_detector: OSDetector | None = None

        self._find_special_modules()

    def _find_special_modules(self):
        """Находим модули, которым нужен start/stop."""
        for enricher in self.enrichers:
            if isinstance(enricher, MdnsResolver):
                self._mdns_resolver = enricher
            elif isinstance(enricher, OSDetector):
                self._os_detector = enricher

    async def start(self):
        """Инициализация всех модулей перед запуском."""
        logger.info("NetDaemon starting...")

        if self._mdns_resolver:
            await self._mdns_resolver.start()
            logger.info("mDNS Resolver started")

        # OSDetector пока не требует start(), но оставляем место для будущего
        if self._os_detector:
            logger.debug("OSDetector initialized")

        logger.info(f"NetDaemon started with {len(self.enrichers)} enrichers")

    async def stop(self):
        """Корректная остановка всех модулей."""
        logger.info("NetDaemon stopping...")

        if self._mdns_resolver:
            await self._mdns_resolver.stop()

        logger.info("NetDaemon stopped")

    async def run(self):
        """Основной цикл демона."""
        await self.start()

        try:
            while True:
                await self._handle_commands()

                if self._is_active:
                    await self._perform_scan_cycle()
                    await asyncio.sleep(self.pause_time)
                else:
                    await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            logger.info("Daemon received cancellation signal")
        except Exception as e:
            logger.exception("Unexpected error in daemon loop")
        finally:
            await self.stop()

    async def _handle_commands(self):
        command = self._signal_manager.get_latest_command()

        if command == "STOP":
            if self._is_active:
                self._is_active = False
                logger.info("🛑 Scanning paused")
        elif command == "START":
            if not self._is_active:
                self._is_active = True
                logger.info("🚀 Scanning resumed")
        elif command == "SCAN_NOW":
            logger.info("Manual one-time scan triggered")

    async def _perform_scan_cycle(self):
        """Один полный цикл сканирования."""
        try:
            start_time = datetime.now()
            logger.debug("Starting network scan...")

            devices: List[DeviceInfo] = await self.discovery.scan()

            for device in devices:
                # === Обогащение всеми модулями ===
                for enricher in self.enrichers:
                    try:
                        device = await enricher.enrich(device)
                    except Exception as e:
                        logger.warning(
                            f"Enricher {enricher.__class__.__name__} failed for {device.ip}: {e}"
                        )

                # Сохранение
                is_new = await self.storage.add_or_update(device)

                status = "NEW" if is_new else "UP "
                logger.info(
                    f"[{status}] {device.ip:<15} | "
                    f"{(device.os_family or 'Unknown'):<12} | "
                    f"{(device.hostname or 'Unknown'):<25} | "
                    f"{(device.vendor or '')}"
                )

            duration = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Scan cycle completed in {duration:.1f}s ({len(devices)} devices found)")

        except Exception as e:
            logger.error(f"Error during scan cycle: {e}", exc_info=True)