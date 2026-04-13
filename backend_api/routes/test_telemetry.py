import json
import os
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend_api.gateway_service.main import app
from iam_service.auth_methods import create_access_token, get_password_hash
from shared.database import Base, User, get_db, create_db_and_tables

TEST_DATABASE_URL = "sqlite:///./test_telemetry.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestTelemetryAPI(unittest.TestCase):

    def setUp(self):
        create_db_and_tables(engine)
        self.client = TestClient(app)
        self.db = TestingSessionLocal()
        
        # Create a test user and token
        self.username = "testuser_telemetry"
        self.password = "testpassword"
        self.user = self.db.query(User).filter(User.username == self.username).first()
        if not self.user:
            hashed_password = get_password_hash(self.password)
            self.user = User(username=self.username, hashed_password=hashed_password, role="admin")
            self.db.add(self.user)
            self.db.commit()
            self.db.refresh(self.user)

        jwt_data = {
            "sub": self.user.username,
            "role": self.user.role,
            "twofa_enabled": False,
            "twofa_enforced": False,
        }
        self.token = create_access_token(self.db, user_id=self.user.id, data=jwt_data)

    def tearDown(self):
        self.db.close()
        os.remove("./test_telemetry.db")

    def test_ingest_custom_log(self):
        self.client.cookies = {"access_token": self.token}
        log_data = {
            "source": "my-custom-app",
            "log_entry": {
                "message": "This is a custom log message",
                "level": "info",
                "timestamp": "2023-12-06T12:00:00Z"
            }
        }
        
        response = self.client.post("/api/telemetry/ingest", json=log_data)
        
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), {"message": "Log entry accepted for ingestion."})

    def test_ingest_custom_log_unauthenticated(self):
        self.client.cookies.clear()
        log_data = {
            "source": "my-custom-app",
            "log_entry": "This is a custom log message"
        }
        
        response = self.client.post("/api/telemetry/ingest", json=log_data)
        
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()