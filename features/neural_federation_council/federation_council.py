import logging
import uuid
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("federation_council")

class NeuralFederationCouncil:
    """
    Neural Federation Council:
    Implements multi-agent consensus for high-impact security decisions.
    Prevents "rogue AI" behavior by requiring a quorum of authorized agents to sign off 
    on disruptive actions (like network-wide isolation or database wipes).
    """

    def __init__(self, quorum_size: int = 3, timeout_seconds: int = 30):
        self.quorum_size = quorum_size
        self.timeout_seconds = timeout_seconds
        self.active_proposals: Dict[str, Dict[str, Any]] = {}
        logger.info(f"Neural Federation Council established. Quorum threshold: {quorum_size} agents.")

    def submit_proposal(self, agent_id: str, action: str, details: Dict[str, Any]) -> str:
        """
        An agent submits a disruptive action proposal to the council.
        """
        proposal_id = str(uuid.uuid4())[:8]
        self.active_proposals[proposal_id] = {
            "proposer": agent_id,
            "action": action,
            "details": details,
            "votes": {agent_id: True}, # Auto-vote yes from proposer
            "timestamp": time.time(),
            "status": "pending",
            "votes_needed": self.quorum_size
        }
        logger.info(f"Proposal {proposal_id} submitted by {agent_id}: {action}")
        return proposal_id

    def cast_vote(self, proposal_id: str, agent_id: str, approve: bool = True) -> Dict[str, Any]:
        """
        Agents cast their votes on a pending proposal.
        """
        if proposal_id not in self.active_proposals:
            return {"status": "error", "message": "Proposal not found or expired."}

        proposal = self.active_proposals[proposal_id]
        
        # Check for timeout
        if time.time() - proposal["timestamp"] > self.timeout_seconds:
            proposal["status"] = "expired"
            logger.warning(f"Proposal {proposal_id} EXPIRED due to consensus timeout.")
            return {"status": "expired"}

        if proposal["status"] != "pending":
            return {"status": proposal["status"]}

        # Register vote
        proposal["votes"][agent_id] = approve
        vote_count = sum(1 for v in proposal["votes"].values() if v is True)
        
        logger.info(f"Agent {agent_id} voted {'YES' if approve else 'NO'} on {proposal_id}. Current Quorum: {vote_count}/{self.quorum_size}")

        # Check for consensus
        if vote_count >= self.quorum_size:
            proposal["status"] = "consensus_reached"
            logger.info(f"CONSENSUS REACHED for Proposal {proposal_id}: Executing {proposal['action']}")
            return {"status": "consensus_reached", "action": proposal["action"]}
        
        # Check for total rejection
        no_votes = sum(1 for v in proposal["votes"].values() if v is False)
        if no_votes > (self.quorum_size / 2):
            proposal["status"] = "rejected"
            logger.warning(f"Proposal {proposal_id} REJECTED by Federation Council.")
            return {"status": "rejected"}

        return {"status": "pending", "current_votes": vote_count}

    def get_council_status(self) -> Dict[str, Any]:
        return {
            "active_count": len([p for p in self.active_proposals.values() if p["status"] == "pending"]),
            "quorum_threshold": self.quorum_size,
            "proposals": self.active_proposals
        }

if __name__ == "__main__":
    council = NeuralFederationCouncil(quorum_size=2)
    p_id = council.submit_proposal("agent-001", "ISOLATE_DATA_CENTER", {"target": "DC-NORTH"})
    result = council.cast_vote(p_id, "agent-002", True)
    print(f"Final Decision: {result['status']}")
