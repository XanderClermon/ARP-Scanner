from scapy.all import IP, ICMP, TCP, sr1
from interfaces import *

class BasicOSDetector(BaseOSDetector):
    def __init__(self, tcp_port=80):
        self.tcp_port = tcp_port

    def detect(self, ip: str) -> dict:
        result = {}

        # ICMP для TTL
        resp = sr1(IP(dst=ip) / ICMP(), timeout=1.5, verbose=False)
        if resp and resp.haslayer(IP):
            result["ttl"] = resp[IP].ttl

        # TCP SYN для Window + Options
        resp = sr1(IP(dst=ip) / TCP(dport=self.tcp_port, flags="S"),
                   timeout=1.5, verbose=False)

        if resp and resp.haslayer(TCP):
            tcp = resp[TCP]
            result["window"] = tcp.window
            result["options"] = [o[0] for o in tcp.options]

        return result