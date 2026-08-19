from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SIDECAR_COMPOSE = REPOSITORY_ROOT / "deploy/wazuh-pilot/sidecar/docker-compose.yml"
MANAGER_FRAGMENT = REPOSITORY_ROOT / "deploy/wazuh-pilot/manager/ossec.conf.fragment.xml"
MANAGER_ENTRYPOINT = REPOSITORY_ROOT / "deploy/wazuh-pilot/manager/custom-phantomnet-pilot"
MANAGER_SERVICE = REPOSITORY_ROOT / "deploy/wazuh-pilot/manager/phantomnet-wazuh-drain.service"
MANAGER_INSTALLER = REPOSITORY_ROOT / "deploy/wazuh-pilot/manager/install-manager-pilot.sh"


def test_sidecar_manifest_keeps_alert_access_read_only_and_never_exposes_a_service_port():
    compose = SIDECAR_COMPOSE.read_text(encoding="utf-8")

    assert "target: /wazuh-alerts/alerts.json" in compose
    assert "read_only: true" in compose
    assert "secrets:" in compose
    assert "PHANTOMNET_WAZUH_TOKEN_FILE: /run/secrets/phantomnet_forwarder_token" in compose
    assert "cap_drop:" in compose
    assert "- ALL" in compose
    assert "no-new-privileges:true" in compose
    assert "ports:" not in compose
    assert "PHANTOMNET_ALLOW_INSECURE_HTTP: \"false\"" in compose
    assert "containment" not in compose.lower()
    assert "active-response" not in compose.lower()


def test_manager_manifest_queues_only_selected_alerts_and_never_wires_active_response():
    fragment = MANAGER_FRAGMENT.read_text(encoding="utf-8")
    entrypoint = MANAGER_ENTRYPOINT.read_text(encoding="utf-8")

    assert "<name>custom-phantomnet-pilot</name>" in fragment
    assert "<level>7</level>" in fragment
    assert "<group>syscheck,syscollector,sca,rootcheck</group>" in fragment
    assert "<alert_format>json</alert_format>" in fragment
    assert "SpoolForwarder(config).enqueue_file" in entrypoint
    assert "PHANTOMNET_WAZUH_STREAM_URL" in entrypoint
    assert "active-response" not in fragment.lower()
    assert "containment" not in entrypoint.lower()
    assert "urlopen" not in entrypoint


def test_manager_drain_service_is_hardened_and_uses_persistent_state_only():
    service = MANAGER_SERVICE.read_text(encoding="utf-8")
    installer = MANAGER_INSTALLER.read_text(encoding="utf-8")

    assert "User=wazuh" in service
    assert "EnvironmentFile=/etc/phantomnet/wazuh-pilot.env" in service
    assert "NoNewPrivileges=true" in service
    assert "ProtectSystem=strict" in service
    assert "ReadWritePaths=/var/lib/phantomnet-wazuh-pilot" in service
    assert "CapabilityBoundingSet=" in service
    assert "install -d -o wazuh -g wazuh -m 0750" in installer
    assert "chmod 0640 \"${ENVIRONMENT_FILE}\" \"${TOKEN_FILE}\"" in installer
    assert "systemctl restart wazuh-manager" not in installer
