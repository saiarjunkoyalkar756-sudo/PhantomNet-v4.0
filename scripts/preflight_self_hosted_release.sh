#!/usr/bin/env bash
# Secret-safe preflight for the non-production self-hosted reference topology.
# Run only on an operator-controlled Docker host with a protected lab or production .env.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/deploy/self-hosted/docker-compose.yml"
ENV_FILE="${1:-$ROOT_DIR/deploy/self-hosted/.env}"

fail() {
  printf '%s\n' "$1" >&2
  exit 2
}

[[ -f "$ENV_FILE" ]] || fail "Self-hosted release preflight requires a protected environment file."
[[ -f "$COMPOSE_FILE" ]] || fail "Self-hosted release preflight cannot find the reference Compose manifest."

case "$ENV_FILE" in
  "$ROOT_DIR"/*)
    git -C "$ROOT_DIR" check-ignore -q "$ENV_FILE" || fail "Refusing an environment file that is not excluded from version control."
    ;;
esac

mode="$(stat -c '%a' "$ENV_FILE")"
permissions=$((8#$mode))
(( (permissions & 0077) == 0 )) || fail "Refusing an environment file readable by group or other users."

required_keys=(
  PHANTOMNET_ENVIRONMENT
  PHANTOMNET_SAFE_MODE
  PHANTOMNET_POSTGRES_PASSWORD
  PHANTOMNET_REDIS_PASSWORD
  PHANTOMNET_NEO4J_PASSWORD
  PHANTOMNET_JWT_SECRET_KEY
  PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY
  PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY_ID
  PHANTOMNET_ENDPOINT_CONTAINMENT_ENABLED
  PHANTOMNET_AWS_SECURITY_GROUP_CONTAINMENT_ENABLED
  PHANTOMNET_WAZUH_RESPONSE_ENABLED
)

value_for() {
  local key="$1"
  local matches
  matches="$(grep -Ec "^[[:space:]]*${key}=" "$ENV_FILE" || true)"
  [[ "$matches" == "1" ]] || fail "Self-hosted release preflight requires exactly one value for every required setting."
  sed -n "s/^[[:space:]]*${key}=//p" "$ENV_FILE"
}

is_placeholder() {
  local value="$1"
  [[ -z "$value" || "$value" == *"REPLACE_WITH_"* || "$value" == *"CHANGE_ME"* || "$value" == *"YOUR_"* ]]
}

declare -A settings
for key in "${required_keys[@]}"; do
  settings["$key"]="$(value_for "$key")"
  is_placeholder "${settings[$key]}" && fail "Self-hosted release preflight found an incomplete required setting."
done

case "${settings[PHANTOMNET_ENVIRONMENT]}" in
  staging|production) ;;
  *) fail "Self-hosted release preflight requires a staging or production environment declaration." ;;
esac

[[ "${settings[PHANTOMNET_SAFE_MODE]}" == "false" ]] || fail "Self-hosted release preflight requires safe mode to be explicitly disabled for the controlled topology."

for adapter_key in \
  PHANTOMNET_ENDPOINT_CONTAINMENT_ENABLED \
  PHANTOMNET_AWS_SECURITY_GROUP_CONTAINMENT_ENABLED \
  PHANTOMNET_WAZUH_RESPONSE_ENABLED; do
  [[ "${settings[$adapter_key]}" == "false" ]] || fail "Self-hosted release preflight requires all response adapters to remain disabled."
done

(( ${#settings[PHANTOMNET_JWT_SECRET_KEY]} >= 32 )) || fail "Self-hosted release preflight requires a sufficiently long JWT signing secret."
(( ${#settings[PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY]} >= 32 )) || fail "Self-hosted release preflight requires a sufficiently long containment audit key."

command -v docker >/dev/null 2>&1 || fail "Docker Engine is required for self-hosted release preflight."
docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is required for self-hosted release preflight."

docker compose \
  --project-directory "$ROOT_DIR" \
  --env-file "$ENV_FILE" \
  --file "$COMPOSE_FILE" \
  config --quiet >/dev/null 2>&1 || fail "Self-hosted reference Compose configuration validation failed."

printf '%s\n' "Self-hosted release preflight passed. Retain only secret-free evidence and continue with the controlled lab gates."
