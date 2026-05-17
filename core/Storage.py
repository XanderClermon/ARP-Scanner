import redis.asyncio as redis
import time
from config import settings

import json
import asyncio
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from dataclasses import asdict

from core.interfaces import BaseStorage
from core.interfaces import DeviceInfo

class JsonStorage(BaseStorage):
    """
    High-efficiency JSON storage.
    Handles Set and Datetime serialization automatically.
    """

    def __init__(self, filename: str = "devices.json"):
        self.filename = Path(filename)
        self._data: Dict[str, dict] = self._load()

    def _load(self) -> Dict[str, dict]:
        """Synchronous load on initialization."""
        if self.filename.exists():
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _serialize(self, obj):
        """Custom serializer for types JSON doesn't handle by default."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, set):
            return list(obj)
        return obj

    async def add_or_update(self, device: DeviceInfo) -> bool:
        ip = device.ip
        is_new = ip not in self._data

        # Convert dataclass to dict and update internal cache
        self._data[ip] = asdict(device)

        # Async save to avoid blocking the daemon loop
        asyncio.create_task(self._save())
        return is_new

    async def get_device(self, ip: str) -> Optional[DeviceInfo]:
        data = self._data.get(ip)
        return self._dict_to_device(data) if data else None

    async def get_all_devices(self) -> List[DeviceInfo]:
        return [self._dict_to_device(d) for d in self._data.values()]

    async def _save(self):
        """Writes current state to disk."""
        try:
            content = json.dumps(self._data, default=self._serialize, ensure_ascii=False, indent=2)
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"JSON Save Error: {e}")

    def _dict_to_device(self, data: dict) -> DeviceInfo:
        """Restores DeviceInfo from dictionary."""
        # Convert ISO string back to datetime
        if isinstance(data.get("last_seen"), str):
            data["last_seen"] = datetime.fromisoformat(data["last_seen"])

        # Convert port list back to set
        if "open_ports" in data:
            data["open_ports"] = set(data["open_ports"])

        return DeviceInfo(**data)


class RedisStorage(BaseStorage):
    """
    Async Redis storage optimized for the Control Panel.
    Stores devices as clean JSON objects within a single HSET.
    """

    def __init__(self):
        # Используем асинхронный клиент
        self.r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.key = "detected_devices"

    async def add_or_update(self, device: DeviceInfo) -> bool:
        """
        Serializes DeviceInfo to JSON and saves it to Redis Hash.
        Returns True if the device is newly discovered.
        """
        ip = device.ip

        # 1. Проверяем, было ли устройство в базе (для логики NEW/UP)
        is_new = not await self.r.hexists(self.key, ip)

        # 2. Конвертируем в словарь и чистим от пустых полей (как в JsonStorage)
        raw_dict = asdict(device)
        clean_dict = {
            k: v for k, v in raw_dict.items()
            if v is not None and v != "" and v != [] and v != {}
        }

        # 3. Сериализуем в JSON (default=list корректно обработает set портов)
        json_data = json.dumps(clean_dict, default=list, ensure_ascii=False)

        # 4. Пишем в Redis (поле: IP, значение: JSON)
        await self.r.hset(self.key, ip, json_data)

        return is_new

    async def get_device(self, ip: str) -> Optional[DeviceInfo]:
        """Retrieves a single device from Redis."""
        data = await self.r.hget(self.key, ip)
        if not data:
            return None
        return self._dict_to_device(json.loads(data))

    async def get_all_devices(self) -> List[DeviceInfo]:
        """Fetches all devices for the Control Panel view."""
        all_data = await self.r.hgetall(self.key)
        devices = []
        for json_str in all_data.values():
            devices.append(self._dict_to_device(json.loads(json_str)))
        return devices

    def _dict_to_device(self, data: dict) -> DeviceInfo:
        """Helper to restore DeviceInfo object from JSON dict."""
        if "open_ports" in data:
            data["open_ports"] = set(data["open_ports"])
        return DeviceInfo(**data)