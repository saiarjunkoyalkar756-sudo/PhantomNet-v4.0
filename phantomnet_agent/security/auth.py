# security/auth.py
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AgentAuthenticator:
    """
    Manages agent identity and handles authentication/authorization logic.
    """
    def __init__(self, agent_id: str, secret_key: Optional[str] = None):
        self.agent_id = agent_id
        self.secret_key = secret_key # In a real system, this would be more complex (e.g., loaded securely)
        self.is_authenticated = False
        self.auth_token: Optional[str] = None # Placeholder for JWT or similar token

    async def authenticate_with_backend(self) -> bool:
        """
        Simulates authentication with a backend service.
        In a real scenario, this would involve sending credentials (e.g., client certificate, API key)
        and receiving a JWT or session token.
        """
        logger.info(f"Agent '{self.agent_id}' attempting to authenticate with backend...")
        await asyncio.sleep(0.5) # Simulate network delay

        if self.secret_key: # Simple check for a 'secret'
            # In a real system:
            # 1. Generate client certificate or sign a challenge
            # 2. Send to backend with agent_id
            # 3. Receive and validate JWT/token
            self.auth_token = f"dummy_jwt_for_{self.agent_id}_and_secret"
            self.is_authenticated = True
            logger.info(f"Agent '{self.agent_id}' authenticated successfully.")
        else:
            self.is_authenticated = False
            logger.warning(f"Agent '{self.agent_id}' failed to authenticate (no secret key provided).")
        
        return self.is_authenticated

    def get_auth_headers(self) -> Dict[str, str]:
        """Returns authentication headers to be used in outgoing requests."""
        if self.is_authenticated and self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    def authorize_action(self, action_type: str, required_permissions: List[str]) -> bool:
        """
        Checks if the agent is authorized to perform a specific action.
        This is a client-side check; the backend should also perform server-side authorization.
        """
        # In a real system, this would parse the JWT for scopes/permissions
        # For now, it's a simple check against a hardcoded list or a config value.
        agent_permissions = ["process:kill", "network:block", "system:isolate"] # Example allowed permissions
        for perm in required_permissions:
            if perm not in agent_permissions:
                logger.warning(f"Agent '{self.agent_id}' is not authorized for permission: {perm}")
                return False
        logger.debug(f"Agent '{self.agent_id}' authorized for action: {action_type}")
        return True

    def verify_api_key(self, api_key: str) -> bool:
        """
        Verifies an API key for local API access.
        This is a simple comparison; for production, use secure token storage and comparison.
        """
        # This API key would typically be stored in a secure config and not hardcoded.
        expected_api_key = os.environ.get("PHANTOMNET_AGENT_API_KEY", "super_secret_api_key")
        if hmac.compare_digest(api_key.encode('utf-8'), expected_api_key.encode('utf-8')):
            logger.debug("API key verified.")
            return True
        logger.warning("Invalid API key provided.")
        return False

if __name__ == '__main__':
    import asyncio
    import os

    logging.basicConfig(level=logging.DEBUG)

    # --- Test Case 1: Successful authentication ---
    print("--- Test: Successful Authentication ---")
    auth1 = AgentAuthenticator(agent_id="agent-001", secret_key="my_secret")
    asyncio.run(auth1.authenticate_with_backend())
    print(f"Agent 001 authenticated: {auth1.is_authenticated}, Token: {auth1.auth_token}")
    print(f"Auth Headers: {auth1.get_auth_headers()}")
    assert auth1.is_authenticated

    # --- Test Case 2: Failed authentication (no secret) ---
    print("\n--- Test: Failed Authentication (no secret) ---")
    auth2 = AgentAuthenticator(agent_id="agent-002")
    asyncio.run(auth2.authenticate_with_backend())
    print(f"Agent 002 authenticated: {auth2.is_authenticated}")
    assert not auth2.is_authenticated

    # --- Test Case 3: Authorization check ---
    print("\n--- Test: Authorization ---")
    is_authorized_kill = auth1.authorize_action("process_kill", ["process:kill"])
    print(f"Agent 001 authorized for process:kill (expected True): {is_authorized_kill}")
    assert is_authorized_kill

    is_authorized_unallowed = auth1.authorize_action("system_reboot", ["system:reboot"])
    print(f"Agent 001 authorized for system:reboot (expected False): {is_authorized_unallowed}")
    assert not is_authorized_unallowed

    # --- Test Case 4: API Key Verification ---
    print("\n--- Test: API Key Verification ---")
    os.environ["PHANTOMNET_AGENT_API_KEY"] = "my_api_key_123"
    auth_api = AgentAuthenticator(agent_id="api_verifier")
    
    valid_key = "my_api_key_123"
    invalid_key = "wrong_api_key"

    print(f"Verifying valid API key '{valid_key}': {auth_api.verify_api_key(valid_key)}")
    assert auth_api.verify_api_key(valid_key)

    print(f"Verifying invalid API key '{invalid_key}': {auth_api.verify_api_key(invalid_key)}")
    assert not auth_api.verify_api_key(invalid_key)

    del os.environ["PHANTOMNET_AGENT_API_KEY"]
