import asyncio, datetime, json, hashlib
from uuid import uuid4
import socket
import paramiko
import threading # Keep threading for the Transport, but the server itself will be asyncio
import random  # Import random
from .base import Honeypot
from backend_api.honeypot_service.metrics import honeypot_sessions_total, honeypot_events_total, honeypot_errors_total

class SSHHoneypot(Honeypot):
    # Define a list of possible SSH banners
    SSH_BANNERS = [
        "SSH-2.0-OpenSSH_7.6p1 Ubuntu-4ubuntu0.3",
        "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.2",
        "SSH-2.0-OpenSSH_6.7p1 Debian-5+deb8u3",
        "SSH-2.0-OpenSSH_5.3",
        "SSH-2.0-OpenSSH_7.9p1 Debian-10",
        "SSH-2.0-dropbear_2018.76",
        "SSH-2.0-libssh-0.9.3",
    ]

    def __init__(self, honeypot_id, port, event_forwarder, shutdown_event):
        super().__init__(port, event_forwarder, shutdown_event)
        self.honeypot_id = honeypot_id

    async def run(self):
        class SSHServer(paramiko.ServerInterface):
            def __init__(self, addr, port, honeypot_id, event_forwarder, banner):
                self.addr = addr
                self.port = port
                self.honeypot_id = honeypot_id
                self.event_forwarder = event_forwarder
                self.banner = banner  # Store the selected banner

            async def check_auth_password(self, username, password):
                session_id = str(uuid4())
                ts = datetime.datetime.utcnow().isoformat()
                payload = f"username={username}, password={password}"
                event = {
                    "honeypot_id": self.honeypot_id,
                    "session_id": session_id,
                    "src_ip": self.addr[0],
                    "src_port": self.addr[1],
                    "dst_port": self.port,
                    "protocol": "ssh",
                    "event_type": "auth_attempt",
                    "payload": payload,
                    "timestamp": ts,
                    "payload_hash": hashlib.sha256(payload.encode()).hexdigest(),
                }
                await self.event_forwarder(event)
                honeypot_events_total.labels(
                    honeypot_id=self.honeypot_id,
                    honeypot_type="ssh",
                    event_type="auth_attempt"
                ).inc()
                print(f"[!] SSH login attempt: user={username}, password={password} from {self.addr[0]}:{self.addr[1]}")
                return paramiko.AUTH_FAILED

            async def check_channel_request(self, kind, chanid):
                session_id = str(uuid4())
                ts = datetime.datetime.utcnow().isoformat()
                payload = f"kind={kind}, chanid={chanid}"
                event = {
                    "honeypot_id": self.honeypot_id,
                    "session_id": session_id,
                    "src_ip": self.addr[0],
                    "src_port": self.addr[1],
                    "dst_port": self.port,
                    "protocol": "ssh",
                    "event_type": "channel_request",
                    "payload": payload,
                    "timestamp": ts,
                    "payload_hash": hashlib.sha256(payload.encode()).hexdigest(),
                }
                await self.event_forwarder(event)
                honeypot_events_total.labels(
                    honeypot_id=self.honeypot_id,
                    honeypot_type="ssh",
                    event_type="channel_request"
                ).inc()
                print(f"[!] SSH channel request: kind={kind}, chanid={chanid} from {self.addr[0]}:{self.addr[1]}")
                return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

        async def _handle_client(reader, writer):
            peername = writer.get_extra_info('peername')
            sockname = writer.get_extra_info('sockname')
            addr = peername
            
            honeypot_sessions_total.labels(honeypot_id=self.honeypot_id, honeypot_type="ssh").inc()

            sock = writer.get_extra_info('socket')
            transport = paramiko.Transport(sock)
            transport.add_server_key(paramiko.RSAKey.generate(2048))
            selected_banner = random.choice(self.SSH_BANNERS)
            transport.set_banner(selected_banner)
            
            server = SSHServer(
                addr,
                self.port,
                self.honeypot_id,
                self.event_forwarder,
                selected_banner,
            )
            
            try:
                transport.start_server(server=server)
                while transport.is_active():
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"[-] Error handling SSH connection: {e}")
                honeypot_errors_total.labels(
                    honeypot_id=self.honeypot_id,
                    honeypot_type="ssh",
                    error_type=e.__class__.__name__
                ).inc()
            finally:
                transport.close()
                writer.close()
        
        server = await asyncio.start_server(_handle_client, "0.0.0.0", self.port)
        print(f"[+] SSH Honeypot active on port {self.port}")
        async with server:
            await server.serve_forever()
