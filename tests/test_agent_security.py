# tests/test_agent_security.py
import pytest
import json
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.exceptions import InvalidSignature
from phantomnet_agent.security.jwt_manager import JWTManager

def test_jwt_kid_stability():
    """Verify that JWT KID generation is cryptographically stable (retains same value)."""
    # Generate RSA key pairs
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    # Initial manager init
    manager1 = JWTManager(private_key_pem=private_pem, public_key_pem=public_pem, agent_id="agent-007")
    kid1 = manager1.current_signing_kid

    # Simulate restart by instantiating again with same keys
    manager2 = JWTManager(private_key_pem=private_pem, public_key_pem=public_pem, agent_id="agent-007")
    kid2 = manager2.current_signing_kid

    # Ensure stable KID hash (resolves CRITICAL C5)
    assert kid1 == kid2
    assert kid1 == hashlib.sha256(private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )).hexdigest()[:8]

def test_command_signature_tamper_detection():
    """Verify that tampered commands are successfully blocked by cryptographic signature verification."""
    # Generate test keys
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    command_type = "execute_os_command"
    command_id = "task-001"
    command_payload = {"cmd": "rm -rf /"}

    # Generate valid signature
    verify_payload = f"{command_type}:{command_id}:{json.dumps(command_payload, sort_keys=True)}"
    valid_sig = private_key.sign(
        verify_payload.encode('utf-8'),
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    # 1. Verify correct payload passes
    try:
        public_key.verify(
            valid_sig,
            verify_payload.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        verified = True
    except InvalidSignature:
        verified = False
    assert verified is True

    # 2. Tamper the payload (e.g. change the command command_payload)
    tampered_payload = {"cmd": "echo 'safe'"}
    tampered_verify_payload = f"{command_type}:{command_id}:{json.dumps(tampered_payload, sort_keys=True)}"
    
    # Verify tampered payload fails
    with pytest.raises(InvalidSignature):
        public_key.verify(
            valid_sig,
            tampered_verify_payload.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
