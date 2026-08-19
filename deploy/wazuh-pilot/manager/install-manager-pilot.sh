#!/usr/bin/env bash
# Install the telemetry-only Wazuh Phase 1 manager integration assets.
# This script never changes Wazuh Active Response and never calls a containment endpoint.
set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly REPOSITORY_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"
readonly INSTALL_ROOT="/opt/phantomnet-wazuh-pilot"
readonly STATE_ROOT="/var/lib/phantomnet-wazuh-pilot"
readonly ENVIRONMENT_FILE="/etc/phantomnet/wazuh-pilot.env"
readonly TOKEN_FILE="/etc/phantomnet/wazuh-forwarder-token"

if [[ "${EUID}" -ne 0 ]]; then
  printf 'Run this installer as root.\n' >&2
  exit 1
fi

for required in /var/ossec /var/ossec/integrations /var/ossec/etc/ossec.conf; do
  if [[ ! -e "${required}" ]]; then
    printf 'Required Wazuh path is missing: %s\n' "${required}" >&2
    exit 1
  fi
done

if ! id wazuh >/dev/null 2>&1; then
  printf 'The wazuh service account does not exist. Install Wazuh before this pilot package.\n' >&2
  exit 1
fi

if [[ ! -f "${ENVIRONMENT_FILE}" ]]; then
  printf 'Create %s from wazuh-pilot.env.example and set the tenant-bound HTTPS stream URL first.\n' "${ENVIRONMENT_FILE}" >&2
  exit 1
fi
if [[ ! -f "${TOKEN_FILE}" ]]; then
  printf 'Create %s with the one-time PhantomNet forwarder token first.\n' "${TOKEN_FILE}" >&2
  exit 1
fi
if [[ ! -s "${TOKEN_FILE}" ]]; then
  printf 'The PhantomNet forwarder token file is empty.\n' >&2
  exit 1
fi

install -d -o root -g root -m 0755 "${INSTALL_ROOT}"
install -d -o wazuh -g wazuh -m 0750 "${STATE_ROOT}" "${STATE_ROOT}/spool"
install -d -o root -g root -m 0750 /etc/phantomnet

rm -rf "${INSTALL_ROOT}/integrations"
cp -a "${REPOSITORY_ROOT}/integrations" "${INSTALL_ROOT}/integrations"
chown -R root:root "${INSTALL_ROOT}/integrations"
find "${INSTALL_ROOT}/integrations" -type d -exec chmod 0755 {} +
find "${INSTALL_ROOT}/integrations" -type f -name '*.py' -exec chmod 0644 {} +

install -o root -g wazuh -m 0750 "${SCRIPT_DIR}/custom-phantomnet-pilot" /var/ossec/integrations/custom-phantomnet-pilot
install -o root -g root -m 0644 "${SCRIPT_DIR}/phantomnet-wazuh-drain.service" /etc/systemd/system/phantomnet-wazuh-drain.service
chown root:wazuh "${ENVIRONMENT_FILE}" "${TOKEN_FILE}"
chmod 0640 "${ENVIRONMENT_FILE}" "${TOKEN_FILE}"

systemctl daemon-reload
systemctl enable --now phantomnet-wazuh-drain.service

cat <<'NEXT_STEPS'

Manager assets installed. Before enabling Wazuh delivery:
1. Review and manually merge ossec.conf.fragment.xml inside <ossec_config>.
2. Validate the full Wazuh configuration with the local Wazuh verification procedure.
3. Restart wazuh-manager in the approved maintenance window.
4. Confirm the drain service is healthy with:
   systemctl status phantomnet-wazuh-drain.service
5. Send one selected lab alert and confirm the PhantomNet stream response shows
   adapter_mode=read_only_streaming and automatic_enforcement=false.

NEXT_STEPS
