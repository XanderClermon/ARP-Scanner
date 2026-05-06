from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseNetworkModule(ABC):
    """Базовый класс для любого сетевого инструмента."""
    def __init__(self, **kwargs):
        # Позволяет передавать любые настройки (интерфейс, таймауты)
        for key, value in kwargs.items():
            setattr(self, key, value)

class BaseDiscoveryModule(BaseNetworkModule):
    """Для модулей, которые сканируют сеть целиком (например, ARP)."""
    @abstractmethod
    async def scan(self) -> List[Dict[str, Any]]:
        """Возвращает список найденных устройств: [{'ip':..., 'mac':...}]"""
        pass

class BaseEnricherModule(BaseNetworkModule):
    """Для модулей, которые изучают конкретный узел (OS, DNS, Vendor)."""
    @abstractmethod
    def enrich(self, ip: str) -> Dict[str, Any]:
        """Возвращает словарь с новыми данными об устройстве."""
        pass

class BaseStorage(ABC):
    """Для систем хранения данных."""
    @abstractmethod
    def add_device(self, ip: str, mac: str, **kwargs) -> bool:
        pass