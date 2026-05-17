import asyncio
from typing import List
from core.interfaces import (BaseDiscoveryModule, BaseEnricherModule, BaseStorage, DeviceInfo, ScanMode, ILifecycle)

class NetDaemon:

    def __init__( self, discovery: BaseDiscoveryModule, storage: BaseStorage, enrichers: List[BaseEnricherModule],
                  mode: ScanMode = ScanMode.LEGACY, pause_time: float = 60.0,):
        self.discovery = discovery
        self.storage = storage
        self.enrichers = enrichers
        self.mode = mode
        self.pause_time = pause_time
        self._is_active = True

    async def _manage_lifecycle(self, action: str):
        """Triggers start/stop methods for all modules supporting ILifecycle."""
        targets = [self.discovery] + self.enrichers
        for obj in targets:
            if isinstance(obj, ILifecycle):
                method = getattr(obj, action)
                await method()

    async def run(self):
        """Main execution loop."""
        print(f"[*] SmartSniffer started in {self.mode.value} mode")
        await self._manage_lifecycle("start")

        try:
            while True:
                # SignalManager logic can be integrated here later
                if self._is_active:
                    await self._perform_scan_cycle()
                    await asyncio.sleep(self.pause_time)
                else:
                    await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await self._manage_lifecycle("stop")

    async def _process_single_device(self, device: DeviceInfo):
        """Runs the enrichment pipeline for a specific device and saves it."""
        try:
            # Run all enrichers sequentially for this specific device
            for enricher in self.enrichers:
                device = await enricher.enrich(device, self.mode)

            await self.storage.add_or_update(device)

            status = "NEW" if device.extra.get("is_new") else "UP"
            print(f"[{status}] {device.ip:<15} | {device.os_family or 'Unknown':<10} | {device.hostname or ''}")
        except Exception as e:
            print(f"[!] Error processing {device.ip}: {e}")

    async def _perform_scan_cycle(self):
        """Discovers devices and processes them in parallel."""
        try:
            # 1. Discovery phase
            found_devices = await self.discovery.scan(self.mode)
            if not found_devices:
                return

            # 2. Enrichment & Storage phase (Parallel processing)
            # We create a task for each device to run enrichers concurrently
            tasks = [self._process_single_device(d) for d in found_devices]
            await asyncio.gather(*tasks)

        except Exception as e:
            print(f"[!] Scan cycle failed: {e}")