# Orchestrator/EnrichmentService.py
import asyncio
from typing import List, Dict
from datetime import datetime

from core.interfaces import BaseService, DeviceInfo, BaseStorage
from .StateService import StateService


class EnrichmentService(BaseService):
    """
    Умная обработка устройств: full enrichment для новых, fast — для существующих.
    Не создаёт модули сам — получает их через конструктор.
    """

    def __init__(
            self,
            enrichers: List,  # список твоих модулей: GetName, GetOS, PortScanner, GetDevice и т.д.
            storage: BaseStorage,
            state: StateService
    ):
        self.enrichers = enrichers
        self.storage = storage
        self.state = state

        # Для оптимизации: какие модули считаем "тяжёлыми"
        self.heavy_enrichers = []  # сюда можно потом добавить PortScanner, OSDetector и т.д.

    async def start(self):
        print("[EnrichmentService] Запущен")

    async def stop(self):
        print("[EnrichmentService] Остановлен")

    async def process(self, device: DeviceInfo) -> DeviceInfo:
        """
        Главный метод: обрабатывает одно устройство
        """
        try:
            existing = await self.storage.get_by_ip(device.ip)
            is_new = existing is None

            if is_new:
                await self._full_enrichment(device)
                print(f"[NEW] {device.ip} — полный анализ")
            else:
                await self._fast_enrichment(device, existing)

            # Обновляем динамические поля
            device.last_seen = datetime.now()
            device.online = True

            # Сохраняем в хранилище
            await self.storage.add_or_update(device)
            return device

        except Exception as e:
            print(f"[!] Error enriching {device.ip}: {e}")
            import traceback
            traceback.print_exc()
            return device

    async def _full_enrichment(self, device: DeviceInfo):
        """Полная обработка для новых устройств"""
        for enricher in self.enrichers:
            try:
                device = await enricher.enrich(device, self.state.scan_mode)
            except Exception as e:
                print(f"   [!] Ошибка в enricher {enricher.__class__.__name__}: {e}")

        self.state.mark_full_scan()

    async def _fast_enrichment(self, device: DeviceInfo, existing: DeviceInfo):
        """Быстрая обработка для уже известных устройств"""
        # Копируем стабильные данные
        device.hostname = existing.hostname
        device.os_family = existing.os_family
        device.os_name = existing.os_name
        device.device_type = existing.device_type if hasattr(existing, 'device_type') else None
        device.extra = existing.extra.copy()

        # Запускаем только лёгкие / динамические enrichers
        for enricher in self.enrichers:
            enricher_name = enricher.__class__.__name__

            # Пример: PortScanner и GetStatus запускаем реже
            if "PortScanner" in enricher_name or "Status" in enricher_name:
                if self._should_scan_ports():
                    device = await enricher.enrich(device, self.state.scan_mode)
            else:
                # Hostname, OS и т.д. — не трогаем повторно
                pass

    def _should_scan_ports(self) -> bool:
        """Логика частоты сканирования портов (например раз в 3 цикла)"""
        # Можно сделать умнее позже
        return True  # временно всегда сканируем, потом настроим

    # Вспомогательный метод для будущего GetStatus
    async def set_enrichers(self, enrichers: List):
        """Если нужно динамически менять enrichers"""
        self.enrichers = enrichers