import pytest
import time
import hashlib
import json
import datetime
from shared.database import Base, Block, test_engine, get_db
from iam_service.auth_methods import get_current_user, UserRole
from unittest.mock import patch, MagicMock

# Helper function to create a mock user object for get_current_user override
def create_mock_user(user_data, user_id=1):
    mock_user = MagicMock()
    mock_user.username = user_data["username"]
    mock_user.id = user_id
    mock_user.role = user_data["role"]
    mock_user.hashed_password = "mocked_hashed_password_string"
    mock_user.email = "test@example.com"
    mock_user.disabled = False
    mock_user.totp_secret = None
    mock_user.twofa_enforced = False
    return mock_user


# Mock DUMMY_SYSTEM_FILE for Orchestrator initialization
DUMMY_SYSTEM_FILE = "dummy_system_state.txt" 
@pytest.fixture(autouse=True)
def mock_orchestrator_dependencies(monkeypatch):
    """Mocks external dependencies for the Orchestrator to run in isolation."""
    # Mock the Orchestrator's internal dependencies if needed
    mock_orchestrator_instance = MagicMock()
    mock_orchestrator_instance.cognitive_core.analyze_threat.return_value = {
        "label": "medium", # Changed from "NORMAL" to match expected threat_level
        "score": 0.5,
        "explanation": "Mocked explanation.",
        "threat_level": "medium",  # This should be a top-level key
        "threat_data_received": "suspicious_activity",
        "neural_analysis": {"label": "medium", "explanation": "mocked neural explanation"},
    }
    mock_orchestrator_instance.handle_threat.return_value = MagicMock()
    # Mock PhantomChain explicitly
    mock_phantom_chain_instance = MagicMock()
    mock_phantom_chain_instance.chain = [ # Set chain attribute directly to a list with a mock genesis block
        {
            "index": 1,
            "timestamp": datetime.datetime.fromtimestamp(time.time()).isoformat(),
            "transactions": [],
            "proof": 100,
            "previous_hash": "1",
            "block_hash": "mock_genesis_hash_123", # Mock a hash
            "merkle_root": None,
        }
    ]
    mock_orchestrator_instance.phantom_chain = mock_phantom_chain_instance # Assign the mocked phantom_chain to the orchestrator instance
    monkeypatch.setattr("phantomnet_agent.orchestrator.PhantomChain", MagicMock(return_value=mock_phantom_chain_instance))
    
    # Directly mock the get_orchestrator dependency
    monkeypatch.setattr("backend_api.orchestrator_api.get_orchestrator", lambda db_session=None: mock_orchestrator_instance)
    monkeypatch.setattr("phantomnet_agent.orchestrator.Orchestrator", MagicMock(return_value=mock_orchestrator_instance))
    monkeypatch.setattr("backend_api.orchestrator_api.DUMMY_SYSTEM_FILE", DUMMY_SYSTEM_FILE)


def test_handle_threat_endpoint(client):
    print("\n--- Testing /orchestrator/threats/ endpoint ---")
    response = client.post(
        "/orchestrator/threats/", json={"threat_string": "suspicious_activity"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Threat analyzed."
    assert data["analysis"]["threat_level"] == "SIMULATED"


def test_get_blockchain_endpoint(client):
    print("\n--- Testing /orchestrator/blockchain/ endpoint ---")
    
    # Setup mock user for authorization
    mock_user_data = {"username": "testviewer", "password": "securepassword", "role": "viewer"}
    mock_viewer_obj = create_mock_user(mock_user_data)
    client.app.dependency_overrides[get_current_user] = lambda: mock_viewer_obj

    db = next(client.app.dependency_overrides[get_db]())
    # Ensure genesis block exists for this test
    if db.query(Block).count() == 0:
        genesis_block_data = {
            "index": 1,
            "timestamp": time.time(),
            "transactions": [],
            "proof": 100,
            "previous_hash": "1",
        }
        genesis_block_hash = hashlib.sha256(
            json.dumps(genesis_block_data, sort_keys=True).encode()
        ).hexdigest()

        genesis_block = Block(
            index=genesis_block_data["index"],
            timestamp=datetime.datetime.fromtimestamp(
                genesis_block_data["timestamp"]
            ),
            proof=genesis_block_data["proof"],
            previous_hash=genesis_block_data["previous_hash"],
            block_hash=genesis_block_hash,
            merkle_root=None,
        )
        db.add(genesis_block)
        db.commit()
    db.close()

    response = client.get(
        "/orchestrator/blockchain/",
        headers={"Authorization": "Bearer dummy_viewer_token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "chain" in data
    assert isinstance(data["chain"], list)
    assert len(data["chain"]) >= 1
    # Check that genesis block is present
    assert data["chain"][0]["index"] == 1

    # Clean up dependency override
    client.app.dependency_overrides.pop(get_current_user, None)
