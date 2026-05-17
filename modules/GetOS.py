from core.interfaces import BaseEnricherModule, DeviceInfo, ScanMode

    # TODO: TCP Fingerprinting (like Nmap), HTTP User-Agent & Banner Grabbing, DHCP Fingerprinting

class OSDetector(BaseEnricherModule):
    """
    Analyzes TTL, ports, and hostnames to identify the Operating System.
    """

    def __init__(self):
        super().__init__()
        # Weight-based OS fingerprints
        self.os_weights = {
            "Windows": {"ttl": {64, 128}, "ports": {445, 135, 139}, "keywords": ["desktop", "win"]},
            "Linux": {"ttl": {64}, "ports": {22, 111}, "keywords": ["linux", "ubuntu", "debian"]},
            "Darwin/iOS": {"ttl": {64}, "ports": {62078}, "keywords": ["iphone", "ipad", "macbook", "apple"]},
            "Android": {"ttl": {64}, "ports": {5555}, "keywords": ["android", "phone"]}
        }

    async def enrich(self, device: DeviceInfo, mode: ScanMode) -> DeviceInfo:
        scores = {os_name: 0 for os_name in self.os_weights}

        # 1. Analyze Open Ports
        for os_name, marks in self.os_weights.items():
            common_ports = device.open_ports.intersection(marks["ports"])
            scores[os_name] += len(common_ports) * 3  # Ports are strong indicators

        # 2. Analyze Hostname
        if device.hostname:
            name_lower = device.hostname.lower()
            for os_name, marks in self.os_weights.items():
                if any(k in name_lower for k in marks["keywords"]):
                    scores[os_name] += 5

        # 3. Determine the winner
        best_os = max(scores, key=scores.get)
        if scores[best_os] > 0:
            device.os_family = best_os
            device.os = f"{best_os} (Estimated)"

        return device