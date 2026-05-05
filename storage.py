from interfaces import BaseStorage
import os, json

class DeviceStorage(BaseStorage):
    def __init__(self):
        # Ключ — MAC-адрес, значение — IP
        self._devices = {}

    def add_device(self, ip: str, mac: str) -> bool:
        if mac not in self._devices:
            self._devices[mac] = ip
            return True  # Устройство новое

        # Если IP изменился при том же MAC (DHCP сработал), обновим его
        if self._devices[mac] != ip:
            self._devices[mac] = ip
        return False  # Устройство уже было в базе


class JsonStorage(BaseStorage):
    def __init__(self, filename="devices.json"):
        self.filename = filename
        # Сначала загружаем данные, потом работаем с ними в памяти
        self._devices = self._load_from_file()

    def _load_from_file(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}  # На случай, если файл пустой или поврежден
        return {}

    def _save_to_file(self):
        """Вспомогательный метод для сохранения текущего состояния"""
        with open(self.filename, "w") as f:
            json.dump(self._devices, f, indent=4)  # indent для красоты в файле

    def add_device(self, ip: str, mac: str) -> bool:
        is_new = False

        if mac not in self._devices:
            self._devices[mac] = ip
            is_new = True
        elif self._devices[mac] != ip:
            self._devices[mac] = ip
            # Даже если MAC старый, а IP сменился — это повод обновить файл
            is_new = False
        else:
            # Устройство уже есть и данные те же — ничего не делаем
            return False

        # Если мы дошли сюда, значит данные изменились — сохраняем
        self._save_to_file()
        return is_new
