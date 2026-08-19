#!/usr/bin/env bash
# Non-production Docker recovery validation only. Never point this runner at a production Compose project.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.recovery-validation.yml"
ARTIFACT_DIR="${PHANTOMNET_RECOVERY_ARTIFACT_DIR:-$ROOT_DIR/artifacts}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PROJECT_NAME="phantomnet-recovery-${TIMESTAMP,,}"
ARTIFACT_FILE="$ARTIFACT_DIR/docker_recovery_validation_${TIMESTAMP}.jsonl"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for broker and PostgreSQL recovery validation." >&2
  exit 2
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is required for broker and PostgreSQL recovery validation." >&2
  exit 2
fi
: "${RECOVERY_DB_PASSWORD:?Set an ephemeral non-production RECOVERY_DB_PASSWORD before running this validation.}"
: "${RECOVERY_AUDIT_HMAC_KEY:?Set an ephemeral non-production RECOVERY_AUDIT_HMAC_KEY before running this validation.}"
: "${RECOVERY_AUDIT_HMAC_KEY_ID:?Set an ephemeral non-production RECOVERY_AUDIT_HMAC_KEY_ID before running this validation.}"

mkdir -p "$ARTIFACT_DIR"
export RECOVERY_DB_PASSWORD
export RECOVERY_AUDIT_HMAC_KEY
export RECOVERY_AUDIT_HMAC_KEY_ID
export RECOVERY_RUN_ID="docker-recovery-${TIMESTAMP}"

compose() {
  docker compose --project-name "$PROJECT_NAME" --file "$COMPOSE_FILE" "$@"
}

cleanup() {
  compose down --volumes --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

run_probe() {
  local mode="$1"
  compose run --rm --no-deps recovery-probe "$mode" | tee -a "$ARTIFACT_FILE"
}

run_probe_expect_failure() {
  local mode="$1"
  local check_name="$2"
  local status
  set +e
  compose run --rm --no-deps recovery-probe "$mode" | tee -a "$ARTIFACT_FILE"
  status=${PIPESTATUS[0]}
  set -e
  if [[ "$status" -eq 0 ]]; then
    echo "${check_name} unexpectedly succeeded while its required dependency was stopped." >&2
    return 1
  fi
  printf '{"check":"%s","status":"passed"}\n' "$check_name" | tee -a "$ARTIFACT_FILE"
}

wait_for_redpanda() {
  local attempt
  for attempt in $(seq 1 30); do
    if compose exec -T redpanda rpk cluster health --exit-when-healthy >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "Redpanda did not become healthy after restart." >&2
  return 1
}

wait_for_postgres() {
  local attempt
  for attempt in $(seq 1 30); do
    if compose exec -T postgres pg_isready -U recovery_validator -d recovery_validation >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "PostgreSQL did not become healthy after restart." >&2
  return 1
}

echo '{"phase":"startup","status":"started"}' | tee "$ARTIFACT_FILE"
compose build recovery-probe
compose up --detach --build redpanda postgres
wait_for_redpanda
wait_for_postgres
run_probe combined

echo '{"phase":"broker_restart","status":"started"}' | tee -a "$ARTIFACT_FILE"
run_probe audit
compose stop redpanda
run_probe_expect_failure broker broker_outage_fail_closed
run_probe audit
compose start redpanda
wait_for_redpanda
run_probe broker
run_probe audit

echo '{"phase":"postgres_restart","status":"started"}' | tee -a "$ARTIFACT_FILE"
run_probe audit
compose stop postgres
run_probe_expect_failure postgres postgres_outage_fail_closed
compose start postgres
wait_for_postgres
run_probe postgres
run_probe audit

echo '{"phase":"complete","status":"passed"}' | tee -a "$ARTIFACT_FILE"
echo "Recovery validation evidence: $ARTIFACT_FILE"
