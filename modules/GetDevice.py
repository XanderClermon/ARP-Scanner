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
        device_type = "Workstation"  # Default type
        max_score = 0

        name_lower = (device.hostname or "").lower()

        for d_type, marks in self.types.items():
            score = 0
            # Check ports
            if device.open_ports.intersection(marks["ports"]):
                score += 4
            # Check keywords
            if any(k in name_lower for k in marks["keywords"]):
                score += 6

            if score > max_score:
                max_score = score
                device_type = d_type

        # Store in extra or a new field if we decide to add one to DeviceInfo
        device.extra["device_type"] = device_type
        return device