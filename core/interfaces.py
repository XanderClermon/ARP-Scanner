from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class ScanMode(Enum):
    ACTIVE = "active"
    GHOST = "ghost"

@dataclass
class DeviceInfo:
    ip: str
    mac: str
    hostname: Optional[str] = None
    os_family: Optional[str] = None
    open_ports: Set[int] = field(default_factory=set)
    extra: Dict[str, Any] = field(default_factory=dict)

class ILifecycle(ABC):
    """Интерфейс для модулей, требующих инициализации (start/stop)."""
    async def start(self): pass
    async def stop(self): pass

class BaseNetworkModule(ABC):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class BaseDiscoveryModule(BaseNetworkModule, ILifecycle):
    @abstractmethod
    async def scan(self, mode: ScanMode) -> List[DeviceInfo]: pass

class BaseEnricherModule(BaseNetworkModule, ILifecycle):
    @abstractmethod
    async def enrich(self, device: DeviceInfo, mode: ScanMode) -> DeviceInfo: pass

class BaseStorage(ABC):
    @abstractmethod
    async def add_or_update(self, device: DeviceInfo) -> bool:
        """Добавляет или обновляет устройство. Возвращает True, если устройство было новым."""
        pass

    @abstractmethod
    async def get_all_devices(self) -> List[DeviceInfo]:
        pass

    # === Новые методы (очень важны для новой архитектуры) ===
    @abstractmethod
    async def get_by_ip(self, ip: str) -> Optional[DeviceInfo]:
        """Получить одно устройство по IP"""
        pass

    @abstractmethod
    async def get_online_devices(self) -> List[DeviceInfo]:
        """Получить все онлайн устройства"""
        pass


# Новый интерфейс для сервисов оркестратора
class BaseService(ABC):
    """Базовый интерфейс для всех сервисов в Orchestrator"""
    async def start(self):
        pass

    async def stop(self):
        pass