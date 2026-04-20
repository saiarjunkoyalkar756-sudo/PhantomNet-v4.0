# backend_api/security/zero_trust_manager.py

from fastapi import Request, HTTPException
from typing import Optional, Dict, Any
from shared.logger_config import logger
from shared.zero_trust_engine import ZeroTrustEngine, Identity, AccessRequest

class IntegratedZeroTrustManager:
    """
    Enforces Zero-Trust security principles for all incoming requests,
    utilizing the core ZeroTrustEngine.
    """

    def __init__(self):
        self.engine = ZeroTrustEngine()
        logger.info("IntegratedZeroTrustManager initialized with core engine.")

    async def verify_request(self, request: Request) -> Dict[str, Any]:
        """
        Verifies a request based on identity, device posture, and other signals.
        """
        # 1. Verify mTLS connection (Signal 1)
        client_cert = request.headers.get("X-Client-Cert-Fingerprint")
        if not client_cert:
            logger.warning("ZeroTrust: Missing mTLS fingerprint.")
            # In production, this might be a hard fail. For audit, we'll mark as low-trust.
        
        # 2. Evaluate Identity (Signal 2)
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.error("ZeroTrust: Missing or invalid Authorization header.")
            raise HTTPException(status_code=401, detail="Authentication required")
        
        token = auth_header.split(" ")[1]
        # Real JWT validation happens in IAM service, but we'll simulate the identity extraction here
        # In a real grid, this service would call the IAM verifier or check a local JTI cache.
        identity_id = "user_placeholder" # Extracted from token
        
        # 3. Build Access Request
        access_req = AccessRequest(
            identity=Identity(id=identity_id, type="user"),
            resource=str(request.url.path),
            action=request.method,
            context={
                "source_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "device_health": request.headers.get("X-Device-Health", "unknown"),
                "mtls_verified": client_cert is not None
            }
        )

        # 4. Evaluate through Engine
        enforcement = await self.engine.evaluate_access_request(access_req)
        
        if enforcement.enforced_action != "allowed":
            logger.critical(f"ZeroTrust: Access DENIED for {identity_id}. Reason: {enforcement.enforced_action}")
            raise HTTPException(
                status_code=403, 
                detail=f"Zero-Trust Policy Violation: {enforcement.enforced_action}"
            )

        logger.info(f"ZeroTrust: Access GRANTED for {identity_id}. Score: {enforcement.details.get('trust_score_at_request')}")
        return {"user_id": identity_id, "trust_score": enforcement.details.get("trust_score_at_request")}

# Export as zero_trust_manager for compatibility
zero_trust_manager = IntegratedZeroTrustManager()
