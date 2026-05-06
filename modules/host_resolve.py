from core.interfaces import BaseEnricherModule

class MdnsResolver(BaseEnricherModule):
    def __init__(self):
        self._cache = {} # IP -> Hostname

    def update_service(self, zc, type, name):
        """Метод для Zeroconf"""
        info = zc.get_service_info(type, name)
        if info:
            for address in info.parsed_addresses():
                self._cache[address] = info.server.strip('.')

    def enrich(self, ip: str) -> dict:
        """Возвращает имя из кэша mDNS"""
        name = self._cache.get(ip, "Unknown")
        return {"hostname": name}