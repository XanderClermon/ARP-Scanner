import redis
import time
from config import settings

import json
import asyncio
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from core.interfaces import BaseStorage
from core.interfaces import DeviceInfo

class JsonStorage(BaseStorage):
    """Хранилище устройств в JSON-файле."""

    def __init__(self, filename: str = "devices.json"):
        self.filename = Path(filename)
        self._data: Dict[str, dict] = {}  # ip -> device dict

    async def add_or_update(self, device: DeviceInfo) -> bool:
        """Добавляет или обновляет устройство. Возвращает True, если устройство новое."""
        return await asyncio.to_thread(self._sync_add_or_update, device)

    def _sync_add_or_update(self, device: DeviceInfo) -> bool:
        self._load_if_needed()

        ip = device.ip
        is_new = ip not in self._data

        # Преобразуем DeviceInfo в dict для сохранения
        device_dict = {
            "ip": device.ip,
            "mac": device.mac,
            "hostname": device.hostname,
            "vendor": device.vendor,
            "os_family": device.os_family,
            "os_version": device.os_version,
            "last_seen": device.last_seen.isoformat() if device.last_seen else datetime.now().isoformat(),
            "extra": device.extra or {}
        }

        self._data[ip] = device_dict
        self._save()

        return is_new

    async def get_device(self, ip: str) -> Optional[DeviceInfo]:
        self._load_if_needed()
        data = self._data.get(ip)
        if not data:
            return None
        return self._dict_to_device(data)

    async def get_all_devices(self) -> List[DeviceInfo]:
        self._load_if_needed()
        return [self._dict_to_device(d) for d in self._data.values()]

    def _load_if_needed(self):
        if self._data:
            return
        if self.filename.exists():
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}

    def _save(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[!] Ошибка сохранения JSON: {e}")

    def _dict_to_device(self, data: dict) -> DeviceInfo:
        """Преобразует словарь обратно в DeviceInfo."""
        return DeviceInfo(
            ip=data["ip"],
            mac=data["mac"],
            hostname=data.get("hostname"),
            vendor=data.get("vendor"),
            os_family=data.get("os_family"),
            os_version=data.get("os_version"),
            last_seen=datetime.fromisoformat(data["last_seen"]) if data.get("last_seen") else datetime.now(),
            extra=data.get("extra", {})
        )


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
