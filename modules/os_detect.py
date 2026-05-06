from core.interfaces import BaseEnricherModule
from scapy.all import IP, ICMP, TCP, sr1
from typing import Dict, Any


class BasicOSDetector(BaseEnricherModule):
    def __init__(self, tcp_port: int = 80):
        self.tcp_port = tcp_port

    def enrich(self, ip: str) -> Dict[str, Any]:
        """Собирает TTL и TCP-параметры для определения ОС"""
        result = {"os": "Unknown"}
        data = {}

        # ICMP запрос
        resp = sr1(IP(dst=ip) / ICMP(), timeout=1, verbose=False)
        if resp and resp.haslayer(IP):
            data["ttl"] = resp[IP].ttl

        # TCP SYN запрос
        resp = sr1(
            IP(dst=ip) / TCP(dport=self.tcp_port, flags="S"),
            timeout=1,
            verbose=False
        )
        if resp and resp.haslayer(TCP):
            data["window"] = resp[TCP].window
            data["options"] = [o[0] for o in resp[TCP].options]
            if "ttl" not in data:
                data["ttl"] = resp[IP].ttl

        # Логика вердикта (перенесена из анализатора для компактности)
        ttl = data.get("ttl")
        if ttl:
            if ttl in (128, 127, 129):
                result["os"] = "Windows"
            elif ttl in (64, 63, 65):
                result["os"] = "Linux/Android/macOS"
            elif ttl in (255, 254):
                result["os"] = "Network Device"
            else:
                result["os"] = f"Unknown (TTL={ttl})"

        return result