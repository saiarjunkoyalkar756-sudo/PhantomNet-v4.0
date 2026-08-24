from __future__ import annotations

import json
from pathlib import Path

from scripts.check_agent_source_contract import validate


ROOT = Path(__file__).resolve().parents[1]
PORTAL_SOURCES = [
    ROOT / "phantomnet-website/app/layout.tsx",
    ROOT / "phantomnet-website/app/about/page.tsx",
    ROOT / "phantomnet-website/app/ai-intelligence/page.tsx",
    ROOT / "phantomnet-website/app/architecture/page.tsx",
    ROOT / "phantomnet-website/app/features/page.tsx",
    ROOT / "phantomnet-website/app/platform/page.tsx",
    ROOT / "phantomnet-website/app/roadmap/page.tsx",
    ROOT / "phantomnet-website/app/security-trust/page.tsx",
]


def test_public_portal_does_not_reintroduce_unsupported_autonomy_or_blockchain_claims():
    content = "\n".join(path.read_text(encoding="utf-8").casefold() for path in PORTAL_SOURCES)

    for forbidden in (
        "blockchain-powered",
        "immutable blockchain",
        "self-healing cyber defense",
        "autonomous cyber defense",
        "billions of events",
        "millions of events per second",
        "self-evolving threat brain",
        "neural federation council",
        "cognitive core intelligence",
        "post-quantum cryptographic audit",
    ):
        assert forbidden not in content

    assert "tamper-evident" in content
    assert "approval-bound" in content
    assert "roadmap" in content


def test_license_is_complete_mit_text_and_not_a_placeholder():
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

    assert license_text.startswith("MIT License\n")
    assert "Permission is hereby granted, free of charge" in license_text
    assert "THE SOFTWARE IS PROVIDED \"AS IS\"" in license_text
    assert "..." not in license_text


def test_ci_uses_committed_frontend_lockfiles_and_legacy_compose_is_explicitly_nonproduction():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert workflow.count("run: npm ci") == 2
    assert workflow.count("run: npm audit --audit-level=low") == 2
    assert "Legacy broad development topology" in compose
    assert "deploy/self-hosted/docker-compose.yml" in compose
    assert "SERVICE_name" not in compose
    assert "SERVICE_NAME: 'audit-log-collector'" not in compose
    assert "audit-log-collector:" not in compose


def test_portable_agent_source_contract_is_explicit_about_its_limits_and_passes_for_current_tree():
    result = validate(ROOT)

    assert result["missing_paths"] == []
    assert result["python_compilation_passed"] is True
    assert result["python_source_count"] > 0
    assert result["native_binary_proof"] is False
    assert result["device_runtime_proof"] is False


def test_frontend_runtime_dependency_baselines_include_the_remediated_versions():
    dashboard = json.loads((ROOT / "dashboard_frontend/package.json").read_text(encoding="utf-8"))
    portal = json.loads((ROOT / "phantomnet-website/package.json").read_text(encoding="utf-8"))

    assert dashboard["dependencies"]["axios"] == "^1.19.0"
    assert dashboard["dependencies"]["js-cookie"] == "^3.0.8"
    assert dashboard["dependencies"]["react-router-dom"] == "^7.18.2"
    assert portal["dependencies"]["next"] == "^16.3.1"


def test_ci_workflow_renames_do_not_claim_automatic_cloud_deployment_or_device_proof():
    build_workflow = (ROOT / ".github/workflows/build-and-test.yml").read_text(encoding="utf-8")
    platform_workflow = (ROOT / ".github/workflows/platforms.yml").read_text(encoding="utf-8")
    deployment_workflow = (ROOT / ".github/workflows/cd.yml").read_text(encoding="utf-8")

    assert "Agent Source Contract" in build_workflow
    assert "Cross-Platform Source Contract" in platform_workflow
    assert "native binary" in build_workflow.casefold()
    assert "android/termux runtime behavior" in build_workflow.casefold()
    assert "aws-actions/configure-aws-credentials" not in deployment_workflow
    assert "No Docker service was started" in deployment_workflow
