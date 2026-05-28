from fastapi import HTTPException
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.x509.extensions import SubjectAlternativeName, DNSName
from datetime import datetime, timedelta, timezone
import jwt
import uuid
from typing import Optional, Dict, Any, List

from .jti_store import JtiStore, default_jti_store
from backend_api.shared.settings import settings

# Global set for simple in-memory token revocation
revoked_tokens = set()

def generate_key_pair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_pem, public_pem


def generate_self_signed_ca():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "PhantomNet Self-Signed CA"),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=3650))  # 10-year validity
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .sign(private_key, hashes.SHA256())
    )

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    return private_key_pem, cert_pem


def sign_certificate(
    public_key_pem: str,
    ca_private_key_pem: str,
    ca_certificate_pem: str,
    common_name: str,
):
    ca_private_key = serialization.load_pem_private_key(
        ca_private_key_pem.encode("utf-8"), password=None
    )
    ca_cert = x509.load_pem_x509_certificate(ca_certificate_pem.encode("utf-8"))

    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(serialization.load_pem_public_key(public_key_pem.encode("utf-8")))
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))  # 1-year validity
        .add_extension(SubjectAlternativeName([DNSName(common_name)]), critical=False)
        .sign(ca_private_key, hashes.SHA256())
    )

    return cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")


def sign_data(data: bytes, private_key_pem: str) -> str:
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"), password=None
    )
    signature = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )
    return signature.hex()


def verify_signature(data: bytes, signature: str, public_key_pem: str) -> bool:
    public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
    try:
        public_key.verify(
            bytes.fromhex(signature),
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
        return True
    except InvalidSignature:
        return False


def create_inter_node_jwt(
    agent_id: int, cluster_id: str, scope: str, private_key_pem: str
) -> str:
    now = datetime.now(timezone.utc)
    token_lifetime = timedelta(seconds=120)
    payload = {
        "iss": str(agent_id),
        "sub": str(agent_id),
        "aud": cluster_id,
        "iat": now,
        "exp": now + token_lifetime,
        "jti": str(uuid.uuid4()),  # Unique JWT ID for replay protection
        "scope": scope,
    }
    # Use RS256 for signing with RSA private key
    encoded_jwt = jwt.encode(payload, private_key_pem, algorithm="RS256")
    return encoded_jwt


def verify_inter_node_jwt(
    jwt_token: str,
    public_key_pem: str,
    cluster_id: str,
    jti_store: JtiStore = default_jti_store,
) -> dict:
    # Check revocation status first
    if jwt_token in revoked_tokens:
        raise HTTPException(status_code=401, detail="Token has been revoked.")

    try:
        decoded_payload = jwt.decode(
            jwt_token, public_key_pem, algorithms=["RS256"], audience=cluster_id
        )

        # Replay protection
        jti = decoded_payload.get("jti")
        if not jti:
            raise jwt.InvalidTokenError("JWT ID (jti) claim is missing.")
            
        if jti_store.is_jti_used(jti):
            raise jwt.InvalidTokenError("JWT ID (jti) has been used already.")
        
        # Mark JTI as used
        exp = decoded_payload.get("exp")
        iat = decoded_payload.get("iat")
        if exp and iat:
            token_lifetime = timedelta(seconds=(exp - iat))
            # Add a small buffer to the expiration
            jti_store.mark_jti_as_used(jti, expires_in=token_lifetime + timedelta(seconds=60))

        return decoded_payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="JWT has expired")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid audience")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid JWT: {e}")

# --- Token Revocation & Refresh Support ---
def revoke_jwt(token: str):
    """Adds a token to the revoked tokens list."""
    revoked_tokens.add(token)

def refresh_jwt(token: str, private_key_pem: str, token_expiry_minutes: int = 15) -> str:
    """Refreshes a valid or slightly expired token if validation holds."""
    # Decode token ignoring expiration to get the payload
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid token structure for refresh.")

    now = datetime.now(timezone.utc)
    # Check if issuer is present
    iss = payload.get("iss")
    if not iss:
        raise HTTPException(status_code=400, detail="Token missing issuer claim.")

    new_payload = {
        **payload,
        "iat": now.timestamp(),
        "nbf": now.timestamp(),
        "exp": (now + timedelta(minutes=token_expiry_minutes)).timestamp(),
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(new_payload, private_key_pem, algorithm="RS256")

# --- Rate Limiting Helper (Redis Pipeline based) ---
def check_rate_limit(redis_client, key: str, limit: int, window: int) -> bool:
    """
    Standardized helper to check rate limits via a Redis pipeline.
    Returns True if allowed, False if blocked.
    """
    if redis_client is None:
        return True # Fail open if Redis is unavailable
    try:
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        request_count, _ = pipe.execute()
        return request_count <= limit
    except Exception:
        return True # Fail open on unexpected exceptions
