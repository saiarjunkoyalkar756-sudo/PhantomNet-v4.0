import pytest
from shared.database import get_db
from shared.database import create_db_and_tables, User, Base, test_engine, TestingSessionLocal
from iam_service.auth_methods import get_password_hash, create_access_token
import datetime
from unittest.mock import MagicMock
from iam_service.auth_methods import get_current_user, UserRole


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


@pytest.fixture(autouse=True)
def mock_password_hash_fixture(monkeypatch):
    # This fixture mocks get_password_hash to always return a short, consistent hash
    # It has autouse=True to apply globally, but we'll also directly set hashed_password
    # in setup fixtures for explicit control.
    def mock_get_password_hash(password):
        return "mocked_hashed_password_string"
    monkeypatch.setattr("iam_service.auth_methods.get_password_hash", mock_get_password_hash)

@pytest.fixture(autouse=True)
def mock_verify_password(monkeypatch):
    # Mock verify_password to bypass passlib for login tests
    def mock_verify_password_func(plain_password, hashed_password):
        # Simulate successful verification for known test passwords
        if plain_password == "shortpassword" and hashed_password == "mocked_hashed_password_string":
            return True
        if plain_password == "adminpass" and hashed_password == "mocked_hashed_password_string":
            return True
        return False
    monkeypatch.setattr("iam_service.auth_methods.verify_password", mock_verify_password_func)

@pytest.fixture
def test_user_data():
    return {
        "username": "testuser",
        "password": "shortpassword",
        "role": "user",
    }


@pytest.fixture
def test_admin_data():
    return {
        "username": "adminuser",
        "password": "adminpass",
        "role": "admin",
    }


@pytest.fixture
def register_test_user(client, test_user_data):
    db = next(client.app.dependency_overrides[get_db]()) # Use the client's session
    # Directly set a mocked hashed password to avoid passlib ValueError
    hashed_password = "mocked_hashed_password_string"
    user = User(
        username=test_user_data["username"],
        hashed_password=hashed_password,
        role=test_user_data["role"],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def register_test_admin(client, test_admin_data):
    db = next(client.app.dependency_overrides[get_db]()) # Use the client's session
    # Directly set a mocked hashed password to avoid passlib ValueError
    hashed_password = "mocked_hashed_password_string"
    admin_user = User(
        username=test_admin_data["username"],
        hashed_password=hashed_password,
        role=test_admin_data["role"],
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    db.close()
    return admin_user


def test_register_user(client, test_user_data):
    response = client.post(
        "/api/auth/register",
        json={"username": test_user_data["username"], "password": test_user_data["password"], "role": test_user_data["role"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["username"] == test_user_data["username"]
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == test_user_data["role"]


def test_register_existing_user(client, register_test_user, test_user_data):
    response = client.post(
        "/api/auth/register",
        json={"username": test_user_data["username"], "password": test_user_data["password"], "role": test_user_data["role"]},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}


def test_login_for_access_token(client, register_test_user, test_user_data):
    response = client.post(
        "/api/auth/token",
        data={"username": test_user_data["username"], "password": test_user_data["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_for_access_token_invalid_credentials(client):
    response = client.post(
        "/api/auth/token", data={"username": "nonexistent", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


def test_read_users_me(client, register_test_user, test_user_data):
    mock_user_obj = create_mock_user(test_user_data)
    client.app.dependency_overrides[get_current_user] = lambda: mock_user_obj

    response = client.get(
        "/api/auth/users/me/", headers={"Authorization": f"Bearer dummy_token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user_data["username"]
    assert data["role"] == test_user_data["role"]
    assert data["hashed_password"] == "mocked_hashed_password_string"

    client.app.dependency_overrides.pop(get_current_user, None)


def test_read_users_me_unauthorized(client):
    response = client.get("/api/auth/users/me/")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_role_based_access_admin(client, register_test_admin, test_admin_data):
    mock_admin_obj = create_mock_user(test_admin_data)
    client.app.dependency_overrides[get_current_user] = lambda: mock_admin_obj

    response = client.post(
        "/blockchain/add_transaction", # Corrected URL
        headers={"Authorization": f"Bearer dummy_admin_token"},
        json={"ip": "192.168.1.1", "port": 80, "data": "test data"},
    )
    assert response.status_code != 403

    client.app.dependency_overrides.pop(get_current_user, None)


def test_role_based_access_non_admin(client, register_test_user, test_user_data):
    mock_user_obj = create_mock_user(test_user_data)
    client.app.dependency_overrides[get_current_user] = lambda: mock_user_obj

    response = client.post(
        "/orchestrator/blockchain/add_transaction", # Corrected URL
        headers={"Authorization": f"Bearer dummy_user_token"},
        json={"ip": "192.168.1.1", "port": 80, "data": "test data"},
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Not enough permissions"}

    client.app.dependency_overrides.pop(get_current_user, None)
