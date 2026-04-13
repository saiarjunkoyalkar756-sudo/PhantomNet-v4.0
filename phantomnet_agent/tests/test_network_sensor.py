import pytest
from unittest.mock import MagicMock, patch
from phantomnet_agent.networking.network_sensor import NetworkSensor
from scapy.all import IP, TCP, UDP, DNS, DNSQR

@pytest.fixture(autouse=True)
def mock_scapy_sniff():
    with patch('scapy.all.sniff') as mock_sniff:
        yield mock_sniff

@pytest.fixture
def network_sensor():
    return NetworkSensor(event_queue=MagicMock())

def test_process_packet_ip(network_sensor):
    packet = IP(src="1.2.3.4", dst="5.6.7.8")
    network_sensor.process_packet(packet)
    network_sensor.event_queue.put_nowait.assert_called_with({
        "type": "packet_metadata",
        "data": {
            "timestamp": pytest.approx(network_sensor.event_queue.put_nowait.call_args[0][0]['data']['timestamp']),
            "source_ip": "1.2.3.4",
            "destination_ip": "5.6.7.8",
            "size": 20,
            "protocol": 0,
        }
    })

def test_process_packet_tcp(network_sensor):
    packet = IP(src="1.2.3.4", dst="5.6.7.8") / TCP(sport=12345, dport=80)
    network_sensor.process_packet(packet)
    network_sensor.event_queue.put_nowait.assert_called()

def test_process_packet_udp(network_sensor):
    packet = IP(src="1.2.3.4", dst="5.6.7.8") / UDP(sport=12345, dport=53)
    network_sensor.process_packet(packet)
    network_sensor.event_queue.put_nowait.assert_called()

def test_process_dns_packet(network_sensor):
    packet = IP(src="1.2.3.4", dst="8.8.8.8") / UDP(dport=53) / DNS(rd=1, qd=DNSQR(qname="google.com"))
    network_sensor.process_dns_packet(packet)
    network_sensor.event_queue.put_nowait.assert_called_with({
        "type": "dns_query",
        "data": {
            "timestamp": pytest.approx(network_sensor.event_queue.put_nowait.call_args[0][0]['data']['timestamp']),
            "client_ip": "1.2.3.4",
            "domain_name": "google.com.",
            "record_type": 1,
            "entropy": pytest.approx(2.5216406363433186)
        }
    })
    
    packet_suspicious = IP(src="1.2.3.4", dst="8.8.8.8") / UDP(dport=53) / DNS(rd=1, qd=DNSQR(qname="asdfghjklqwertyuiopzxcvbnm.com"))
    network_sensor.process_dns_packet(packet_suspicious)
    network_sensor.event_queue.put_nowait.assert_called_with({
        "type": "dns_query",
        "data": {
            "timestamp": pytest.approx(network_sensor.event_queue.put_nowait.call_args[0][0]['data']['timestamp']),
            "client_ip": "1.2.3.4",
            "domain_name": "asdfghjklqwertyuiopzxcvbnm.com.",
            "record_type": 1,
            "entropy": pytest.approx(4.700439718141092),
            "is_suspicious": True,
            "suspicion_reason": "High entropy"
        }
    })
