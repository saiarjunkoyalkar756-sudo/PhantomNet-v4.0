#!/usr/bin/env bash
# Disposable containerized dry-run for the governed Wazuh response lifecycle.
# It never contacts a Wazuh manager or a real endpoint and must not receive production secrets.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.wazuh-governed-dry-run.yml"
ARTIFACT_ROOT="${PHANTOMNET_WAZUH_DRY_RUN_ARTIFACT_ROOT:-$ROOT_DIR/artifacts}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PROJECT_NAME="phantomnet-wazuh-dry-run-${TIMESTAMP,,}"
RUN_DIR="$ARTIFACT_ROOT/wazuh_governed_response_dry_run_${TIMESTAMP}"
LOG_FILE="$RUN_DIR/docker_run.log"

if ! command -v docker >/dev/null 2>&1; then
  printf 'Docker Engine is required for the containerized dry-run.\n' >&2
  exit 2
fi
if ! docker compose version >/dev/null 2>&1; then
  printf 'Docker Compose v2 is required for the containerized dry-run.\n' >&2
  exit 2
fi
if [[ ! -f "$COMPOSE_FILE" ]]; then
  printf 'Dry-run Compose manifest is missing: %s\n' "$COMPOSE_FILE" >&2
  exit 2
fi

mkdir -p "$RUN_DIR"
export DRY_RUN_ARTIFACT_HOST_DIR="$RUN_DIR"

compose() {
  docker compose --project-name "$PROJECT_NAME" --file "$COMPOSE_FILE" "$@"
}

cleanup() {
  compose down --volumes --remove-orphans >>"$LOG_FILE" 2>&1 || true
}
trap cleanup EXIT

{
  printf 'timestamp=%s\n' "$TIMESTAMP"
  printf 'project=%s\n' "$PROJECT_NAME"
  printf 'scope=isolated_sqlite_simulated_wazuh_no_network_no_endpoint_change\n'
  printf 'status=started\n'
} | tee "$LOG_FILE"

compose config >>"$LOG_FILE"
compose up --build --abort-on-container-exit --exit-code-from governed-response-dry-run 2>&1 | tee -a "$LOG_FILE"

result_file="$(find "$RUN_DIR" -maxdepth 1 -type f -name 'wazuh_governed_response_dry_run_*.json' -print -quit)"
if [[ -z "$result_file" ]]; then
  printf 'Dry-run container exited without a result artifact.\n' >&2
  exit 1
fi
if ! grep -q '"status": "passed"' "$result_file" || ! grep -q '"audit_chain_valid": true' "$result_file"; then
  printf 'Dry-run artifact did not contain passed signed-audit evidence.\n' >&2
  exit 1
fi

printf 'status=passed\n' | tee -a "$LOG_FILE"
printf 'Docker dry-run evidence: %s\n' "$RUN_DIR"
