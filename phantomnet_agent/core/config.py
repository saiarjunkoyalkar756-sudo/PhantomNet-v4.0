# core/config.py
import yaml
import os
import logging
from pydantic import ValidationError

from schemas.config_schema import PhantomNetAgentConfig

logger = logging.getLogger(__name__)

def load_config(config_path: str = "config/agent.example.yml") -> PhantomNetAgentConfig | None:
    """
    Loads and validates configuration from a YAML file using Pydantic models.
    Applies overrides from environment variables.
    """
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found at {config_path}")
        return None
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Apply environment variable overrides
        agent_config = config_data.get('agent', {})
        
        if os.getenv("PHANTOMNET_PLATFORM_OVERRIDE"):
            agent_config['platform_override'] = os.getenv("PHANTOMNET_PLATFORM_OVERRIDE")
            logger.info(f"Config override: platform_override = {agent_config['platform_override']}")
        
        if os.getenv("PHANTOMNET_ENABLE_EBPF"):
            agent_config['enable_ebpf'] = os.getenv("PHANTOMNET_ENABLE_EBPF").lower() == 'true'
            logger.info(f"Config override: enable_ebpf = {agent_config['enable_ebpf']}")

        if os.getenv("PHANTOMNET_ENABLE_PCAP"):
            agent_config['enable_pcap'] = os.getenv("PHANTOMNET_ENABLE_PCAP").lower() == 'true'
            logger.info(f"Config override: enable_pcap = {agent_config['enable_pcap']}")

        if os.getenv("PHANTOMNET_FORCE_ADMIN_WARN"):
            agent_config['force_admin_warn'] = os.getenv("PHANTOMNET_FORCE_ADMIN_WARN").lower() == 'true'
            logger.info(f"Config override: force_admin_warn = {agent_config['force_admin_warn']}")

        if os.getenv("PHANTOMNET_SAFE_MODE"):
            agent_config['safe_mode'] = os.getenv("PHANTOMNET_SAFE_MODE").lower() == 'true'
            logger.info(f"Config override: safe_mode = {agent_config['safe_mode']}")
        
        config_data['agent'] = agent_config # Update the agent section
        
        config = PhantomNetAgentConfig(**config_data)
        logger.info(f"Configuration loaded and validated from {config_path}")
        return config
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration from {config_path}: {e}")
        return None
    except ValidationError as e:
        logger.error(f"Configuration validation error: {e}")
        return None

if __name__ == '__main__':
    # Example usage:
    # Assuming agent.example.yml is in config/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    example_config_path = os.path.join(project_root, "config", "agent.example.yml")
    
    config = load_config(example_config_path)
    if config:
        print("Configuration loaded successfully:")
        print(config.model_dump_json(indent=2))
    else:
        print("Failed to load configuration.")
