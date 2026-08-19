#!/usr/bin/env bash
# Isolated, non-production Docker topology validation. Never use this runner with production services or secrets.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.integration.yml"
ARTIFACT_DIR="${PHANTOMNET_TOPOLOGY_ARTIFACT_DIR:-$ROOT_DIR/artifacts}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PROJECT_NAME="phantomnet-topology-${TIMESTAMP,,}"
LOG_FILE="$ARTIFACT_DIR/docker_topology_validation_${TIMESTAMP}.log"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker Engine is required for topology validation." >&2
  exit 2
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is required for topology validation." >&2
  exit 2
fi

mkdir -p "$ARTIFACT_DIR"

compose() {
  docker compose --project-name "$PROJECT_NAME" --file "$COMPOSE_FILE" --profile verify "$@"
}

cleanup() {
  compose logs --no-color >>"$LOG_FILE" 2>&1 || true
  compose down --volumes --remove-orphans >>"$LOG_FILE" 2>&1 || true
}
trap cleanup EXIT

{
  echo "timestamp=${TIMESTAMP}"
  echo "project=${PROJECT_NAME}"
  echo "scope=isolated_postgres_redis_redpanda_neo4j_round_trip_validation"
  echo "status=started"
} | tee "$LOG_FILE"

compose config >>"$LOG_FILE"
compose up --build --abort-on-container-exit --exit-code-from integration-tests 2>&1 | tee -a "$LOG_FILE"

echo "status=passed" | tee -a "$LOG_FILE"
echo "Topology validation evidence: $LOG_FILE"
