import asyncio
from scapy.all import IP, TCP, sr1
from typing import Dict, Any
from .base import BaseOSFingerprint
from .database import OS_SIGNATURES


class TCPStackDetector(BaseOSFingerprint):
    """Более точная стратегия на основе TCP SYN/ACK параметров."""

    def __init__(self, tcp_port: int = 80):
        self.tcp_port = tcp_port

    async def fingerprint(self, ip: str) -> Dict[str, Any]:
        return await asyncio.to_thread(self._sync_fingerprint, ip)

    def _sync_fingerprint(self, ip: str) -> Dict[str, Any]:
        resp = sr1(
            IP(dst=ip) / TCP(dport=self.tcp_port, flags="S"),
            timeout=1.5,
            verbose=False,
            retry=1
        )

        if not resp or not resp.haslayer(TCP):
            return {"os_family": "Unknown", "os_version": None, "confidence": 25, "method": "tcp_stack"}

        window = resp[TCP].window
        ttl = resp[IP].ttl if resp.haslayer(IP) else None
        df = bool(resp[IP].flags & 0x02) if resp.haslayer(IP) else False

        best_match = {"os_family": "Unknown", "confidence": 40, "method": "tcp_stack"}

        for sig in OS_SIGNATURES.values():
            if window in sig["window_sizes"] or abs(window - sig["window_sizes"][0]) < 1000:
                confidence = 70 + sig.get("confidence_boost", 0)
                if ttl and not (sig["ttl_range"][0] <= ttl <= sig["ttl_range"][1]):
                    confidence -= 15

                if confidence > best_match["confidence"]:
                    best_match = {
                        "os_family": sig["family"],
                        "os_version": sig["versions"][0],
                        "confidence": min(confidence, 92),
                        "method": "tcp_stack"
                    }

        # Дополнительная эвристика для Android / Apple
        if best_match["os_family"] == "Linux" and window > 50000:
            best_match["os_family"] = "Android"
            best_match["confidence"] += 8

        return best_match