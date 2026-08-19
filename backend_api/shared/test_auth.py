import pytest
from backend_api.shared.database import Base, TestingSessionLocal, User, create_db_and_tables, get_db, test_engine
from backend_api.iam_service.auth_methods import (
    UserRole,
    create_access_token,
    get_current_user,
    get_password_hash,
    has_role,
)
import datetime
from unittest.mock import MagicMock

from fastapi import Depends

async def dummy_blockchain_add_transaction():
    return {"message": "success"}


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
    def mock_get_password_hash(password):
        return "mocked_hashed_password_string"
    monkeypatch.setattr("backend_api.iam_service.auth_methods.get_password_hash", mock_get_password_hash)

@pytest.fixture(autouse=True)
def mock_verify_password(monkeypatch):
    def mock_verify_password_func(plain_password, hashed_password):
        # Support both string and bytes format in verification safely
        if isinstance(hashed_password, bytes):
            hashed_password = hashed_password.decode('utf-8', errors='ignore')
        if plain_password == "shortpassword" and hashed_password == "mocked_hashed_password_string":
            return True
        if plain_password == "adminpass" and hashed_password == "mocked_hashed_password_string":
            return True
        return False
    monkeypatch.setattr("backend_api.iam_service.auth_methods.verify_password", mock_verify_password_func)

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
    db = TestingSessionLocal()
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
    db = TestingSessionLocal()
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
    data = response.json()["data"]
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
    assert response.json()["error"]["message"] == "Username already registered"


def test_login_for_access_token(client, register_test_user, test_user_data):
    response = client.post(
        "/api/auth/token",
        data={"username": test_user_data["username"], "password": test_user_data["password"]},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_for_access_token_invalid_credentials(client):
    response = client.post(
        "/api/auth/token", data={"username": "nonexistent", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Incorrect username or password"


def test_read_users_me(client, register_test_user, test_user_data):
    mock_user_obj = create_mock_user(test_user_data)
    client.app.dependency_overrides[get_current_user] = lambda: mock_user_obj
    if get_current_user:
        client.app.dependency_overrides[get_current_user] = lambda: mock_user_obj

    response = client.get(
        "/api/auth/users/me", headers={"Authorization": f"Bearer dummy_token"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["username"] == test_user_data["username"]
    assert data["role"] == test_user_data["role"]

    client.app.dependency_overrides.pop(get_current_user, None)
    if get_current_user:
        client.app.dependency_overrides.pop(get_current_user, None)


def test_read_users_me_unauthorized(client):
    response = client.get("/api/auth/users/me")
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Not authenticated"


def test_role_based_access_admin(client, register_test_admin, test_admin_data):
    if not any(route.path == "/blockchain/add_transaction" for route in client.app.routes):
        client.app.post("/blockchain/add_transaction", dependencies=[Depends(has_role([UserRole.ADMIN]))])(dummy_blockchain_add_transaction)

    mock_admin_obj = create_mock_user(test_admin_data)
    client.app.dependency_overrides[get_current_user] = lambda: mock_admin_obj
    if get_current_user:
        client.app.dependency_overrides[get_current_user] = lambda: mock_admin_obj

    response = client.post(
        "/blockchain/add_transaction", # Corrected URL
        headers={"Authorization": f"Bearer dummy_admin_token"},
        json={"ip": "192.168.1.1", "port": 80, "data": "test data"},
    )
    assert response.status_code != 403

    client.app.dependency_overrides.pop(get_current_user, None)
    if get_current_user:
        client.app.dependency_overrides.pop(get_current_user, None)


def test_role_based_access_non_admin(client, register_test_user, test_user_data):
    if not any(route.path == "/blockchain/add_transaction" for route in client.app.routes):
        client.app.post("/blockchain/add_transaction", dependencies=[Depends(has_role([UserRole.ADMIN]))])(dummy_blockchain_add_transaction)

    mock_user_obj = create_mock_user(test_user_data)
    client.app.dependency_overrides[get_current_user] = lambda: mock_user_obj
    if get_current_user:
        client.app.dependency_overrides[get_current_user] = lambda: mock_user_obj

    response = client.post(
        "/blockchain/add_transaction", # Corrected URL
        headers={"Authorization": f"Bearer dummy_user_token"},
        json={"ip": "192.168.1.1", "port": 80, "data": "test data"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Not enough permissions"

    client.app.dependency_overrides.pop(get_current_user, None)
    if get_current_user:
        client.app.dependency_overrides.pop(get_current_user, None)
