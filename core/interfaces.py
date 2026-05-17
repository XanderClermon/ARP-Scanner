from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class ScanMode(Enum):
    GHOST = "ghost"    # Пассивный (только слушаем)
    LEGACY = "legacy"  # Активный (сканируем, пингуем)

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
    async def add_or_update(self, device: DeviceInfo) -> bool: pass
    @abstractmethod
    async def get_all_devices(self) -> List[DeviceInfo]: pass