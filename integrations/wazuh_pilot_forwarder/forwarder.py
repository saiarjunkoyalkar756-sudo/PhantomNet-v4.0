"""Telemetry-only Wazuh-to-PhantomNet pilot forwarder.

This module deliberately contains no Wazuh API client, containment route, subprocess call,
or endpoint action. It forwards selected Wazuh alert JSON only to the tenant-bound
PhantomNet Wazuh forwarder stream endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import argparse
import fcntl
import json
import logging
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


LOGGER = logging.getLogger("phantomnet.wazuh_pilot_forwarder")
MAX_ALERT_BYTES = 1_048_576
MAX_TOKEN_BYTES = 4_096


class ConfigurationError(ValueError):
    """Raised when a pilot configuration violates a safety boundary."""


class DeliveryError(RuntimeError):
    """Raised when PhantomNet cannot accept a telemetry batch."""


@dataclass(frozen=True)
class PilotConfig:
    """Configuration for a telemetry-only forwarder instance."""

    endpoint_url: str
    token_path: Path
    state_path: Path
    spool_directory: Path
    min_rule_level: int = 7
    allowed_groups: tuple[str, ...] = ("syscheck", "syscollector", "sca", "rootcheck")
    batch_size: int = 25
    poll_interval_seconds: float = 1.0
    allow_insecure_http: bool = False

    def validate(self) -> None:
        parsed = urlparse(self.endpoint_url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise ConfigurationError("PHANTOMNET_WAZUH_STREAM_URL must be an absolute HTTP(S) URL.")
        if parsed.scheme != "https" and not self.allow_insecure_http:
            raise ConfigurationError("Telemetry delivery requires HTTPS unless PHANTOMNET_ALLOW_INSECURE_HTTP=true is set for a lab only.")
        if not parsed.path.endswith("/stream") or "/wazuh/forwarders/" not in parsed.path:
            raise ConfigurationError("PHANTOMNET_WAZUH_STREAM_URL must target the registered read-only Wazuh forwarder stream endpoint.")
        if self.min_rule_level < 0 or self.min_rule_level > 16:
            raise ConfigurationError("PHANTOMNET_WAZUH_MIN_RULE_LEVEL must be between 0 and 16.")
        if not self.allowed_groups:
            raise ConfigurationError("At least one Wazuh rule group must be allow-listed.")
        if self.batch_size < 1 or self.batch_size > 500:
            raise ConfigurationError("PHANTOMNET_WAZUH_BATCH_SIZE must be between 1 and 500.")
        if self.poll_interval_seconds <= 0:
            raise ConfigurationError("PHANTOMNET_WAZUH_POLL_INTERVAL_SECONDS must be greater than zero.")

    @classmethod
    def from_environment(cls) -> "PilotConfig":
        groups = tuple(
            group.strip()
            for group in os.environ.get("PHANTOMNET_WAZUH_ALLOWED_GROUPS", "syscheck,syscollector,sca,rootcheck").split(",")
            if group.strip()
        )
        config = cls(
            endpoint_url=os.environ.get("PHANTOMNET_WAZUH_STREAM_URL", ""),
            token_path=Path(os.environ.get("PHANTOMNET_WAZUH_TOKEN_FILE", "/run/secrets/phantomnet_forwarder_token")),
            state_path=Path(os.environ.get("PHANTOMNET_WAZUH_STATE_FILE", "/var/lib/phantomnet-wazuh-forwarder/state.json")),
            spool_directory=Path(os.environ.get("PHANTOMNET_WAZUH_SPOOL_DIR", "/var/lib/phantomnet-wazuh-forwarder/spool")),
            min_rule_level=int(os.environ.get("PHANTOMNET_WAZUH_MIN_RULE_LEVEL", "7")),
            allowed_groups=groups,
            batch_size=int(os.environ.get("PHANTOMNET_WAZUH_BATCH_SIZE", "25")),
            poll_interval_seconds=float(os.environ.get("PHANTOMNET_WAZUH_POLL_INTERVAL_SECONDS", "1")),
            allow_insecure_http=os.environ.get("PHANTOMNET_ALLOW_INSECURE_HTTP", "false").lower() == "true",
        )
        config.validate()
        return config


@dataclass(frozen=True)
class DeliveryResult:
    """The limited response evidence accepted from the telemetry endpoint."""

    status: int
    body: dict[str, Any]


class BatchTransport(Protocol):
    """Small transport interface so network delivery remains testable."""

    def deliver(self, batch: dict[str, Any]) -> DeliveryResult:
        """Deliver one telemetry batch or raise DeliveryError."""


class HttpBatchTransport:
    """HTTPS-only standard-library transport for the read-only stream endpoint."""

    def __init__(self, config: PilotConfig):
        self._config = config

    def _read_token(self) -> str:
        try:
            token = self._config.token_path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise DeliveryError("The PhantomNet forwarder token file cannot be read.") from exc
        if not token or len(token.encode("utf-8")) > MAX_TOKEN_BYTES:
            raise DeliveryError("The PhantomNet forwarder token is missing or exceeds the allowed size.")
        return token

    def deliver(self, batch: dict[str, Any]) -> DeliveryResult:
        payload = json.dumps(batch, separators=(",", ":"), sort_keys=True).encode("utf-8")
        request = Request(
            self._config.endpoint_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-PhantomNet-Forwarder-Token": self._read_token(),
                "User-Agent": "phantomnet-wazuh-pilot-forwarder/1.0",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:  # noqa: S310 - URL is validated pilot configuration.
                raw = response.read(MAX_ALERT_BYTES)
                body = json.loads(raw.decode("utf-8")) if raw else {}
                if response.status != 202:
                    raise DeliveryError(f"PhantomNet refused telemetry batch with HTTP {response.status}.")
                return DeliveryResult(status=response.status, body=body)
        except HTTPError as exc:
            raise DeliveryError(f"PhantomNet refused telemetry batch with HTTP {exc.code}.") from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise DeliveryError("PhantomNet telemetry endpoint is unavailable or returned invalid JSON.") from exc


def _atomic_json_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
        json.dump(value, temporary, sort_keys=True, separators=(",", ":"))
        temporary.write("\n")
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.chmod(temporary_path, 0o600)
    temporary_path.replace(path)


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DeliveryError(f"State file {path} is unreadable or malformed; refusing to guess delivery state.") from exc
    if not isinstance(loaded, dict):
        raise DeliveryError(f"State file {path} is not a JSON object; refusing to guess delivery state.")
    return loaded


def _canonical_alert(alert: Any) -> dict[str, Any]:
    if not isinstance(alert, dict):
        raise DeliveryError("Wazuh alert must be a JSON object.")
    encoded = json.dumps(alert, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_ALERT_BYTES:
        raise DeliveryError("Wazuh alert exceeds the pilot maximum alert size.")
    return alert


def _alert_is_allowed(alert: dict[str, Any], config: PilotConfig) -> bool:
    rule = alert.get("rule")
    if not isinstance(rule, dict):
        return False
    try:
        level = int(rule.get("level", -1))
    except (TypeError, ValueError):
        return False
    groups = rule.get("groups", [])
    if not isinstance(groups, list):
        return False
    return level >= config.min_rule_level and bool(set(config.allowed_groups).intersection(str(group) for group in groups))


def _batch_id(sequence: int, alerts: list[dict[str, Any]]) -> str:
    digest = sha256(json.dumps(alerts, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:24]
    return f"wazuh-pilot-{sequence:020d}-{digest}"


def make_batch(sequence: int, alerts: list[dict[str, Any]]) -> dict[str, Any]:
    if sequence < 1:
        raise DeliveryError("Forwarder sequence must begin at one.")
    if not alerts:
        raise DeliveryError("A telemetry batch must contain at least one Wazuh alert.")
    return {"batch_id": _batch_id(sequence, alerts), "sequence": sequence, "alerts": alerts}


class ReadOnlyTailer:
    """Tails Wazuh JSON alerts without modifying Wazuh or its manager configuration."""

    def __init__(self, config: PilotConfig, alert_file: Path, transport: BatchTransport | None = None):
        self._config = config
        self._alert_file = alert_file
        self._transport = transport or HttpBatchTransport(config)

    def _state(self) -> dict[str, Any]:
        state = _read_json(self._config.state_path, {"offset": 0, "next_sequence": 1})
        offset = state.get("offset")
        sequence = state.get("next_sequence")
        if not isinstance(offset, int) or offset < 0 or not isinstance(sequence, int) or sequence < 1:
            raise DeliveryError("Tailer state is invalid; refusing to replay or skip telemetry silently.")
        return state

    def run_once(self) -> int:
        state = self._state()
        try:
            file_size = self._alert_file.stat().st_size
            offset = 0 if state["offset"] > file_size else state["offset"]
            with self._alert_file.open("r", encoding="utf-8") as alert_stream:
                alert_stream.seek(offset)
                accepted: list[dict[str, Any]] = []
                last_offset = offset
                while len(accepted) < self._config.batch_size:
                    line = alert_stream.readline()
                    if not line:
                        break
                    last_offset = alert_stream.tell()
                    if not line.strip():
                        continue
                    alert = _canonical_alert(json.loads(line))
                    if _alert_is_allowed(alert, self._config):
                        accepted.append(alert)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DeliveryError("Wazuh alert file cannot be parsed safely.") from exc

        if not accepted:
            if last_offset != offset:
                _atomic_json_write(self._config.state_path, {"offset": last_offset, "next_sequence": state["next_sequence"]})
            return 0

        batch = make_batch(state["next_sequence"], accepted)
        self._transport.deliver(batch)
        _atomic_json_write(
            self._config.state_path,
            {"offset": last_offset, "next_sequence": state["next_sequence"] + 1},
        )
        LOGGER.info("Delivered %s Wazuh alerts in sequence %s.", len(accepted), batch["sequence"])
        return len(accepted)

    def run_forever(self) -> None:
        while True:
            try:
                self.run_once()
            except DeliveryError as exc:
                LOGGER.error("Read-only tailer delivery failed closed: %s", exc)
            time.sleep(self._config.poll_interval_seconds)


class SpoolForwarder:
    """Durably accepts Wazuh manager alerts, then drains them in strict sequence."""

    def __init__(self, config: PilotConfig, transport: BatchTransport | None = None):
        self._config = config
        self._transport = transport or HttpBatchTransport(config)

    @property
    def pending_directory(self) -> Path:
        return self._config.spool_directory / "pending"

    def enqueue_file(self, alert_file: Path) -> Path:
        try:
            payload = alert_file.read_bytes()
        except OSError as exc:
            raise DeliveryError("Wazuh integration alert file cannot be read.") from exc
        if not payload or len(payload) > MAX_ALERT_BYTES:
            raise DeliveryError("Wazuh integration alert file is empty or exceeds the pilot maximum size.")
        try:
            alert = _canonical_alert(json.loads(payload.decode("utf-8")))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DeliveryError("Wazuh integration alert file is not valid JSON.") from exc
        if not _alert_is_allowed(alert, self._config):
            return Path()
        digest = sha256(payload).hexdigest()
        self.pending_directory.mkdir(mode=0o750, parents=True, exist_ok=True)
        target = self.pending_directory / f"{digest}.json"
        if target.exists():
            return target
        with tempfile.NamedTemporaryFile("wb", dir=self.pending_directory, delete=False) as temporary:
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.chmod(temporary_path, 0o600)
        try:
            os.link(temporary_path, target)
        except FileExistsError:
            temporary_path.unlink(missing_ok=True)
        else:
            temporary_path.unlink(missing_ok=True)
        return target

    def drain_once(self) -> int:
        self.pending_directory.mkdir(mode=0o750, parents=True, exist_ok=True)
        state = _read_json(self._config.state_path, {"next_sequence": 1})
        sequence = state.get("next_sequence")
        if not isinstance(sequence, int) or sequence < 1:
            raise DeliveryError("Spool state is invalid; refusing to guess telemetry sequence.")
        pending = sorted(self.pending_directory.glob("*.json"))[: self._config.batch_size]
        if not pending:
            return 0
        alerts = [_canonical_alert(json.loads(path.read_text(encoding="utf-8"))) for path in pending]
        batch = make_batch(sequence, alerts)
        self._transport.deliver(batch)
        for path in pending:
            path.unlink(missing_ok=False)
        _atomic_json_write(self._config.state_path, {"next_sequence": sequence + 1})
        LOGGER.info("Delivered spool batch sequence %s containing %s Wazuh alerts.", sequence, len(alerts))
        return len(alerts)

    def drain_forever(self) -> None:
        while True:
            try:
                self.drain_once()
            except (DeliveryError, OSError, json.JSONDecodeError) as exc:
                LOGGER.error("Manager spool delivery failed closed: %s", exc)
            time.sleep(self._config.poll_interval_seconds)


def _locked_execution(lock_path: Path, callback) -> int:
    lock_path.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        return callback()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Telemetry-only Wazuh to PhantomNet pilot forwarder")
    parser.add_argument("mode", choices=("tail", "enqueue", "drain"))
    parser.add_argument("--alert-file", type=Path, help="Wazuh JSON alert file for enqueue mode or JSON-lines alerts file for tail mode")
    parser.add_argument("--once", action="store_true", help="Run one delivery attempt and exit")
    args = parser.parse_args(argv)
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
    config = PilotConfig.from_environment()

    if args.mode == "tail":
        if args.alert_file is None:
            parser.error("--alert-file is required for tail mode")
        tailer = ReadOnlyTailer(config, args.alert_file)
        if args.once:
            tailer.run_once()
        else:
            tailer.run_forever()
        return 0

    spool = SpoolForwarder(config)
    lock_path = config.spool_directory / "forwarder.lock"
    if args.mode == "enqueue":
        if args.alert_file is None:
            parser.error("--alert-file is required for enqueue mode")
        _locked_execution(lock_path, lambda: (spool.enqueue_file(args.alert_file), 0)[1])
        return 0
    if args.once:
        _locked_execution(lock_path, spool.drain_once)
    else:
        spool.drain_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
