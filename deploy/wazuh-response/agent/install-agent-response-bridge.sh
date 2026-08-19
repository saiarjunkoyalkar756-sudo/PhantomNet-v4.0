#!/usr/bin/env bash
# Stage endpoint-side assets for the approval-gated PhantomNet Wazuh response bridge.
# This script does not enable local enforcement, merge Wazuh command configuration, or restart Wazuh.
set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly ENVIRONMENT_FILE="/var/ossec/etc/phantomnet-response.env"
readonly ACTIVE_RESPONSE_DIR="/var/ossec/active-response/bin"

if [[ "${EUID}" -ne 0 ]]; then
  printf 'Run this installer as root.\n' >&2
  exit 1
fi

for required in /var/ossec /var/ossec/etc "${ACTIVE_RESPONSE_DIR}"; do
  if [[ ! -d "${required}" ]]; then
    printf 'Required Wazuh agent path is missing: %s\n' "${required}" >&2
    exit 1
  fi
done

if ! getent group wazuh >/dev/null; then
  printf 'The wazuh group does not exist. Install the Wazuh agent before staging this bridge.\n' >&2
  exit 1
fi

if [[ ! -f "${ENVIRONMENT_FILE}" ]]; then
  printf 'Create %s from phantomnet-response.env.example and load reviewed secret values first.\n' "${ENVIRONMENT_FILE}" >&2
  exit 1
fi

install -o root -g wazuh -m 0750 "${SCRIPT_DIR}/phantomnet-network-response.py" "${ACTIVE_RESPONSE_DIR}/phantomnet-network-response.py"
install -o root -g wazuh -m 0750 "${SCRIPT_DIR}/phantomnet-network-isolate" "${ACTIVE_RESPONSE_DIR}/phantomnet-network-isolate"
install -o root -g wazuh -m 0750 "${SCRIPT_DIR}/phantomnet-network-release" "${ACTIVE_RESPONSE_DIR}/phantomnet-network-release"
chown root:wazuh "${ENVIRONMENT_FILE}"
chmod 0640 "${ENVIRONMENT_FILE}"

cat <<'NEXT_STEPS'

Endpoint response bridge assets are staged but remain inert.

Before any activation:
1. Keep PHANTOMNET_WAZUH_RESPONSE_LOCAL_ENFORCEMENT_ENABLED=false.
2. Review the supplied command fragment and merge only its <command> entries into the approved agent or group configuration.
3. Do not add an <active-response> trigger block; PhantomNet calls the scripts only after a governed approval.
4. Supply a dedicated, lab-tested local executor that emits exact JSON verification evidence for isolate and release.
5. Test the full request -> approval -> command -> signed receipt -> rollback lifecycle in an allow-listed lab agent.
6. Restart or reconfigure Wazuh only through the approved change process.

NEXT_STEPS
