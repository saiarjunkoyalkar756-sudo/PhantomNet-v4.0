# phantomnet_agent/certs/generate_certs.py
import datetime
import os
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

# Define output directory for certificates
CERT_DIR = Path(__file__).parent.resolve()
SERVER_CERT_DIR = CERT_DIR / "server"
AGENT_CERT_DIR = CERT_DIR / "agent"


def generate_self_signed_cert(
    common_name: str, key_path: Path, cert_path: Path, is_ca: bool = False
):
    """
    Generates a private key and a self-signed certificate.
    If `is_ca` is True, it creates a Certificate Authority.
    """
    # Generate private key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Write private key to disk
    with open(key_path, "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Create subject and issuer
    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
    )

    # Build certificate
    cert_builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        )
    )

    if is_ca:
        cert_builder = cert_builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True
        )
    else:
        # Add DNS names for server/client certs
        cert_builder = cert_builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        )

    # Sign the certificate with its own private key
    certificate = cert_builder.sign(key, hashes.SHA256())

    # Write certificate to disk
    with open(cert_path, "wb") as f:
        f.write(certificate.public_bytes(serialization.Encoding.PEM))

    print(f"Generated key: {key_path}")
    print(f"Generated cert: {cert_path}")
    return key, certificate


def generate_cert_signed_by_ca(
    common_name: str,
    ca_key,
    ca_cert,
    key_out_path: Path,
    cert_out_path: Path,
):
    """
    Generates a certificate signed by a given Certificate Authority.
    """
    # Generate private key for the new certificate
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    with open(key_out_path, "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Create subject for the new certificate
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])

    # Build the certificate, signed by the CA
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        )
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        )
    )

    certificate = builder.sign(ca_key, hashes.SHA256())

    with open(cert_out_path, "wb") as f:
        f.write(certificate.public_bytes(serialization.Encoding.PEM))

    print(f"Generated signed key: {key_out_path}")
    print(f"Generated signed cert: {cert_out_path}")

def main():
    """
    Main function to generate all necessary certificates for mTLS.
    """
    print("--- Generating mTLS Certificates for PhantomNet ---")

    # Create output directories if they don't exist
    SERVER_CERT_DIR.mkdir(exist_ok=True)
    AGENT_CERT_DIR.mkdir(exist_ok=True)

    # 1. Generate the Certificate Authority (CA)
    print("\nStep 1: Generating Certificate Authority...")
    ca_key, ca_cert = generate_self_signed_cert(
        common_name="PhantomNet Root CA",
        key_path=CERT_DIR / "ca.key",
        cert_path=CERT_DIR / "ca.crt",
        is_ca=True,
    )

    # 2. Generate the Server Certificate (for the backend)
    print("\nStep 2: Generating Backend Server Certificate...")
    generate_cert_signed_by_ca(
        common_name="phantomnet-backend",
        ca_key=ca_key,
        ca_cert=ca_cert,
        key_out_path=SERVER_CERT_DIR / "server.key",
        cert_out_path=SERVER_CERT_DIR / "server.crt",
    )

    # 3. Generate the Client Certificate (for the agent)
    print("\nStep 3: Generating Agent Client Certificate...")
    generate_cert_signed_by_ca(
        common_name="phantomnet-agent",
        ca_key=ca_key,
        ca_cert=ca_cert,
        key_out_path=AGENT_CERT_DIR / "agent.key",
        cert_out_path=AGENT_CERT_DIR / "agent.crt",
    )

    print("\n--- Certificate Generation Complete ---")
    print(
        "Place the 'server' certs on your backend and the 'agent' certs with your agent."
    )
    print(
        f"The CA certificate '{CERT_DIR / 'ca.crt'}' must be trusted by both."
    )


if __name__ == "__main__":
    main()
