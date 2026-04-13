# actions/base.py
from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Optional, Union

from schemas.actions import AgentAction # Keep for type hinting for individual actions if needed
from schemas.config_schema import PhantomNetAgentConfig # Keep for config access
from bus.base import Transport # Keep for transport access
from phantomnet_agent.platform_compatibility.linux_adapter import LinuxAdapter
from phantomnet_agent.platform_compatibility.windows_adapter import WindowsAdapter
from phantomnet_agent.platform_compatibility.termux_adapter import TermuxAdapter

class Action(ABC):
    """
    Abstract base class for all agent actions.
    Actions are operations that the agent can perform on the system.
    """
    def __init__(self, logger: logging.Logger, transport: Optional[Transport] = None, config: Optional[PhantomNetAgentConfig] = None, adapter: Optional[Union[LinuxAdapter, WindowsAdapter, TermuxAdapter]] = None):
        self.logger = logger
        self.transport = transport
        self.config = config
        self.adapter = adapter

    # The abstract 'execute' method is removed as AgentExecutor will call specific methods
    # like ping_host, execute_os_command, etc., directly.
    # Subclasses will implement these specific action methods.
