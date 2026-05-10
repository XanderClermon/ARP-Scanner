"""База сигнатур OS (расширяемая)."""

OS_SIGNATURES = {
    # TTL + Window Size + DF flag patterns
    "windows": {
        "ttl_range": (120, 130),
        "window_sizes": [8192, 65535, 16384, 64240],
        "family": "Windows",
        "versions": ["Windows 10/11", "Windows Server"],
        "confidence_boost": 15
    },
    "linux": {
        "ttl_range": (55, 70),
        "window_sizes": [5840, 5720, 65535, 29200],
        "family": "Linux",
        "versions": ["Linux", "Android"],
        "confidence_boost": 10
    },
    "android": {
        "ttl_range": (55, 70),
        "window_sizes": [5720, 65535, 524288],
        "family": "Android",
        "versions": ["Android"],
        "confidence_boost": 20
    },
    "macos_ios": {
        "ttl_range": (55, 70),
        "window_sizes": [65535, 131072],
        "family": "Apple",
        "versions": ["macOS", "iOS"],
        "confidence_boost": 18
    },
    "network_device": {
        "ttl_range": (240, 256),
        "window_sizes": [4128, 8192, 16384],
        "family": "Network Device",
        "versions": ["Cisco", "MikroTik", "Router"],
        "confidence_boost": 25
    }
}