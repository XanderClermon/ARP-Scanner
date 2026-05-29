# Orchestrator/StateService.py
import asyncio
from datetime import datetime
from core.interfaces import ScanMode, BaseService


class StateService(BaseService):
    """
    Управляет состоянием демона.
    Это единый источник правды для всех остальных сервисов.
    """

    def __init__(self):
        self._is_running = True
        self._is_paused = False
        self._scan_mode = ScanMode.ACTIVE
        self._scan_interval = 15  # секунд
        self._last_full_scan = datetime.now()

        self._lock = asyncio.Lock()  # для потоко-безопасного изменения состояния

    async def start(self):
        print("[StateService] Запущен")

    async def stop(self):
        self._is_running = False
        print("[StateService] Остановлен")

    # ==================== Геттеры ====================

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    @property
    def scan_mode(self) -> ScanMode:
        return self._scan_mode

    @property
    def scan_interval(self) -> int:
        return self._scan_interval

    @property
    def last_full_scan(self) -> datetime:
        return self._last_full_scan

    # ==================== Сеттеры / Команды ====================

    async def pause(self):
        async with self._lock:
            self._is_paused = True
            print("[StateService] Сканирование приостановлено")

    async def resume(self):
        async with self._lock:
            self._is_paused = False
            print("[StateService] Сканирование возобновлено")

    async def set_mode(self, mode: ScanMode):
        async with self._lock:
            self._scan_mode = mode
            print(f"[StateService] Режим сканирования изменён на: {mode.value}")

    async def set_scan_interval(self, seconds: int):
        async with self._lock:
            if seconds >= 5:
                self._scan_interval = seconds
                print(f"[StateService] Интервал сканирования установлен: {seconds} сек")

    def mark_full_scan(self):
        """Вызывать после выполнения полного обогащения"""
        self._last_full_scan = datetime.now()

    # ==================== Утилиты ====================

    def should_do_full_enrichment(self) -> bool:
        """Логика: делать полный enrich раз в N минут или при необходимости"""
        minutes_passed = (datetime.now() - self._last_full_scan).total_seconds() / 60
        return minutes_passed > 10  # например, полный rescans раз в 10 минут