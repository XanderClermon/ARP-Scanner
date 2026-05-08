import os
import json
from core.interfaces import BaseStorage
import redis
import time
from config import settings

class JsonStorage(BaseStorage):
    def __init__(self, filename="devices.json"):
        self.filename = filename
        self._devices = self._load()

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save(self):
        with open(self.filename, "w") as f:
            json.dump(self._devices, f, indent=4)

    def add_device(self, ip: str, mac: str, name: str = "Unknown", OS: str = "Unknow", **kwargs) -> bool:
        is_completely_new = mac not in self._devices

        device_data = {
            "ip": ip,
            "mac": mac,
            "name": name,
            "OS": OS
        }

        if is_completely_new or self._devices[mac] != device_data:
            self._devices[mac] = device_data
            self._save()
            return is_completely_new

        return False


class RedisStorage(BaseStorage):
    def __init__(self):
        self.r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )

    def add_device(self, ip, mac, **kwargs):
        # 1. Основная логика твоего хранилища (проверка на новизну и т.д.)
        # ... твой существующий код ...

        # 2. А теперь пишем в HSET для веб-интерфейса
        hostname = kwargs.get("hostname", "Unknown")
        timestamp = time.strftime("%H:%M:%S")

        # Собираем строку: "MAC|Имя|Время"
        data_string = f"{mac}|{hostname}|{timestamp}"

        # Пишем в Redis
        self.r.hset("detected_devices", ip, data_string)

        return True  # или результат проверки is_new
