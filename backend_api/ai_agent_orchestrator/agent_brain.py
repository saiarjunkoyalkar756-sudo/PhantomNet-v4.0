# backend_api/ai_agent_orchestrator/agent_brain.py

import logging
import json
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend_api.shared.logger_config import logger
from backend_api.shared.consensus_engine import ConsensusEngine

class AgentBrain:
    """
    The reasoning core for PhantomNet AI Agents.
    Implements a ReAct (Reasoning + Acting) loop to solve security tasks.
    Integrated with Federation Council Consensus for high-impact actions.
    """

    def __init__(self):
        self.logger = logger
        self.active_agents = {}
        self.consensus_engine = ConsensusEngine(quorum_threshold=0.66)
        self.logger.info("AgentBrain: Reasoning engine and Consensus Council online.")

    async def reason_and_plan(self, task: str, persona: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        The main ReAct loop:
        1. THOUGHT: What is the task and what do I know?
        2. ACTION: What tool should I use to get more info?
        3. OBSERVATION: What did the tool return?
        4. REPEAT or FINAL ANSWER.
        """
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        reasoning_steps = []
        proposed_actions = []

        # Step 1: Initial Thought
        thought_1 = f"Persona[{persona}]: I have received a task to '{task}'. First, I need to assess the current asset context."
        reasoning_steps.append(thought_1)
        self.logger.info(f"Agent[{task_id}]: {thought_1}")

        # Step 2: Simulated Action (Querying Asset Inventory)
        action_1 = {"tool": "AssetInventory", "action": "get_asset_details", "params": {"query": task}}
        # Simulate tool observation
        observation_1 = "Asset 'DB_SERVER_01' identified with high vulnerability score (CVE-2024-XXXX)."
        reasoning_steps.append(f"Observation: {observation_1}")

        # Step 3: Second Thought
        thought_2 = f"Based on the observation of critical vulnerabilities on DB_SERVER_01, I must check if there is an active exploit pattern in the logs."
        reasoning_steps.append(thought_2)

        # Step 4: Simulated Action (PNQL Query)
        action_2 = {"tool": "PNQL_Engine", "action": "query_logs", "params": {"query": "SELECT * FROM logs WHERE asset='DB_SERVER_01' AND severity='high'"}}
        observation_2 = "Detected lateral movement attempt from 10.0.0.5 to DB_SERVER_01."
        reasoning_steps.append(f"Observation: {observation_2}")

        # Step 5: Final Thought & Proposed Remediation
        thought_final = f"I have confirmed an active lateral movement threat targeting a vulnerable database. I will initiate a Federation Council consensus vote for isolation."
        reasoning_steps.append(thought_final)

        # TRIGGER PHASE 3: CONSENSUS VOTE
        proposed_action = "trigger_soar_playbook:isolate_vulnerable_host"
        await self.consensus_engine.initiate_vote(task_id, proposed_action, agent_count=3)
        
        # Simulate other agents voting
        await self.consensus_engine.cast_vote(task_id, "agent_ghost", True, "Corroborated: Found matching forensic artifacts in memory.")
        await self.consensus_engine.cast_vote(task_id, "agent_recon", True, "Corroborated: Lateral path is viable and asset is critical.")
        await self.consensus_engine.cast_vote(task_id, persona, True, "Primary Agent: Active exploit detected in logs.")
        
        consensus_result = await self.consensus_engine.check_consensus(task_id)
        reasoning_steps.append(f"Consensus Result: {consensus_result['status'].upper()} (Approvals: {consensus_result['approval_ratio']*100}%)")

        if consensus_result["status"] == "approved":
            proposed_actions.append({
                "action": "trigger_soar_playbook",
                "playbook_name": "isolate_vulnerable_host",
                "parameters": {"host_id": "DB_SERVER_01", "reason": "Confirmed lateral movement. Consensus reached via Federation Council."}
            })
        else:
            reasoning_steps.append("Action blocked: Quorum not reached.")

        return {
            "task_id": task_id,
            "status": "plan_generated" if consensus_result["status"] == "approved" else "consensus_failed",
            "reasoning_steps": reasoning_steps,
            "proposed_actions": proposed_actions,
            "timestamp": datetime.now().isoformat()
        }

    async def execute_plan(self, task_id: str, plan: Dict[str, Any]):
        """
        Executes the proposed actions by calling relevant microservices.
        """
        self.logger.info(f"AgentBrain: Executing plan for {task_id}")
        for action in plan.get("proposed_actions", []):
            self.logger.info(f"AgentBrain: Triggering {action['action']} - {action['playbook_name']}")
            # Implementation would call SOAR Engine API here
        return True
