# backend_api/zero_trust_engine.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import random
import time
import uuid

# --- Data Models for Zero-Trust Operations ---
class Identity(BaseModel):
    id: str = Field(..., description="Unique ID for the entity (user, device, service)")
    type: str = Field(..., description="Type of identity ('user', 'device', 'service')")
    attributes: Dict[str, Any] = Field({}, description="Attributes associated with the identity")

class AccessRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for the access request")
    identity: Identity = Field(..., description="The identity requesting access")
    resource: str = Field(..., description="The resource being accessed")
    action: str = Field(..., description="The action being performed on the resource (e.g., 'read', 'write', 'execute')")
    context: Dict[str, Any] = Field({}, description="Contextual information (e.g., 'source_ip', 'time_of_day', 'device_health')")

class TrustScore(BaseModel):
    entity_id: str = Field(..., description="ID of the entity (user, device, service)")
    score: float = Field(..., ge=0, le=100, description="Calculated trust score (0-100)")
    factors: Dict[str, Any] = Field({}, description="Factors influencing the trust score")
    last_evaluated: float = Field(default_factory=time.time, description="Timestamp of the last trust score evaluation")

class ZeroTrustPolicy(BaseModel):
    policy_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for the policy")
    name: str = Field(..., description="Name of the policy")
    description: str = Field(..., description="Description of the policy")
    rules: List[str] = Field(..., description="List of policy rules (e.g., 'allow if user_trust_score > 80 and device_health = high')")
    enforcement_action: str = Field("deny", description="Action if policy is violated ('deny', 'alert', 'quarantine')")

class EnforcementAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for the enforcement action")
    access_request_id: str = Field(..., description="ID of the access request that triggered the action")
    policy_id: str = Field(..., description="ID of the violated policy")
    enforced_action: str = Field(..., description="The action taken (e.g., 'denied_access', 'isolated_device')")
    timestamp: float = Field(default_factory=time.time, description="Timestamp of the enforcement")
    details: Dict[str, Any] = Field({}, description="Additional details about the enforcement")


class ZeroTrustEngine:
    def __init__(self):
        self.policies: Dict[str, ZeroTrustPolicy] = {}
        self.current_trust_scores: Dict[str, TrustScore] = {}
        self.enforcement_logs: List[EnforcementAction] = []

        # Default policies
        self.add_policy(ZeroTrustPolicy(
            name="High-Privilege Access",
            description="Requires high trust score for sensitive resource access",
            rules=["user_trust_score > 90", "device_health = 'healthy'"],
            enforcement_action="deny"
        ))
        self.add_policy(ZeroTrustPolicy(
            name="Lateral Movement Prevention",
            description="Prevents lateral movement if device trust is low",
            rules=["device_trust_score < 50", "action = 'ssh_to_server'"],
            enforcement_action="quarantine_device"
        ))

    def add_policy(self, policy: ZeroTrustPolicy):
        """Adds a new Zero-Trust policy."""
        self.policies[policy.policy_id] = policy
        logger.info(f"[{__name__}] Added Zero-Trust policy: {policy.name} ({policy.policy_id})")

    def update_policy(self, policy_id: str, updated_policy: ZeroTrustPolicy) -> Optional[ZeroTrustPolicy]:
        """Updates an existing Zero-Trust policy."""
        if policy_id in self.policies:
            self.policies[policy_id] = updated_policy
            logger.info(f"[{__name__}] Updated Zero-Trust policy: {updated_policy.name} ({policy_id})")
            return updated_policy
        return None

    def delete_policy(self, policy_id: str) -> bool:
        """Deletes a Zero-Trust policy."""
        if policy_id in self.policies:
            del self.policies[policy_id]
            logger.info(f"[{__name__}] Deleted Zero-Trust policy: {policy_id}")
            return True
        return False

    def get_policy(self, policy_id: str) -> Optional[ZeroTrustPolicy]:
        """Retrieves a specific Zero-Trust policy."""
        return self.policies.get(policy_id)

    def get_all_policies(self) -> List[ZeroTrustPolicy]:
        """Retrieves all Zero-Trust policies."""
        return list(self.policies.values())

    async def _evaluate_trust_score(self, identity: Identity) -> TrustScore:
        """Simulates calculating a trust score for an identity."""
        time.sleep(random.uniform(0.5, 2)) # Simulate processing
        
        # Example factors for simulation
        login_history_score = random.uniform(50, 100)
        device_health_score = random.uniform(40, 95)
        geo_location_score = random.uniform(70, 100)

        # Simple aggregation
        score = (login_history_score + device_health_score + geo_location_score) / 3
        
        trust_factors = {
            "login_history": login_history_score,
            "device_health": device_health_score,
            "geo_location": geo_location_score
        }
        
        self.current_trust_scores[identity.id] = TrustScore(
            entity_id=identity.id,
            score=round(score, 2),
            factors=trust_factors
        )
        return self.current_trust_scores[identity.id]

    async def get_trust_score(self, entity_id: str) -> Optional[TrustScore]:
        """Retrieves the current trust score for an entity, re-evaluating if necessary."""
        # For simulation, always re-evaluate or use a cached one for a short period
        # In a real system, this would involve continuous evaluation or event-driven updates.
        identity = Identity(id=entity_id, type="user", attributes={"username": entity_id}) # Placeholder identity
        return await self._evaluate_trust_score(identity)

    async def evaluate_access_request(self, request: AccessRequest) -> EnforcementAction:
        """Evaluates an access request against defined policies."""
        logger.info(f"[{__name__}] Evaluating access request (ID: {request.request_id}) for {request.identity.id} accessing {request.resource}")
        
        trust_score_obj = await self.get_trust_score(request.identity.id)
        if not trust_score_obj:
            trust_score_obj = TrustScore(entity_id=request.identity.id, score=0, factors={"reason": "identity_unknown"})

        # Simulate context dynamically
        context = request.context
        context["user_trust_score"] = trust_score_obj.score
        context["device_health"] = random.choice(["healthy", "compromised", "unknown"]) # Simulated device health

        enforced_action = "allowed"
        violated_policy_id = None
        
        for policy in self.policies.values():
            policy_violated = False
            for rule in policy.rules:
                # This is a very simplistic rule evaluation. In reality, a proper rule engine is needed.
                # For demo, assumes rules are simple Python evaluable strings based on context.
                try:
                    # Replace context variables with their simulated values
                    eval_rule = rule
                    for key, value in context.items():
                        # Basic type handling for string comparison
                        if isinstance(value, str):
                            eval_rule = eval_rule.replace(key, f"'{value}'")
                        else:
                            eval_rule = eval_rule.replace(key, str(value))
                    
                    if not eval(eval_rule): # If rule is not met
                        policy_violated = True
                        break
                except Exception as e:
                    logger.error(f"Error evaluating policy rule '{rule}': {e}")
                    # In case of error, assume policy is violated to be safe
                    policy_violated = True
                    break
            
            if policy_violated:
                enforced_action = policy.enforcement_action
                violated_policy_id = policy.policy_id
                logger.warning(f"[{__name__}] Access request {request.request_id} violated policy {policy.name}. Action: {enforced_action}")
                break # Enforce first violated policy

        enforcement_log = EnforcementAction(
            access_request_id=request.request_id,
            policy_id=violated_policy_id if violated_policy_id else "N/A",
            enforced_action=enforced_action,
            details={"access_granted": enforced_action == "allowed", "trust_score_at_request": trust_score_obj.score}
        )
        self.enforcement_logs.append(enforcement_log)
        return enforcement_log

    def get_enforcement_logs(self) -> List[EnforcementAction]:
        """Retrieves all recorded enforcement actions."""
        return self.enforcement_logs

