from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseOSFingerprint(ABC):
    """Базовый интерфейс для всех стратегий OS fingerprinting (SOLID - Open/Closed)."""

    @abstractmethod
    async def fingerprint(self, ip: str) -> Dict[str, Any]:
        """
        Возвращает результат fingerprinting.
        Формат:
        {
            "os_family": str,
            "os_version": str | None,
            "confidence": float,      # 0-100
            "method": str
        }
        """
        pass