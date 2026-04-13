import pytest
import os
import json
import datetime
import importlib
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from blockchain_layer.blockchain import Blockchain
from shared.database import Base, Block, Transaction, SessionLocal # Moved Block, Transaction, SessionLocal here


# Define a fixture for an in-memory SQLite database session for testing
@pytest.fixture(scope="function")
def db_session_factory():
    # Define the database file path in a temporary location
    db_file_path = os.path.join(
        "/data/data/com.termux/files/home/.gemini/tmp/ad1ea826cb0f4295afdb1907c7352a84a1a1003965f03d9432baf71cd1d2a7bf",
        f"test_db_{os.getpid()}.db",
    )

    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_file_path), exist_ok=True)

    # Physically delete the database file before each test to ensure a clean slate
    if os.path.exists(db_file_path):
        os.remove(db_file_path)

    # RELOAD THE DATABASE MODULE AGGRESSIVELY
    import backend_api.database

    importlib.reload(backend_api.database)
 

    # Create a local engine and SessionLocal for this test, using the reloaded database module's Base
    local_engine = create_engine(
        f"sqlite:///{db_file_path}", connect_args={"check_same_thread": False}
    )
    LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=local_engine)

    # Drop all tables to ensure a clean slate, including previous runs
    Base.metadata.drop_all(bind=local_engine)
    # Create tables based on the latest schema for this local engine
    Base.metadata.create_all(bind=local_engine)

    yield LocalSession

    # Clean up the database after each test
    Base.metadata.drop_all(bind=local_engine)
    if os.path.exists(db_file_path):
        os.remove(db_file_path)


def test_new_blockchain_creates_genesis_block(db_session_factory):
    with db_session_factory() as db_session:
        # Initialize a new Blockchain instance
        blockchain = Blockchain(db_session)

        # Query the database for blocks
        blocks = db_session.query(Block).all()
        assert len(blocks) == 1

        genesis_block = blocks[0]
        assert genesis_block.index == 1
        assert genesis_block.previous_hash == "1"
        assert genesis_block.proof == 100
        assert genesis_block.block_hash is not None
        assert genesis_block.merkle_root is None  # Genesis block has no transactions


def test_new_transaction_adds_to_db_session(db_session_factory):
    with db_session_factory() as db_session:
        blockchain = Blockchain(db_session)
        # Ensure there are no pending transactions initially
        assert (
            db_session.query(Transaction).filter(Transaction.block_id == None).count() == 0
        )

        tx = blockchain.new_transaction(
            "sender_test", "recipient_test", 10.0, "test_data", "type_a", 0.9
        )
        db_session.commit()  # Commit to make it visible to count

        assert tx is not None
        assert tx.sender == "sender_test"
        assert tx.transaction_hash is not None
        assert (
            db_session.query(Transaction).filter(Transaction.block_id == None).count() == 1
        )


def test_new_block_links_pending_transactions_and_resets(db_session_factory):
    with db_session_factory() as db_session:
        blockchain = Blockchain(db_session)  # Genesis block created

        # Add some pending transactions
        tx1 = blockchain.new_transaction("s1", "r1", 1.0)
        tx2 = blockchain.new_transaction("s2", "r2", 2.0)
        db_session.commit()

        # Mine a new block
        last_block = blockchain.last_block
        proof = blockchain.proof_of_work(last_block.proof)
        new_block = blockchain.new_block(proof)
        db_session.commit()  # Commit the new block and linked transactions

        assert new_block is not None
        assert new_block.index == 2
        assert new_block.previous_hash == last_block.block_hash
        assert new_block.block_hash is not None
        assert new_block.merkle_root is not None
        assert len(new_block.transactions) == 2
        assert (
            db_session.query(Transaction).filter(Transaction.block_id == None).count() == 0
        )  # No pending transactions

        # Verify transactions are correctly linked
        retrieved_tx1 = db_session.query(Transaction).filter_by(id=tx1.id).first()
        retrieved_tx2 = db_session.query(Transaction).filter_by(id=tx2.id).first()
        assert retrieved_tx1.block_id == new_block.id
        assert retrieved_tx2.block_id == new_block.id


def test_hash_produces_consistent_hash():
    # Test hashing a dictionary
    data_dict = {"key": "value", "number": 123}
    hash1 = Blockchain.hash(data_dict)
    hash2 = Blockchain.hash(data_dict)
    assert hash1 == hash2

    # Test hashing a Block object (requires a dummy block)
    dummy_block = Block(
        index=1,
        timestamp=datetime.datetime.now(datetime.UTC),
        previous_hash="0",
        block_hash="dummy_hash",
        proof=1,
        merkle_root="dummy_merkle",
    )
    # The hash method will calculate its own hash, so block_hash will be ignored for input hashing
    hash3 = Blockchain.hash(dummy_block)
    # Change something internal to the dummy block, hash should change
    dummy_block.proof = 2
    hash4 = Blockchain.hash(dummy_block)
    assert hash3 != hash4