if __name__ == "__main__":
    engine = ZeroTrustEngine()

    async def test_zero_trust_engine():
        print("--- Adding new policy ---")
        new_policy = ZeroTrustPolicy(
            name="Restricted Resource Access",
            description="Only users with high trust score can access restricted resources from healthy devices.",
            rules=["user_trust_score > 70", "device_health = 'healthy'", "resource_path.startswith('/restricted')"],
            enforcement_action="deny"
        )
        engine.add_policy(new_policy)
        print(f"Added policy: {new_policy.policy_id}")

        print("\n--- Evaluating Access Request (Allowed) ---")
        identity_user = Identity(id="user123", type="user", attributes={"username": "alice"})
        access_req_allowed = AccessRequest(
            identity=identity_user,
            resource="/public/report.pdf",
            action="read",
            context={"source_ip": "192.168.1.10"}
        )
        enforcement_allowed = await engine.evaluate_access_request(access_req_allowed)
        print(json.dumps(enforcement_allowed.dict(), indent=2))

        print("\n--- Evaluating Access Request (Denied by New Policy) ---")
        access_req_denied = AccessRequest(
            identity=identity_user,
            resource="/restricted/financials.xlsx",
            action="read",
            context={"source_ip": "10.0.0.5", "device_health": "compromised"}
        )
        enforcement_denied = await engine.evaluate_access_request(access_req_denied)
        print(json.dumps(enforcement_denied.dict(), indent=2))

        print("\n--- Retrieving Trust Score for user123 ---")
        trust_score = await engine.get_trust_score("user123")
        print(json.dumps(trust_score.dict(), indent=2)) if trust_score else "Trust score not found."

        print("\n--- Retrieving All Policies ---")
        all_policies = engine.get_all_policies()
        print(json.dumps([p.dict() for p in all_policies], indent=2))

        print("\n--- Retrieving Enforcement Logs ---")
        all_logs = engine.get_enforcement_logs()
        print(json.dumps([l.dict() for l in all_logs], indent=2))

    asyncio.run(test_zero_trust_engine())
