import asyncio
from scapy.all import IP, ICMP, sr1
from typing import Dict, Any
from .base import BaseOSFingerprint
from .database import OS_SIGNATURES


class TTLBasedDetector(BaseOSFingerprint):
    """Простая, но очень эффективная TTL-based стратегия."""

    async def fingerprint(self, ip: str) -> Dict[str, Any]:
        return await asyncio.to_thread(self._sync_fingerprint, ip)

    def _sync_fingerprint(self, ip: str) -> Dict[str, Any]:
        ttl = self._get_ttl(ip)
        if not ttl:
            return {"os_family": "Unknown", "os_version": None, "confidence": 20, "method": "ttl"}

        for sig_name, sig in OS_SIGNATURES.items():
            min_ttl, max_ttl = sig["ttl_range"]
            if min_ttl <= ttl <= max_ttl:
                return {
                    "os_family": sig["family"],
                    "os_version": sig["versions"][0],
                    "confidence": 65 + sig.get("confidence_boost", 0),
                    "method": "ttl"
                }

        return {
            "os_family": f"Unknown (TTL={ttl})",
            "os_version": None,
            "confidence": 30,
            "method": "ttl"
        }

    def _get_ttl(self, ip: str) -> int | None:
        """Получаем TTL через ICMP, fallback на TCP SYN."""
        # ICMP
        resp = sr1(IP(dst=ip) / ICMP(), timeout=1.2, verbose=False, retry=1)
        if resp and resp.haslayer(IP):
            return resp[IP].ttl

        # Fallback TCP SYN (port 80 или 443)
        for port in (80, 443):
            resp = sr1(
                IP(dst=ip) / TCP(dport=port, flags="S"),
                timeout=1.1,
                verbose=False
            )
            if resp and resp.haslayer(IP):
                return resp[IP].ttl
        return None