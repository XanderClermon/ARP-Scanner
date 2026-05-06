from abc import ABC, abstractmethod

class BaseScanner(ABC):
    @abstractmethod
    async def get_devices(self) -> list[dict]:
        """Должен вернуть список словарей типа [{'ip': '...', 'mac': '...'}]"""
        pass

class BaseStorage(ABC):                                                                  # удалить
    @abstractmethod
    def add_device(self, ip: str, mac: str, name: str, os: str) -> bool:
        """Должен сохранить устройство и вернуть True, если оно новое"""
        pass

class BaseResolver(ABC):
    @abstractmethod
    def get_name(self, ip: str) -> str:
        """Метод должен вернуть имя устройства по его IP или 'Unknown'"""
        pass

class BaseOSDetector(ABC):
    @abstractmethod
    def detect(self, ip: str) -> dict:
        """Возвращает словарь с найденными признаками (TTL, Window Size и т.д.)"""
        pass