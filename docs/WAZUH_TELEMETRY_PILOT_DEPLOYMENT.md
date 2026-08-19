# Wazuh Phase 1 Telemetry Pilot Deployment

**Purpose:** Deploy selected Wazuh alerts into a tenant-bound PhantomNet forwarder without changing endpoint state, calling Wazuh Active Response, or creating a containment path.

> **Safety model:** Both packages are telemetry-only. They can send alert JSON to `POST /wazuh/forwarders/{forwarder_id}/stream`; they cannot call a containment route, Wazuh Active Response, or the Wazuh API. A successful delivery is evidence of accepted telemetry—not evidence of host isolation or remediation.

## Choose one deployment pattern

| Pattern | Best use | Main benefit | Operational tradeoff |
|---|---|---|---|
| **Read-only sidecar** | First deployment on a Wazuh manager host that can run Docker | Does not modify Wazuh manager configuration or alert handling | Tails `alerts.json`; delivery has a short polling delay and needs read-only log-file access. |
| **Manager-integrated queue** | Environments requiring manager-driven alert selection with no sidecar Docker runtime | Wazuh Integrator sends only selected alerts to a local durable queue | Requires a reviewed Wazuh `ossec.conf` change and an approved manager restart. |

The lower-risk starting point is the **read-only sidecar**. Wazuh’s Integrator module is a valid manager-side option and supports `custom-` integrations, JSON alert files, and filters by level or group.[1] The manager-integrated package intentionally queues locally first; it does not perform an outbound HTTP request within the Wazuh manager’s alert-processing path.

## Package inventory

| Artifact | Purpose |
|---|---|
| `integrations/wazuh_pilot_forwarder/forwarder.py` | Shared standard-library forwarder; TLS validation, filtering, batching, deterministic sequences, local state, and durable spool. |
| `infra/docker/wazuh-pilot-forwarder.Dockerfile` | Minimal non-root container image for the sidecar. |
| `deploy/wazuh-pilot/sidecar/docker-compose.yml` | Read-only Docker sidecar, secret file, no ports, dropped capabilities, immutable root filesystem, persistent state volume. |
| `deploy/wazuh-pilot/manager/ossec.conf.fragment.xml` | Selected Wazuh Integrator configuration block. |
| `deploy/wazuh-pilot/manager/custom-phantomnet-pilot` | Wazuh custom integration script that queues only eligible alert JSON. |
| `deploy/wazuh-pilot/manager/phantomnet-wazuh-drain.service` | Hardened Wazuh-account service that drains the local queue over HTTPS. |
| `deploy/wazuh-pilot/manager/install-manager-pilot.sh` | Conservative installer that stages assets but does not merge `ossec.conf` or restart Wazuh. |

## Before either deployment

### 1. Create the PhantomNet forwarder

From an authenticated PhantomNet account with the `config:write` capability, create one forwarder for exactly one tenant:

```bash
curl --fail-with-body \
  -X POST "$PHANTOMNET_ENDPOINT_INVENTORY_URL/wazuh/forwarders" \
  -H "Authorization: Bearer $PHANTOMNET_OPERATOR_JWT" \
  -H "Content-Type: application/json" \
  --data '{"name":"wazuh-pilot-tenant-a"}'
```

Save the returned `forwarder_id` and one-time `forwarder_token` in the approved secret store. The stream URL format is:

```text
https://<phantomnet-endpoint-inventory>/wazuh/forwarders/<forwarder_id>/stream
```

The receiving endpoint rejects invalid/revoked credentials (`401`), repeated batches, and out-of-order sequences (`409`). Its result reports `adapter_mode: "read_only_streaming"` and `automatic_enforcement: false`. [Forwarder API](../backend_api/endpoint_inventory_service/main.py) [Streaming regression tests](../tests/test_wazuh_forwarder_streaming.py)

### 2. Select a narrow alert scope

Start with the shipped pilot filters:

| Setting | Initial value | Reason |
|---|---|---|
| Minimum rule level | `7` | Reduces volume while keeping actionable pilot events. |
| Rule groups | `syscheck,syscollector,sca,rootcheck` | Focuses on integrity, inventory, posture, and rootcheck evidence. |
| Batch size | `25` | Limits recovery/replay blast radius. |
| Automatic enforcement | `false` | Required Phase 1 boundary. |

Do not expand filters until the team can demonstrate forwarder registration, valid ingestion, credential rejection, replay rejection, Wazuh independence during PhantomNet outage, and tenant-correct asset evidence.

## Option A — read-only Docker sidecar

The sidecar tails the Wazuh manager’s newline-delimited JSON alert stream. It mounts `alerts.json` **read-only**, publishes no service port, runs as UID/GID `65532`, drops all Linux capabilities, uses a read-only root filesystem, and stores only a checkpoint in a named volume.

### Stage configuration and secret

```bash
cd deploy/wazuh-pilot/sidecar
cp .env.example .env
chmod 600 .env
```

Update `.env` with the tenant-bound HTTPS stream URL and the actual host path to Wazuh `alerts.json`. Then create the separate token file. Do not place the token in `.env`.

