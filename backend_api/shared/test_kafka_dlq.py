# backend_api/shared/test_kafka_dlq.py
import pytest
import json
import time
import asyncio
from unittest.mock import MagicMock, patch
from backend_api.shared.kafka_client import ResilientKafkaConsumer

class MockMessage:
    def __init__(self, value):
        self.value = value

def test_dlq_routing_on_three_failures():
    """
    Verifies that a message failing processing 3 times is routed to the DLQ
    and the consumer offset is successfully committed.
    """
    # 1. Prepare mocks for KafkaConsumer and KafkaProducer
    mock_consumer_inst = MagicMock()
    mock_producer_inst = MagicMock()

    # The consumer will yield one message, then raise an exception to exit the infinite loop
    test_payload = {"event_id": "test-123", "event_type": "honeypot_trigger"}
    msg = MockMessage(test_payload)

    class ConsumerIterator:
        def __init__(self):
            self.yielded = False
        def __iter__(self):
            return self
        def __next__(self):
            if not self.yielded:
                self.yielded = True
                return msg
            # Raise an exception to exit the outer listen loop
            raise KeyboardInterrupt("Stop consumer loop for testing")

    mock_consumer_inst.__iter__.return_value = ConsumerIterator()

    # Mock the callback processor to always fail, triggering the 3-strike retry logic
    process_mock = MagicMock(side_effect=ValueError("Simulated processing error"))

    # 2. Patch dependencies in kafka_client module
    with patch("backend_api.shared.kafka_client.SAFE_MODE", False), \
         patch("backend_api.shared.kafka_client.KafkaConsumer", return_value=mock_consumer_inst), \
         patch("backend_api.shared.kafka_client.KafkaProducer", return_value=mock_producer_inst), \
         patch("time.sleep", return_value=None): # Bypass sleep delays for fast execution

        # Create ResilientKafkaConsumer
        consumer = ResilientKafkaConsumer(
            topic="phantomnet.test_topic",
            bootstrap_servers="localhost:9092",
            group_id="test-group",
            dlq_topic="phantomnet.test_topic.dlq"
        )

        # Call listen and catch the simulated loop termination exception
        with pytest.raises(KeyboardInterrupt, match="Stop consumer loop for testing"):
            consumer.listen(process_mock)

        # 3. Assertions
        # Verify the processor was called exactly 3 times
        assert process_mock.call_count == 3

        # Verify that the message was sent to the DLQ
        mock_producer_inst.send.assert_called_once()
        sent_topic, sent_value = mock_producer_inst.send.call_args[0]
        assert sent_topic == "phantomnet.test_topic.dlq"
        assert sent_value["original_topic"] == "phantomnet.test_topic"
        assert sent_value["message_value"] == test_payload
        assert "failed_at" in sent_value
        assert sent_value["error"] == "Failed after 3 attempts."

        # Verify commit was called on the consumer to commit the offset after DLQ routing
        mock_consumer_inst.commit.assert_called_once()
