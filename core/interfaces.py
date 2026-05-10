from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DeviceInfo:
    """Стандартизированная структура данных об устройстве."""
    ip: str
    mac: str
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    os: Optional[str] = None
    last_seen: datetime = None
    extra: Dict[str, Any] = None
    os_family: Optional[str] = None
    os_version: Optional[str] = None

    def __post_init__(self):
        if self.last_seen is None:
            self.last_seen = datetime.now()
        if self.extra is None:
            self.extra = {}

class BaseNetworkModule(ABC):
    """Базовый класс для всех сетевых модулей."""

    def __init__(self, **kwargs):
        # Лучше использовать __dict__ или dataclass, чем setattr в цикле
        for key, value in kwargs.items():
            setattr(self, key, value)

class BaseDiscoveryModule(BaseNetworkModule):
    """Модуль обнаружения устройств (ARP, ICMP, Passive и т.д.)."""

    @abstractmethod
    async def scan(self) -> List[DeviceInfo]:
        """
        Возвращает список найденных устройств.
        Должен быть асинхронным.
        """
        pass

    @abstractmethod
    async def get_interface(self) -> str:
        """Возвращает сетевой интерфейс, на котором работает модуль."""
        pass

class BaseEnricherModule(BaseNetworkModule):
    """Модуль обогащения информации об устройстве."""

    @abstractmethod
    async def enrich(self, device: DeviceInfo) -> DeviceInfo:
        """
        Принимает DeviceInfo и возвращает обогащённую версию.
        Сделал асинхронным — почти все enrichers (DNS, mDNS, HTTP probes)
        могут содержать сетевые запросы.
        """
        pass

class BaseStorage(ABC):
    """Абстракция хранилища устройств."""

    @abstractmethod
    async def add_or_update(self, device: DeviceInfo) -> bool:
        """
        Добавляет новое или обновляет существующее устройство.
        Возвращает True, если устройство было новым.
        """
        pass

    @abstractmethod
    async def get_device(self, ip: str) -> Optional[DeviceInfo]:
        pass

    @abstractmethod
    async def get_all_devices(self) -> List[DeviceInfo]:
        pass