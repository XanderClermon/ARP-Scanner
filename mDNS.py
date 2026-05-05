from zeroconf import ServiceListener, Zeroconf
import socket
from interfaces import BaseResolver

class MdnsResolver(BaseResolver, ServiceListener):
    def __init__(self):
        self._cache = {}

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            for addr in info.addresses:
                ip = socket.inet_ntoa(addr)
                # Очищаем имя от служебных хвостов (было "Ilya.local.", стало "Ilya")
                clean_name = name.split('.')[0]
                self._cache[ip] = clean_name

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self.add_service(zc, type_, name)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass
    # --- метод из интерфейса BaseResolver ---
    def get_name(self, ip: str) -> str:
        # 1. Проверяем то, что наслушала zeroconf
        name = self._cache.get(ip)
        if name:
            return name

        # 2. Активная попытка: Reverse DNS
        try:
            # socket.gethostbyaddr возвращает кортеж (имя, алиасы, адреса)
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except (socket.herror, socket.gaierror):
            pass

        return "Unknown"