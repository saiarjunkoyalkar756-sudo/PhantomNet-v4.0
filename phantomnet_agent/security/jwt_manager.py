import jwt
import asyncio # Keep for possible future async operations or background tasks if re-introduced
import logging
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa # Keep rsa for public_key() from private_key
from cryptography.hazmat.backends import default_backend
from typing import Dict, Any, Optional, List

from utils.logger import get_logger # Use the structured logger

class JWTManager:
    """
    Manages JWT issuing for agent authentication with the backend.
    Takes agent's private and public keys (PEM encoded) directly for signing and verification.
    Supports single signing key and conceptual rotation through external key management.
    """
    def __init__(self, private_key_pem: str, public_key_pem: str, agent_id: str, 
                 algorithm: str = "RS256", token_expiry_minutes: int = 15):
        self.logger = get_logger("phantomnet_agent.jwt_manager")
        self.agent_id = agent_id
        self.algorithm = algorithm
        self.token_expiry_minutes = token_expiry_minutes

        try:
            self.private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
            self.public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=default_backend()
            )
            # Store public key in a dict for potential future rotation/multiple key verification
            self.public_keys_for_verification: Dict[str, Any] = {
                self._get_key_id(self.public_key): self.public_key
            }
            self.current_signing_kid = self._get_key_id(self.private_key.public_key())

            self.logger.info(f"JWTManager initialized for agent {self.agent_id} with key KID: {self.current_signing_kid}")
        except Exception as e:
            self.logger.critical(f"Failed to initialize JWTManager: {e}. Check private/public key PEM data.", exc_info=True)
            raise

    def _get_key_id(self, key) -> str:
        """Generates a simple key ID from the public key for 'kid' header."""
        # In a production system, this would be a cryptographic hash or a managed ID.
        # For simplicity, we use a short hash of the public key's fingerprint.
        fingerprint = key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return str(abs(hash(fingerprint)))[:8] # Short hash as KID

    def get_token(self, payload: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates a signed JWT for agent authentication.
        """
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.token_expiry_minutes)

        jwt_payload = {
            "iss": self.agent_id,
            "sub": self.agent_id, # Subject is the agent itself
            "aud": "phantomnet_manager", # Audience is the manager
            "exp": expires.timestamp(),
            "nbf": now.timestamp(),
            "iat": now.timestamp(),
            **(payload or {}) # Add custom payload data if provided
        }

        headers = {
            "kid": self.current_signing_kid,
            "alg": self.algorithm
        }

        encoded_jwt = jwt.encode(
            jwt_payload,
            self.private_key,
            algorithm=self.algorithm,
            headers=headers
        )
        self.logger.debug(f"Generated JWT for agent {self.agent_id}.", extra={"kid": self.current_signing_kid, "expires_at": expires.isoformat()})
        return encoded_jwt

    def verify_jwt(self, token: str, accepted_public_keys: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Verifies a JWT using known public keys and returns the decoded payload.
        If accepted_public_keys is provided, it uses those for verification; otherwise,
        it uses the public keys known to this JWTManager instance.
        """
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")
        algorithm = headers.get("alg", self.algorithm)

        keys_to_try = accepted_public_keys if accepted_public_keys is not None else self.public_keys_for_verification

        if kid and kid in keys_to_try:
            try:
                decoded_payload = jwt.decode(
                    token,
                    keys_to_try[kid],
                    algorithms=[algorithm],
                    audience="phantomnet_manager"
                )
                return decoded_payload
            except jwt.ExpiredSignatureError:
                self.logger.warning(f"JWT with KID {kid} has expired.", extra={"kid": kid})
            except jwt.InvalidTokenError as e:
                self.logger.error(f"Invalid JWT with KID {kid}: {e}", extra={"kid": kid, "error": str(e)})
        else:
            self.logger.warning(f"JWT has unknown or missing KID: {kid}. Attempting with all provided public keys (less efficient).", extra={"kid": kid, "known_kids": list(keys_to_try.keys())})
            # Fallback: try all known public keys if KID is unknown or not current
            for pk_kid, public_key_obj in keys_to_try.items():
                try:
                    decoded_payload = jwt.decode(
                        token,
                        public_key_obj,
                        algorithms=[algorithm],
                        audience="phantomnet_manager"
                    )
                    self.logger.info(f"JWT successfully verified with fallback key KID: {pk_kid}", extra={"kid": pk_kid})
                    return decoded_payload
                except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                    continue
        
        self.logger.error("JWT verification failed: No valid key found or invalid token.")
        return None