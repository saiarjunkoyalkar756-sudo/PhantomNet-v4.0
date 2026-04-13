from typing import Callable, Dict, Any
import threading

class Honeypot:
    def __init__(
        self, port: int, event_forwarder: Callable[[Dict[str, Any]], None], shutdown_event: threading.Event
    ):
        self.port = port
        self.event_forwarder = event_forwarder
        self.shutdown_event = shutdown_event

    def run(self):
        raise NotImplementedError
