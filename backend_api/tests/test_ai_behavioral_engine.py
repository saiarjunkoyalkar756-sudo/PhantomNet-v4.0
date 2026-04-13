import pytest
from unittest.mock import MagicMock, patch
from backend_api.ai_behavioral_engine.main import consume_and_process_kafka_messages, generate_alert, generate_network_alert
import json

@pytest.fixture(autouse=True)
def mock_blockchain_dependencies():
    with patch('solcx.install_solc'), \
         patch('solcx.compile_source', return_value={
             '<stdin>:AuditTrail': {
                 'abi': [],
                 'bin': '0x123'
             }
         }), \
         patch('web3.Web3') as MockWeb3, \
         patch('backend_api.ai_behavioral_engine.main.Blockchain') as MockBlockchain:
        
        # Mock Web3 instance
        mock_web3_instance = MockWeb3.return_value
        mock_web3_instance.eth.contract.return_value = MagicMock()
        mock_web3_instance.eth.accounts = ["0xabc"]
        mock_web3_instance.eth.wait_for_transaction_receipt.return_value = MagicMock(contractAddress="0xdef")

        # Mock Blockchain instance
        mock_blockchain_instance = MockBlockchain.return_value
        mock_blockchain_instance.add_event.return_value = None  # Mock add_event
        yield mock_blockchain_instance

@pytest.mark.asyncio
@patch('backend_api.ai_behavioral_engine.main.KafkaConsumer')
@patch('backend_api.ai_behavioral_engine.main.KafkaProducer')
async def test_consume_and_process_kafka_messages(MockKafkaProducer, MockKafkaConsumer):
    # Mock the Kafka consumer to yield a single message
    mock_consumer_instance = MockKafkaConsumer.return_value
    mock_consumer_instance.__iter__.return_value = [
        MagicMock(value=json.dumps({
            "type": "packet_metadata",
            "agent_id": "test_agent",
            "tenant_id": "00000000-0000-0000-0000-000000000001",
            "data": {
                "source_ip": "1.2.3.4",
                "destination_port": 80
            }
        }).encode('utf-8'))
    ]

    # Mock the Kafka producer
    mock_producer_instance = MockKafkaProducer.return_value

    # Run the consumer and process loop
    await consume_and_process_kafka_messages()

    # Assert that the producer was called with an alert
    # This is a simple test, a more robust test would check the content of the alert
    assert mock_producer_instance.send.called

def test_generate_alert():
    alert = generate_alert("00000000-0000-0000-0000-000000000001", "test_agent", 101, 60)
    assert alert["rule_name"] == "High Frequency Event Anomaly"
    assert alert["agent_id"] == "test_agent"

def test_generate_network_alert():
    anomaly = {"type": "Port Scan", "description": "Port scan detected"}
    alert = generate_network_alert("00000000-0000-0000-0000-000000000001", "test_agent", anomaly)
    assert alert["rule_name"] == "Network Anomaly - Port Scan"
    assert alert["agent_id"] == "test_agent"
