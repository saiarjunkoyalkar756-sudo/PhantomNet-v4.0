import sys
import pytest
from unittest.mock import patch

def reset_all_agent_states():
    # Reset _agent_state in all loaded variations of core.state module
    for name, module in list(sys.modules.items()):
        if name == "core.state" or name == "phantomnet_agent.core.state" or name.endswith(".core.state"):
            if hasattr(module, "_agent_state"):
                module._agent_state = None

@pytest.fixture(autouse=True)
def reset_agent_state_fixture():
    reset_all_agent_states()
    yield
    reset_all_agent_states()
