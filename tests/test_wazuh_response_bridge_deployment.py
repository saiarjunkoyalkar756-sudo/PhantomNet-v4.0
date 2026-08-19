from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / "deploy" / "wazuh-response" / "agent"


def test_endpoint_response_script_is_signature_bound_disabled_by_default_and_executor_verified():
    source = (AGENT_DIR / "phantomnet-network-response.py").read_text(encoding="utf-8")

    assert "PHANTOMNET_WAZUH_RESPONSE_COMMAND_HMAC_KEY" in source
    assert "PHANTOMNET_WAZUH_RESPONSE_RECEIPT_HMAC_KEY" in source
    assert "PHANTOMNET_WAZUH_RESPONSE_LOCAL_ENFORCEMENT_ENABLED" in source
    assert '!= "true"' in source
    assert 'evidence.get("verified") is not True' in source
    assert 'evidence.get("network_state") != expected_state' in source
    assert 'parsed.scheme != "https"' in source
    assert "iptables" not in source
    assert "nft " not in source
    assert "ufw " not in source


def test_command_fragment_defines_named_commands_without_automatic_wazuh_triggering():
    fragment = (AGENT_DIR / "ossec.command.fragment.xml").read_text(encoding="utf-8")

    assert "phantomnet-network-isolate" in fragment
    assert "phantomnet-network-release" in fragment
    assert "<timeout_allowed>no</timeout_allowed>" in fragment
    assert "\n<active-response>" not in fragment


def test_agent_installer_stages_only_and_never_restarts_or_enables_wazuh_response():
    installer = (AGENT_DIR / "install-agent-response-bridge.sh").read_text(encoding="utf-8")

    assert "PHANTOMNET_WAZUH_RESPONSE_LOCAL_ENFORCEMENT_ENABLED=false" in installer
    assert "<active-response>" in installer
    assert "systemctl restart" not in installer
    assert "service wazuh" not in installer
    assert "install -o root -g wazuh -m 0750" in installer


def test_response_environment_template_contains_placeholders_not_real_credentials():
    environment = (AGENT_DIR / "phantomnet-response.env.example").read_text(encoding="utf-8")

    assert "replace-from-secret-store" in environment
    assert "PHANTOMNET_WAZUH_RESPONSE_LOCAL_ENFORCEMENT_ENABLED=false" in environment
    assert "PHANTOMNET_WAZUH_RESPONSE_EXECUTOR=" in environment
