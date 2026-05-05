from abc import ABC, abstractmethod

class BaseScanner(ABC):
    @abstractmethod
    async def get_devices(self) -> list[dict]:
        """Должен вернуть список словарей типа [{'ip': '...', 'mac': '...'}]"""
        pass

class BaseStorage(ABC):
    @abstractmethod
    def add_device(self, ip: str, mac: str) -> bool:
        """Должен сохранить устройство и вернуть True, если оно новое"""
        pass