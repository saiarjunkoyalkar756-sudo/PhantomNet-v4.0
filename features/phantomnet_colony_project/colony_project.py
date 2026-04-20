import logging
import uuid
import datetime
import json
from typing import Dict, List, Any

logger = logging.getLogger("phantom_colony")

class PhantomNetColony:
    """
    PhantomNet Colony Project:
    Implements a decentralized swarm intelligence backbone.
    When one agent (Edge Brain) learns a new anomaly, it propagates this 'Biological experience'
    to the rest of the Colony, ensuring the entire fabric evolves together.
    """

    def __init__(self, colony_name: str = "Root_Colony"):
        self.colony_id = f"COLONY_{uuid.uuid4().hex[:6]}"
        self.colony_name = colony_name
        self.agents: List[str] = []
        self.learned_experience: Dict[str, Any] = {}
        logger.info(f"Colony {self.colony_name} online. ID: {self.colony_id}")

    def register_agent(self, agent_id: str):
        if agent_id not in self.agents:
            self.agents.append(agent_id)
            logger.info(f"Agent {agent_id} joined the colony.")

    def propagate_learning(self, source_agent_id: str, insight_data: Dict[str, Any]):
        """
        Receives an insight from a single agent and shares it system-wide.
        """
        insight_id = hashlib.sha256(json.dumps(insight_data, sort_keys=True).encode()).hexdigest()[:10]
        
        self.learned_experience[insight_id] = {
            "source": source_agent_id,
            "data": insight_data,
            "timestamp": datetime.datetime.now().isoformat(),
            "propagation_count": len(self.agents)
        }
        
        logger.info(f"SWARM PROPAGATION: Insight {insight_id} broadcasted to {len(self.agents)} nodes.")
        # In a real environment, this triggers a Kafka publish to the 'colony-intelligence' topic
        return insight_id

    def get_collective_knowledge(self) -> Dict[str, Any]:
        return self.learned_experience

import hashlib
