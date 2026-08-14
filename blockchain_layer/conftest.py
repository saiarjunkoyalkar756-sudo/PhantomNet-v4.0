import os
import sys

# Prevent shadowing of global backend_api by local blockchain_layer/backend_api
for path in list(sys.path):
    if "blockchain_layer" in path:
        try:
            sys.path.remove(path)
        except ValueError:
            pass
if "" in sys.path:
    sys.path.remove("")
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend_api.shared.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    import backend_api.shared.database
    import sys
    # Dynamically apply SQLite sessionmaker override to prevent psycopg2 connection errors
    backend_api.shared.database.SessionLocal = TestingSessionLocal
    if "blockchain_layer.test_blockchain" in sys.modules:
        sys.modules["blockchain_layer.test_blockchain"].SessionLocal = TestingSessionLocal

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# Override SessionLocal inside database module to use TestingSessionLocal for tests
import backend_api.shared.database
backend_api.shared.database.SessionLocal = TestingSessionLocal
