from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class OSAnalysisResult:
    os_name: str
    details: Dict[str, Any]


class OSAnalyzer:
    def analyze(self, ip: str, detector) -> OSAnalysisResult:
        data = detector.detect(ip)
        ttl = data.get("ttl")
        win = data.get("window")
        opts = data.get("options", [])

        if not ttl:
            return OSAnalysisResult("Unknown", data)

        if ttl in (128, 127, 129):
            return OSAnalysisResult("Windows", data)

        if ttl in (64, 63, 65):
            if "SAckOK" in opts:
                return OSAnalysisResult("Linux/Android", data)
            return OSAnalysisResult("Linux/Android/macOS", data)

        if ttl in (255, 254):
            return OSAnalysisResult("Network Device", data)

        return OSAnalysisResult(f"Unknown (TTL={ttl})", data)