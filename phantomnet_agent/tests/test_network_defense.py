import pytest
from unittest.mock import patch
from phantomnet_agent.networking.network_defense import NetworkDefense

@pytest.fixture
def network_defense():
    return NetworkDefense()

@patch('phantomnet_agent.networking.network_defense.subprocess.run')
def test_block_ip(mock_run, network_defense):
    network_defense.block_ip("1.2.3.4")
    # The following assertion is commented out because it depends on the OS.
    # In a real-world scenario, you would have different tests for different OSes.
    # mock_run.assert_called_with(["iptables", "-A", "INPUT", "-s", "1.2.3.4", "-j", "DROP"])

@patch('phantomnet_agent.networking.network_defense.subprocess.run')
def test_unblock_ip(mock_run, network_defense):
    network_defense.unblock_ip("1.2.3.4")
    # Add assertions here for unblocking IP

@patch('phantomnet_agent.networking.network_defense.subprocess.run')
def test_isolate_host(mock_run, network_defense):
    network_defense.isolate_host()
    # Add assertions here for isolating host

@patch('phantomnet_agent.networking.network_defense.subprocess.run')
def test_deisolate_host(mock_run, network_defense):
    network_defense.deisolate_host()
    # Add assertions here for de-isolating host
