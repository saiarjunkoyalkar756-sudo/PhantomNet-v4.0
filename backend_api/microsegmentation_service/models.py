from sqlalchemy import create_engine, Column, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./operational.db"  # Example using SQLite

Base = declarative_base()

class NetworkSegment(Base):
    __tablename__ = "network_segments"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    subnets = Column(JSON)

class SegmentationViolation(Base):
    __tablename__ = "segmentation_violations"
    id = Column(String, primary_key=True, index=True)
    timestamp = Column(String)
    source_ip = Column(String)
    destination_ip = Column(String)
    description = Column(String)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


