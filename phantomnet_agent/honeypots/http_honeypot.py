"""
HTTP Honeypot — PhantomNet Agent
MITRE ATT&CK: T1190 (Exploit Public-Facing Application), T1078 (Valid Accounts)

Mimics an nginx-served admin login panel. Captures and forwards to the event bus:
  - Every inbound HTTP request (method, path, headers, body)
  - POST bodies on login pages (credential harvesting detection)
  - Automated scanner fingerprints (User-Agent, path traversal, common wordlists)

Designed as the highest-yield honeylure for automated internet scanners.
"""

import asyncio
import datetime
import hashlib
import json
import logging
from uuid import uuid4
from typing import Callable, Dict, Any

from .base import Honeypot

logger = logging.getLogger("phantomnet_agent.honeypots.http")

# Fake login page HTML — looks like an nginx-proxied admin panel
_LOGIN_PAGE = b"""\
HTTP/1.1 200 OK\r
Server: nginx/1.18.0 (Ubuntu)\r
Content-Type: text/html; charset=utf-8\r
Connection: close\r
\r
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Admin Login</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f0f2f5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    .box { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.15); width: 320px; }
    h2 { text-align: center; color: #333; margin-bottom: 24px; }
    input { width: 100%; padding: 10px; margin: 8px 0 16px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
    button { width: 100%; padding: 10px; background: #1890ff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
    button:hover { background: #096dd9; }
    .error { color: red; text-align: center; font-size: 13px; margin-top: 8px; }
  </style>
</head>
<body>
  <div class="box">
    <h2>&#128274; Admin Portal</h2>
    <form method="POST" action="/login">
      <label>Username</label>
      <input type="text" name="username" placeholder="Enter username" autocomplete="off">
      <label>Password</label>
      <input type="password" name="password" placeholder="Enter password">
      <button type="submit">Sign In</button>
    </form>
    <p class="error">Invalid credentials.</p>
  </div>
</body>
</html>
"""

_401_RESPONSE = b"""\
HTTP/1.1 401 Unauthorized\r
Server: nginx/1.18.0 (Ubuntu)\r
Content-Type: application/json\r
Connection: close\r
\r
{"error": "Invalid credentials", "code": 401}
"""

_404_RESPONSE = b"""\
HTTP/1.1 404 Not Found\r
Server: nginx/1.18.0 (Ubuntu)\r
Content-Type: text/html\r
Connection: close\r
\r
<html><body><h1>404 Not Found</h1><p>nginx/1.18.0 (Ubuntu)</p></body></html>
"""


class HttpHoneypot(Honeypot):
    """
    HTTP honeypot that mimics an nginx admin panel.

    High-yield lure because:
    - Automated scanners (shodan, masscan, nuclei) hit HTTP first
    - Wordlist attacks against /admin, /login, /wp-login.php are universal
    - POST body capture reveals attacker credential lists
    """

    # Common paths targeted by scanners — all served with the login page
    _LURE_PATHS = {
        "/", "/login", "/admin", "/admin/login", "/wp-login.php",
        "/phpmyadmin", "/manager/html", "/console", "/dashboard",
        "/api/v1/auth", "/.env", "/config.php", "/backup",
    }

    def __init__(self, honeypot_id: str, port: int,
                 event_forwarder: Callable[[Dict[str, Any]], None],
                 shutdown_event: asyncio.Event):
        super().__init__(port, event_forwarder, shutdown_event)
        self.honeypot_id = honeypot_id

    async def run(self):
        server = await asyncio.start_server(
            self._handle_connection, "0.0.0.0", self.port
        )
        logger.info(f"[+] HTTP Honeypot active on port {self.port}")
        async with server:
            # Stop when the global shutdown event fires
            shutdown_task = asyncio.create_task(self.shutdown_event.wait())
            serve_task = asyncio.create_task(server.serve_forever())
            done, pending = await asyncio.wait(
                [shutdown_task, serve_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            for t in pending:
                t.cancel()
        logger.info("[*] HTTP Honeypot stopped.")

    async def _handle_connection(self, reader: asyncio.StreamReader,
                                  writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername") or ("unknown", 0)
        src_ip, src_port = peer[0], peer[1]
        session_id = str(uuid4())
        ts = datetime.datetime.utcnow().isoformat()

        try:
            # Read the HTTP request (max 8 KB to prevent DoS)
            raw = await asyncio.wait_for(reader.read(8192), timeout=5.0)
        except (asyncio.TimeoutError, ConnectionResetError):
            writer.close()
            return

        try:
            request_line, *header_lines = raw.decode("utf-8", errors="replace").split("\r\n")
        except Exception:
            writer.close()
            return

        # Parse method + path
        parts = request_line.split(" ")
        method = parts[0] if len(parts) > 0 else "UNKNOWN"
        path   = parts[1] if len(parts) > 1 else "/"

        # Parse headers
        headers: Dict[str, str] = {}
        body = ""
        in_body = False
        for line in header_lines:
            if line == "":
                in_body = True
                continue
            if in_body:
                body += line
            elif ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        user_agent = headers.get("user-agent", "")
        content_type = headers.get("content-type", "")

        # Detect scanner signatures
        scanner_hints = []
        for sig in ("masscan", "zgrab", "nuclei", "nmap", "sqlmap", "curl/", "python-requests", "go-http-client"):
            if sig.lower() in user_agent.lower():
                scanner_hints.append(sig)

        payload_summary = f"method={method} path={path} ua={user_agent}"
        if body:
            payload_summary += f" body={body[:256]}"

        event: Dict[str, Any] = {
            "honeypot_id": self.honeypot_id,
            "session_id": session_id,
            "src_ip": src_ip,
            "src_port": src_port,
            "dst_port": self.port,
            "protocol": "http",
            "event_type": "http_request",
            "method": method,
            "path": path,
            "user_agent": user_agent,
            "content_type": content_type,
            "body_preview": body[:512],
            "scanner_signatures": scanner_hints,
            "timestamp": ts,
            "payload_hash": hashlib.sha256(payload_summary.encode()).hexdigest(),
        }

        # Credential capture on POST to login endpoints
        if method == "POST" and any(p in path for p in ("/login", "/auth", "/wp-login.php")):
            event["event_type"] = "credential_attempt"
            event["credential_payload"] = body[:512]
            logger.warning(
                f"[!] HTTP honeypot credential attempt from {src_ip} | path={path} | body={body[:128]}"
            )
        else:
            logger.info(f"[*] HTTP request from {src_ip}: {method} {path}")

        # Forward event to the agent bus (fire-and-forget)
        try:
            await self.event_forwarder(event)
        except Exception as e:
            logger.error(f"HTTP honeypot event forward failed: {e}")

        # Send response
        try:
            if path in self._LURE_PATHS or path.startswith("/admin"):
                writer.write(_LOGIN_PAGE)
            elif method == "POST" and "login" in path:
                writer.write(_401_RESPONSE)
            else:
                writer.write(_404_RESPONSE)
            await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()
