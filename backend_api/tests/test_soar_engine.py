import pytest
from unittest.mock import patch, MagicMock
from backend_api.soar_engine.main import soar_engine_thread
from backend_api.soar_engine.playbooks import trigger_playbook
import json

@patch('backend_api.soar_engine.main.KafkaConsumer')
@patch('backend_api.soar_engine.countermeasures.KafkaProducer')
def test_soar_engine_thread(MockKafkaProducer, MockKafkaConsumer):
    # Mock the Kafka consumer to yield a single message
    mock_consumer_instance = MockKafkaConsumer.return_value
    mock_consumer_instance.__iter__.return_value = [
        MagicMock(value=json.dumps({
            "rule_name": "Network Anomaly - Port Scan",
            "details": {
                "source_ip": "1.2.3.4"
            },
            "tenant_id": "test_tenant",
            "agent_id": "test_agent"
        }).encode('utf-8'))
    ]

    # Run the SOAR engine thread
    # This is a simplified test, a more robust test would check the triggered playbook
    with patch('backend_api.soar_engine.main.trigger_playbook') as mock_trigger_playbook:
        soar_engine_thread()
        assert mock_trigger_playbook.called

@patch('backend_api.soar_engine.playbooks.block_ip')
def test_trigger_playbook(mock_block_ip):
    alert = {
        "rule_name": "Network Anomaly - Port Scan",
        "details": {
            "source_ip": "1.2.3.4"
        }
    }
    trigger_playbook(alert)
    mock_block_ip.assert_called_with("1.2.3.4")
