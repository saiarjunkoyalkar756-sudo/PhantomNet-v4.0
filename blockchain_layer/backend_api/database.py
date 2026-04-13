from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
import datetime
from datetime import UTC

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Block(Base):
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, index=True)
    index = Column(Integer, unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.now(datetime.UTC))
    previous_hash = Column(String)
    block_hash = Column(String)
    proof = Column(Integer)
    merkle_root = Column(String)
    transactions = relationship("Transaction", back_populates="block")

    def to_dict(self):
        return {
            "id": self.id,
            "index": self.index,
            "timestamp": self.timestamp.isoformat(timespec="microseconds"),
            "previous_hash": self.previous_hash,
            "block_hash": self.block_hash,
            "proof": self.proof,
            "merkle_root": self.merkle_root,
            "transactions": [tx.to_dict() for tx in self.transactions],
        }


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("blocks.id"))
    sender = Column(String)
    recipient = Column(String)
    amount = Column(Float)
    data = Column(String)
    attack_type = Column(String)
    confidence_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.now(datetime.UTC))
    transaction_hash = Column(String)
    alert_id = Column(Integer)
    normalized_event_id = Column(Integer)
    forensic_record_id = Column(Integer)
    data_type = Column(String)
    block = relationship("Block", back_populates="transactions")

    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "data": self.data,
            "attack_type": self.attack_type,
            "confidence_score": self.confidence_score,
            "timestamp": self.timestamp.isoformat(timespec="microseconds"),
            "transaction_hash": self.transaction_hash,
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
