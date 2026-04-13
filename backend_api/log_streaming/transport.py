import asyncio
from .websocket_broadcaster import broadcaster
from .formatter import serialize_log_record
from loguru import logger

class WebSocketTransport:
    """
    A transport class that sends log records to the WebSocket broadcaster.
    """
    def __init__(self, broadcaster_instance):
        self.broadcaster = broadcaster_instance

    async def send(self, record_dict): # Now accepts the record dictionary
        """
        Formats and sends a log record (as a dictionary) to the broadcaster.
        """
        try:
            log_json_string = serialize_log_record(record_dict)
            await self.broadcaster.broadcast(log_json_string)
        except Exception as e:
            # We use the native logger here to avoid a recursive loop if the transport fails
            logger.warning(f"Failed to transport log to WebSocket: {e}")

# Create a single instance of the transport
ws_transport = WebSocketTransport(broadcaster)

# Create a sink function for Loguru that uses the transport
async def loguru_ws_sink(message):
    """
    An async sink function that can be passed to Loguru's configure method.
    """
    # The message passed by Loguru is the formatted string, not the record.
    # To get the record, we need to use a class-based sink or a lambda
    # that captures the record. For simplicity here, we'll assume the main
    # logger config will handle getting the record to the transport.
    # This is a placeholder; the real sink will be a lambda in logger_config.
    pass