```bash
sudo install -d -o root -g root -m 0750 /etc/phantomnet
sudo sh -c 'umask 077; printf "%s" "$PHANTOMNET_FORWARDER_TOKEN" > /etc/phantomnet/wazuh-forwarder-token'
sudo chmod 600 /etc/phantomnet/wazuh-forwarder-token
```

### Start and validate

```bash
# From deploy/wazuh-pilot/sidecar
sudo docker compose --env-file .env up -d --build
sudo docker compose ps
sudo docker compose logs --tail=100 wazuh-telemetry-sidecar
```

Generate one approved lab alert that matches the selected filters. Confirm the sidecar logs one accepted sequence and PhantomNet creates the expected tenant-scoped asset/integrity evidence. Then stop the sidecar and confirm Wazuh continues to detect and retain alerts normally.

### Sidecar rollback

```bash
sudo docker compose down
```

This stops only the sidecar. It does not alter Wazuh agents, rules, manager configuration, or historical Wazuh alerts. Retain the named state volume for an orderly resume; remove it only after the forwarder is revoked and the operator has reconciled the final sequence.

## Option B — Wazuh Integrator with local durable queue

Wazuh documents that a custom Integrator script is placed under `/var/ossec/integrations/`, begins with an interpreter line, is executable and owned by `root:wazuh`, and receives the alert-file path as its first argument.[1] The supplied custom script follows that contract. It reads the alert JSON, applies the configured filter, and writes a deduplicated spool item. The separate `phantomnet-wazuh-drain.service` then sends batches to PhantomNet.

### Stage the environment and token

```bash
sudo install -d -o root -g root -m 0750 /etc/phantomnet
sudo cp deploy/wazuh-pilot/manager/wazuh-pilot.env.example /etc/phantomnet/wazuh-pilot.env
sudo chown root:wazuh /etc/phantomnet/wazuh-pilot.env
sudo chmod 640 /etc/phantomnet/wazuh-pilot.env
sudo sh -c 'umask 077; printf "%s" "$PHANTOMNET_FORWARDER_TOKEN" > /etc/phantomnet/wazuh-forwarder-token'
sudo chown root:wazuh /etc/phantomnet/wazuh-forwarder-token
sudo chmod 640 /etc/phantomnet/wazuh-forwarder-token
```

Set the forwarder stream URL in `/etc/phantomnet/wazuh-pilot.env`. The queue script parses only allow-listed `KEY=value` settings; it does not source the file as shell code.

### Install the queue and drain assets

```bash
sudo deploy/wazuh-pilot/manager/install-manager-pilot.sh
```

The installer stages the Python forwarder package under `/opt/phantomnet-wazuh-pilot`, creates `/var/lib/phantomnet-wazuh-pilot` as `wazuh:wazuh`, installs the custom script as `root:wazuh` mode `0750`, and enables the independent drain service. It does **not** modify `ossec.conf` or restart the Wazuh manager.

### Apply Wazuh manager configuration as a reviewed change

Manually merge the `ossec.conf.fragment.xml` contents inside the `<ossec_config>` element of `/var/ossec/etc/ossec.conf`. Validate the full Wazuh configuration with your organization’s Wazuh manager configuration-check procedure, then restart the manager only in the approved maintenance window. Wazuh requires a manager restart after Integrator configuration changes.[1]

After restart, validate:

```bash
sudo systemctl status phantomnet-wazuh-drain.service
sudo journalctl -u phantomnet-wazuh-drain.service --since "15 minutes ago"
sudo ls -la /var/lib/phantomnet-wazuh-pilot/spool/pending
```

### Manager-integrated rollback

1. Remove or comment out only the `custom-phantomnet-pilot` `<integration>` block from `ossec.conf`.
2. Validate the full Wazuh configuration and restart the manager in the approved window.
3. Stop and disable the drain service: `sudo systemctl disable --now phantomnet-wazuh-drain.service`.
4. Revoke the matching PhantomNet forwarder; keep the local spool and PhantomNet records for reconciliation.

## Acceptance test matrix

| Test | Expected result |
|---|---|
| Valid selected Wazuh alert | A `202` stream response; canonical telemetry is created; `automatic_enforcement` remains `false`. |
| Rule below level or outside group | Alert is not forwarded; Wazuh alert processing continues normally. |
| Invalid or revoked forwarder token | PhantomNet returns `401`; no endpoint action occurs. |
| Duplicate batch or sidecar restart | PhantomNet rejects replay or the local checkpoint prevents duplicate delivery. |
| PhantomNet unavailable | Sidecar retains its checkpoint and retries on later reads; manager package retains the local spool; Wazuh detection continues. |
| Sidecar/manager package stopped | Wazuh agents and Wazuh alerting continue; only PhantomNet telemetry forwarding pauses. |
| Any containment request | Must be absent. This is a release blocker for Phase 1. |

## Validation status

The package has isolated regression coverage for HTTPS-only validation, allow-listed selection, deterministic tailer sequencing, failed-delivery state safety, manager-spool deduplication, no published sidecar ports, external secret files, dropped capabilities, hardened systemd controls, and absence of Active Response or containment wiring. The current tests run without Docker or Wazuh infrastructure; a live manager and Docker-host pilot remains an operator-side validation step.

## References

[1]: https://documentation.wazuh.com/current/user-manual/manager/integration-with-external-apis.html "Wazuh External API integration and custom scripts"
