from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

# Define the path to the database file
DATABASE_DIR = os.path.join(os.path.dirname(__file__), "data") # Centralized DB directory
DATABASE_FILE = os.path.join(DATABASE_DIR, "audit_logs.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Ensure the database directory exists
os.makedirs(DATABASE_DIR, exist_ok=True)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


