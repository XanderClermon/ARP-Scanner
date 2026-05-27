import asyncio
import threading  # Идеальное решение для изоляции синхронного Redis
from typing import List
from core.interfaces import (BaseDiscoveryModule, BaseEnricherModule, BaseStorage, DeviceInfo, ScanMode, ILifecycle)
from core.manager import SignalManager


class NetDaemon:

    def __init__(self, discovery: BaseDiscoveryModule, storage: BaseStorage, enrichers: List[BaseEnricherModule],
                 mode: ScanMode = ScanMode.ACTIVE, pause_time: float = 60.0, ):
        self.discovery = discovery
        self.storage = storage
        self.enrichers = enrichers
        self.mode = mode
        self.pause_time = pause_time

        self.manager = SignalManager()
        self._is_active = False

        self._redis_thread = threading.Thread(target=self._listen_redis_commands, daemon=True)

    def _listen_redis_commands(self):
        """Этот метод крутится в отдельном системном потоке и вообще не трогает asyncio"""
        print("[*] Redis command listener thread started.")
        while True:
            try:
                command = self.manager.get_latest_command()
                if command:
                    if command == "START" and not self._is_active:
                        print("\n[▶] Thread captured START signal. Triggering scanner...")
                        self._is_active = True
                    elif command == "STOP" and self._is_active:
                        print("\n[🛑] Thread captured STOP signal. Halting scanner...")
                        self._is_active = False
                    # Добавляем обработку переключения режимов
                    elif command == "MODE_ACTIVE":
                        print("\n[⚡] Switch target acquired: ACTIVE mode (Loud scan)")
                        self.mode = ScanMode.ACTIVE
                    elif command == "MODE_GHOST":
                        print("\n[👻] Switch target acquired: GHOST mode (Stealth listen)")
                        self.mode = ScanMode.GHOST
            except Exception as e:
                pass

    async def _manage_lifecycle(self, action: str):
        """Triggers start/stop methods for all modules supporting ILifecycle."""
        targets = [self.discovery] + self.enrichers
        for obj in targets:
            if isinstance(obj, ILifecycle):
                method = getattr(obj, action)
                await method()

    async def run(self):
        """Main execution loop."""
        print(f"[*] SmartSniffer started in {self.mode.value} mode.")
        await self._manage_lifecycle("start")

        # Стартуем поток чтения Redis прямо перед основным циклом
        self._redis_thread.start()
        print("[*] Waiting for Web UI command...")

        time_since_last_scan = self.pause_time

        try:
            while True:
                # Теперь здесь нет никакого чтения Redis! Только чистая работа по таймеру
                if self._is_active:
                    if time_since_last_scan >= self.pause_time:
                        await self._perform_scan_cycle()
                        time_since_last_scan = 0
                    else:
                        await asyncio.sleep(1)
                        time_since_last_scan += 1
                else:
                    # Если стоим на паузе — просто ждем флага из соседнего потока
                    await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            pass
        finally:
            await self._manage_lifecycle("stop")

    async def _process_single_device(self, device: DeviceInfo):
        """Runs the enrichment pipeline for a specific device and saves it."""
        try:
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
            print("[*] Starting network scan cycle...")
            found_devices = await self.discovery.scan(self.mode)
            if not found_devices:
                return

            tasks = [self._process_single_device(d) for d in found_devices]
            await asyncio.gather(*tasks)

        except Exception as e:
            print(f"[!] Scan cycle failed: {e}")