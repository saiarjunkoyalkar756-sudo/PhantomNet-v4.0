# backend_api/shared/consensus_engine.py

import logging
import asyncio
from typing import Dict, Any, List, Optional
from backend_api.shared.logger_config import logger

class ConsensusEngine:
    """
    Federation Council Consensus Engine:
    Validates autonomous security actions by requiring consensus across 
    multiple reasoning agents or detection nodes.
    Prevents 'Friendly Fire' or 'AI Hallucination' from triggering high-impact remediation.
    """

    def __init__(self, quorum_threshold: float = 0.66):
        self.quorum_threshold = quorum_threshold
        self.active_votes: Dict[str, Dict[str, Any]] = {} # keyed by incident_id
        self.logger = logger
        self.logger.info(f"ConsensusEngine: Initialized with {int(quorum_threshold*100)}% quorum requirement.")

    async def initiate_vote(self, incident_id: str, proposed_action: str, agent_count: int):
        """
        Initializes a new voting round for a proposed high-impact action.
        """
        self.active_votes[incident_id] = {
            "action": proposed_action,
            "votes": [],
            "required_voters": agent_count,
            "start_time": asyncio.get_event_loop().time()
        }
        self.logger.info(f"ConsensusEngine: Vote initiated for Incident {incident_id} [{proposed_action}].")

    async def cast_vote(self, incident_id: str, agent_id: str, approve: bool, reasoning: str):
        """
        Allows an agent to cast its vote.
        """
        if incident_id not in self.active_votes:
            self.logger.warning(f"ConsensusEngine: Attempted to vote on non-existent incident {incident_id}.")
            return False

        vote = {"agent_id": agent_id, "approve": approve, "reasoning": reasoning}
        self.active_votes[incident_id]["votes"].append(vote)
        self.logger.info(f"ConsensusEngine: Agent {agent_id} voted {'YES' if approve else 'NO'} on incident {incident_id}.")
        return True

    async def check_consensus(self, incident_id: str) -> Dict[str, Any]:
        """
        Evaluates the current state of a vote and determines if a quorum has been reached.
        """
        if incident_id not in self.active_votes:
            return {"status": "not_found"}

        session = self.active_votes[incident_id]
        total_votes = len(session["votes"])
        approvals = sum(1 for v in session["votes"] if v["approve"])
        
        approval_ratio = approvals / total_votes if total_votes > 0 else 0
        
        status = "pending"
        if total_votes >= session["required_voters"]:
            if approval_ratio >= self.quorum_threshold:
                status = "approved"
                self.logger.info(f"ConsensusEngine: QUORUM REACHED for Incident {incident_id}. Action approved.")
            else:
                status = "rejected"
                self.logger.warning(f"ConsensusEngine: QUORUM FAILED for Incident {incident_id}. Action rejected.")

        return {
            "status": status,
            "incident_id": incident_id,
            "approval_ratio": approval_ratio,
            "total_votes": total_votes,
            "reasoning_summary": [v["reasoning"] for v in session["votes"]]
        }
