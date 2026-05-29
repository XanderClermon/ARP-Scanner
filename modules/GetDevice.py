from core.interfaces import BaseEnricherModule, DeviceInfo, ScanMode


class DeviceClassifier(BaseEnricherModule):
    """
    Classifies device type (Mobile, Server, Router, etc.) based on active services.
    """

    def __init__(self):
        super().__init__()
        self.types = {
            "Router/Gateway": {"ports": {53, 80, 443}, "keywords": ["gateway", "router", "tplink", "asus"]},
            "Server": {"ports": {22, 443, 3306, 5432, 8080}, "keywords": ["srv", "server", "sql"]},
            "Printer": {"ports": {9100, 631, 515}, "keywords": ["printer", "hp", "canon", "epson"]},
            "Mobile": {"ports": {62078}, "keywords": ["phone", "mobile", "android", "iphone"]},
            "Smart Device": {"ports": {554, 8008, 8009}, "keywords": ["tv", "cast", "smart", "cam"]}
        }

    async def enrich(self, device: DeviceInfo, mode: ScanMode) -> DeviceInfo:
        device_type = "Workstation"
        max_score = 0

        name_lower = (device.hostname or "").lower()

        for d_type, data in self.types.items():
            score = 0
            # По портам
            if hasattr(device, 'open_ports') and device.open_ports:
                if set(device.open_ports).intersection(data["ports"]):
                    score += 4
            # По имени
            if any(k in name_lower for k in data["keywords"]):
                score += 6

            if score > max_score:
                max_score = score
                device_type = d_type

        # Важно: сохраняем ТОЛЬКО в extra
        device.extra["device_type"] = device_type
        # Ни в коем случае не делаем device.device_type = ...

        return device