# backend_api/honeypot_service/models.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import datetime

class HoneypotCreate(BaseModel):
    honeypot_id: str
    type: str
    port: int
    host: str = "127.0.0.1"
    capture_level: str = "low"
    tags: List[str] = []

    class Config:
        schema_extra = {
            "example": {
                "honeypot_id": "ssh-honeypot-1",
                "type": "ssh",
                "port": 2222,
                "host": "127.0.0.1",
                "capture_level": "low",
                "tags": ["production", "ssh"]
            }
        }

class HoneypotConfig(HoneypotCreate):
    status: str = "stopped"
    pid: Optional[int] = None

    class Config:
        schema_extra = {
            "example": {
                "honeypot_id": "ssh-honeypot-1",
                "type": "ssh",
                "port": 2222,
                "host": "127.0.0.1",
                "capture_level": "low",
                "tags": ["production", "ssh"],
                "status": "running",
                "pid": 12345
            }
        }

class HoneypotAlert(BaseModel):
    alert_id: str
    timestamp: str
    honeypot_id: str
    alert_type: str
    severity: str
    description: str
    source_ip: str
    event_data: Dict[str, Any]
    enriched_data: Dict[str, Any]

    class Config:
        schema_extra = {
            "example": {
                "alert_id": "alert-12345",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "honeypot_id": "ssh-honeypot-1",
                "alert_type": "ssh_bruteforce_attempt",
                "severity": "high",
                "description": "Multiple failed SSH login attempts detected.",
                "source_ip": "192.168.1.100",
                "event_data": {
                    "event_id": "uuid-123",
                    "payload": "username=root, password=password"
                },
                "enriched_data": {
                    "reverse_dns": "attacker.example.com",
                    "geolocation": {"country": "US"}
                }
            }
        }