def test_proof_of_work_finds_valid_proof(db_session_factory):
    with db_session_factory() as db_session:
        blockchain = Blockchain(db_session)
        last_block = blockchain.last_block
        proof = blockchain.proof_of_work(last_block.proof)
        assert Blockchain.valid_proof(last_block.proof, proof) is True


def test_is_chain_valid_with_valid_chain(db_session_factory):
    with db_session_factory() as db_session:
        blockchain = Blockchain(db_session)  # Genesis block

        # Add a transaction and mine a new block
        blockchain.new_transaction("s1", "r1", 10.0)
        proof1 = blockchain.proof_of_work(blockchain.last_block.proof)
        blockchain.new_block(proof1)
        db_session.commit()

        # Add another transaction and mine another block
        blockchain.new_transaction("s2", "r2", 20.0)
        proof2 = blockchain.proof_of_work(blockchain.last_block.proof)
        blockchain.new_block(proof2)
        db_session.commit()

        assert blockchain.is_chain_valid() is True


def test_is_chain_valid_with_full_transaction(db_session_factory):
    with db_session_factory() as db_session:
        blockchain = Blockchain(db_session)  # Genesis block

        # Add a transaction with all fields and mine a new block
        blockchain.new_transaction(
            "s1",
            "r1",
            10.0,
            data="test data",
            attack_type="test_attack",
            confidence_score=0.99,
            alert_id=123,
            normalized_event_id=456,
            forensic_record_id=789,
            data_type="test_log"
        )
        proof = blockchain.proof_of_work(blockchain.last_block.proof)
        blockchain.new_block(proof)
        db_session.commit()

        assert blockchain.is_chain_valid() is True


def test_is_chain_valid_with_tampered_block_hash(db_session: Session):
    blockchain = Blockchain(db_session)  # Genesis block
    blockchain.new_transaction("s1", "r1", 10.0)
    proof = blockchain.proof_of_work(blockchain.last_block.proof)
    blockchain.new_block(proof)
    db_session.commit()

    # Tamper with a block's hash
    tampered_block = db_session.query(Block).filter_by(index=2).first()
    tampered_block.block_hash = "fake_hash"
    db_session.commit()

    assert blockchain.is_chain_valid() is False


def test_is_chain_valid_with_tampered_transaction_hash(db_session: Session):
    blockchain = Blockchain(db_session)  # Genesis block
    tx = blockchain.new_transaction("s1", "r1", 10.0)
    proof = blockchain.proof_of_work(blockchain.last_block.proof)
    blockchain.new_block(proof)
    db_session.commit()

    # Get the ID of the transaction to tamper
    tx_id = tx.id

    # Tamper with the transaction's hash in a new session to simulate external tampering
    with SessionLocal() as tamper_session:
        tampered_tx = tamper_session.query(Transaction).filter_by(id=tx_id).first()
        tampered_tx.transaction_hash = "another_fake_hash"
        tamper_session.commit()

    # Create a new blockchain instance with a fresh session to validate the tampered chain
    with SessionLocal() as validate_session:
        blockchain_validator = Blockchain(validate_session)
        assert blockchain_validator.is_chain_valid() is False


def test_is_chain_valid_with_tampered_merkle_root(db_session: Session):
    blockchain = Blockchain(db_session)  # Genesis block
    blockchain.new_transaction("s1", "r1", 10.0)
    proof = blockchain.proof_of_work(blockchain.last_block.proof)
    blockchain.new_block(proof)
    db_session.commit()

    # Tamper with a block's merkle root
    tampered_block = db_session.query(Block).filter_by(index=2).first()
    tampered_block.merkle_root = "fake_merkle_root"
    db_session.commit()

    assert blockchain.is_chain_valid() is False


def test_is_chain_valid_with_tampered_proof(db_session: Session):
    blockchain = Blockchain(db_session)  # Genesis block
    blockchain.new_transaction("s1", "r1", 10.0)
    proof = blockchain.proof_of_work(blockchain.last_block.proof)
    blockchain.new_block(proof)
    db_session.commit()

    # Tamper with a block's proof
    tampered_block = db_session.query(Block).filter_by(index=2).first()
    tampered_block.proof = 12345  # Invalid proof
    db_session.commit()

    assert blockchain.is_chain_valid() is False


def test_is_chain_valid_with_tampered_previous_hash(db_session: Session):
    blockchain = Blockchain(db_session)  # Genesis block
    blockchain.new_transaction("s1", "r1", 10.0)
    proof = blockchain.proof_of_work(blockchain.last_block.proof)
    blockchain.new_block(proof)
    db_session.commit()

    # Tamper with a block's previous hash
    tampered_block = db_session.query(Block).filter_by(index=2).first()
    tampered_block.previous_hash = "fake_previous_hash"
    db_session.commit()

    assert blockchain.is_chain_valid() is False
