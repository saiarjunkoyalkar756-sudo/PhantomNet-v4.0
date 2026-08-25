"""Source-contract regression for retired Phantom DNA identity experiments."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEVICE_FINGERPRINT_PACKAGE = ROOT / "features/device_fingerprint"
PHANTOM_DNA_PACKAGE = ROOT / "features/phantom_dna"
IAM_API = ROOT / "backend_api/iam_service/api.py"
IAM_AUTH_METHODS = ROOT / "backend_api/iam_service/auth_methods.py"


def test_phantom_dna_identity_experiment_packages_remain_absent():
    assert not DEVICE_FINGERPRINT_PACKAGE.exists()
    assert not PHANTOM_DNA_PACKAGE.exists()


def test_retained_iam_session_fingerprint_boundary_remains_explicit():
    api_source = IAM_API.read_text(encoding="utf-8")
    auth_source = IAM_AUTH_METHODS.read_text(encoding="utf-8")

    assert "device_fingerprint=x_device_fingerprint" in api_source
    assert "device_fingerprint=device_fingerprint" in auth_source
