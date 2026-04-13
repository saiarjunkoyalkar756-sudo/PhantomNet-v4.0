import logging
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime, timedelta

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from utils.logger import get_logger
from core.state import get_agent_state # To get agent_id from initialized state
from core.config import load_config # To potentially update config
import yaml # For updating config.yml
import os # For os.umask

logger = get_logger("phantomnet_agent.cert_generator")

# Configuration for certificate storage
CERT_DIR = Path("./certs")
AGENT_KEY_NAME = "agent.key"
AGENT_CERT_NAME = "agent.pem"

async def generate_agent_identity(agent_id: str, common_name: str, 
                                  key_path: Path, cert_path: Path) -> Tuple[Path, Path]:
    """
    Generates a self-signed RSA private key and X.509 certificate for the agent.
    If the key and certificate already exist, they are returned.
    """
    CERT_DIR.mkdir(parents=True, exist_ok=True)

    if key_path.exists() and cert_path.exists():
        logger.info(f"Existing agent identity found. Using {key_path} and {cert_path}.")
        return key_path, cert_path

    logger.info(f"Generating new RSA private key for agent '{agent_id}'...")
    
    # Generate RSA private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Save private key (with restricted permissions)
    # Using os.umask to ensure the file is created with 0o600 permissions
    # Note: This is best effort. Actual security requires proper KMS or secure storage.
    old_umask = os.umask(0o077) # Set umask to 0o077 (r/w for owner only)
    try:
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption() # No encryption for simplicity, use AES256 for production
            ))
        logger.info(f"Private key saved to {key_path}")
    finally:
        os.umask(old_umask) # Restore umask

    logger.info(f"Generating self-signed X.509 certificate for agent '{agent_id}'...")
    
    # Create a self-signed certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"PhantomNet"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u"Agent"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name), # Common name for the agent
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365)) # Valid for 1 year
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.KeyUsage(digital_signature=True, key_encipherment=True, data_encipherment=True,
                                     content_commitment=False, key_agreement=False, key_cert_sign=False,
                                     crl_sign=False, encipher_only=False, decipher_only=False), critical=True)
        .sign(private_key, hashes.SHA256(), default_backend())
    )

    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    logger.info(f"Certificate saved to {cert_path}")

    return key_path, cert_path

async def main():
    """
    Main function to generate agent identity (key and certificate) and update configuration.
    """
    # This script should ideally be run before the agent starts or as part of a provisioning process.
    # For testing, we can simulate agent_id.
    
    # Attempt to get agent_id from global state, or use a default
    try:
        agent_state = get_agent_state()
        agent_id = agent_state.agent_id
    except RuntimeError:
        logger.warning("Agent state not initialized. Using default agent_id 'agent-provisioner'.")
        agent_id = "agent-provisioner"

    key_path = CERT_DIR / f"{agent_id}.key"
    cert_path = CERT_DIR / f"{agent_id}.pem"
    
    await generate_agent_identity(agent_id, agent_id, key_path, cert_path)
    
    logger.info("Agent identity generation script finished.")
    # In a real setup, you'd integrate this with config management.
    # For example, update config.agent.mtls_client_cert_path and config.agent.mtls_client_key_path.
    # Since agent.yml uses "agent-{{autogen}}", we don't automatically modify it here.
    # User should update config/agent.yml manually or through an external process.

if __name__ == '__main__':
    # Ensure logs directory exists for get_logger
    (Path(__file__).parent / ".." / "logs").mkdir(parents=True, exist_ok=True)
    asyncio.run(main())