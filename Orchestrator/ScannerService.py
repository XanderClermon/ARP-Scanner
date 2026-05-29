# Orchestrator/ScannerService.pyТ
import asyncio
from typing import List

from core.interfaces import BaseService, ScanMode, DeviceInfo
from .StateService import StateService

class ScannerService(BaseService):

    def __init__(self, discovery, state: StateService):
        self.discovery = discovery
        self.state = state

    async def start(self):
        print("[ScannerService] Запущен")
        if hasattr(self.discovery, 'start') and asyncio.iscoroutinefunction(self.discovery.start):
            await self.discovery.start()

    async def stop(self):
        if hasattr(self.discovery, 'stop') and asyncio.iscoroutinefunction(self.discovery.stop):
            await self.discovery.stop()
        print("[ScannerService] Остановлен")

    async def perform_scan(self) -> List[DeviceInfo]:
        try:
            current_mode = self.state.scan_mode
            print(f"[ScannerService] Вызываю discovery.scan({current_mode.value})...")

            # Защита от не-асинхронного метода
            scan_method = self.discovery.scan
            if asyncio.iscoroutinefunction(scan_method):
                devices = await scan_method(current_mode)
            else:
                print("[ScannerService] scan() не асинхронный, вызываем синхронно")
                devices = scan_method(current_mode)  # если вдруг синхронный

            print(f"[ScannerService] discovery.scan() успешно вернул {len(devices)} устройств")
            return devices or []

        except Exception as e:
            print(f"[!] КРИТИЧЕСКАЯ ОШИБКА в ScannerService.perform_scan: {e}")
            import traceback
            traceback.print_exc()
            return []