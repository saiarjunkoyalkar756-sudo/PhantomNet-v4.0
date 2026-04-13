# This module requires the 'scapy' library.
# Install it using: pip install scapy

import time
from threading import Thread
import math
import asyncio
from typing import List, Optional

from phantomnet_core.os_adapter import get_os, OS_LINUX, OS_WINDOWS, OS_TERMUX

# Conditional import for scapy
try:
    from scapy.all import sniff, IP, TCP, UDP, DNS
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("Scapy not available. Network sensor will operate in limited mode.")

# Placeholder for a real-time communication channel to the backend
def send_telemetry(data):
    print(f"Sending telemetry: {data}")

class NetworkSensor(Thread):
    def __init__(
        self,
        interface: Optional[str] = None,
        event_queue: asyncio.Queue = None,
        polling_interval: int = 5,
        graph_interval: int = 30,
    ):
        super().__init__()
        self.interface = interface
        self.daemon = True
        self.running = False
        self.connection_graph = {}
        self.dns_requests = {}
        self.event_queue = event_queue
        self.current_os = get_os()
        self.scapy_available = SCAPY_AVAILABLE
        self.polling_interval = polling_interval
        self.graph_interval = graph_interval

    def set_polling_interval(self, interval: int):
        """
        Allows the Health Monitor to dynamically adjust the polling interval.
        """
        self.logger.info(f"Updating network sensor polling interval to {interval} seconds.")
        self.polling_interval = interval
        self.graph_interval = max(interval, 30) # Ensure graph is not sent too frequently

    def run(self):
        self.running = True
        print(f"Starting network sensor on interface {self.interface or 'default'} for OS: {self.current_os}")
        
        # Start a background thread to send the network graph periodically
        graph_thread = Thread(target=self._send_network_graph_periodically)
        graph_thread.daemon = True
        graph_thread.start()

        if self.current_os == OS_LINUX and SCAPY_AVAILABLE:
            print("Linux: Starting Scapy sniff with full capabilities.")
            sniff(iface=self.interface, prn=self.process_packet, store=False, stop_filter=lambda p: not self.running)
        elif self.current_os == OS_WINDOWS and SCAPY_AVAILABLE:
            print("Windows: Starting Scapy sniff (requires Npcap/WinPcap).")
            sniff(iface=self.interface, prn=self.process_packet, store=False, stop_filter=lambda p: not self.running)
        elif self.current_os == OS_TERMUX:
            print("Termux: Operating in limited network monitoring mode.")
            self._limited_monitor_mode() # Placeholder for Termux specific monitoring
        else:
            print(f"OS {self.current_os} or Scapy not supported for active sniffing. Running in passive/limited mode.")
            self._limited_monitor_mode() # Fallback

    def _limited_monitor_mode(self):
        """
        Placeholder for limited network monitoring on platforms like Termux.
        """
        while self.running:
            if self.event_queue:
                self.event_queue.put_nowait({
                    "type": "network_activity_limited",
                    "data": {
                        "timestamp": time.time(),
                        "message": "Simulated network activity in limited mode."
                    }
                })
            time.sleep(self.polling_interval)


    def _send_network_graph_periodically(self):
        while self.running:
            time.sleep(self.graph_interval)
            self._send_network_graph()

    def _send_network_graph(self):
        if not self.event_queue:
            return

        connections = []
        for src, dsts in self.connection_graph.items():
            for dst in dsts:
                connections.append({"source_ip": src, "destination_ip": dst, "destination_port": 0, "protocol": ""})
        
        network_graph_data = {
            "timestamp": time.time(),
            "connections": connections,
        }
        self.event_queue.put_nowait({"type": "network_graph", "data": network_graph_data})


    def stop(self):
        self.running = False
        print("Stopping network sensor")

    def is_alive(self) -> bool:
        """
        Checks if the sensor thread is currently running.
        Required by the AgentHealthMonitor.
        """
        return self.running and super().is_alive()

    def process_packet(self, packet):
        if not self.scapy_available:
            return
        if not self.event_queue:
            return

        if IP in packet:
            # Packet Metadata
            metadata = {
                "timestamp": time.time(),
                "source_ip": packet[IP].src,
                "destination_ip": packet[IP].dst,
                "size": len(packet),
                "protocol": packet[IP].proto,
            }
            self.event_queue.put_nowait({"type": "packet_metadata", "data": metadata})

            # Deep Packet Inspection (DPI) for protocol inference
            if packet.haslayer(TCP):
                metadata["source_port"] = packet[TCP].sport
                metadata["destination_port"] = packet[TCP].dport
                # Simple DPI based on port
                if packet[TCP].dport == 80 or packet[TCP].sport == 80:
                    metadata["inferred_protocol"] = "HTTP"
                elif packet[TCP].dport == 443 or packet[TCP].sport == 443:
                    metadata["inferred_protocol"] = "HTTPS"
            elif packet.haslayer(UDP):
                metadata["source_port"] = packet[UDP].sport
                metadata["destination_port"] = packet[UDP].dport
                if packet.haslayer(DNS):
                    self.process_dns_packet(packet)

            # Network Connection Graph
            self.update_connection_graph(packet[IP].src, packet[IP].dst)
            
    def process_dns_packet(self, packet):
        if DNS in packet and packet[DNS].qr == 0: # It's a query
            domain = packet[DNS].qd.qname.decode('utf-8')
            entropy = self.calculate_domain_entropy(domain)
            
            dns_query_data = {
                "timestamp": time.time(),
                "client_ip": packet[IP].src,
                "domain_name": domain,
                "record_type": packet[DNS].qd.qtype,
                "entropy": entropy
            }
            
            # DNS Anomaly Detection
            if entropy > 4.0: # High entropy, potentially DGA
                dns_query_data["is_suspicious"] = True
                dns_query_data["suspicion_reason"] = "High entropy"

            self.event_queue.put_nowait({"type": "dns_query", "data": dns_query_data})


    def calculate_domain_entropy(self, domain: str) -> float:
        p, lns = {}, len(domain)
        for c in domain:
            p[c] = p.get(c, 0) + 1
        
        return -sum(count/lns * math.log2(count/lns) for count in p.values())

    def update_connection_graph(self, src, dst):
        if src not in self.connection_graph:
            self.connection_graph[src] = set()
        self.connection_graph[src].add(dst)

# Example Usage:
# sensor = NetworkSensor()
# sensor.start()
# time.sleep(60)
# sensor.stop()