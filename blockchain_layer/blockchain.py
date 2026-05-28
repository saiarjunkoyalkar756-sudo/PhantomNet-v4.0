# backend_api/blockchain_layer/blockchain.py
import os
import json
import hashlib
import datetime
from datetime import timezone
from typing import List, Any, Dict, Optional

from sqlalchemy.orm import Session
from backend_api.shared.database import Block, Transaction
from backend_api.shared.merkle import get_merkle_root

class BlockchainNotary:
    """
    Manages an immutable, tamper-resistant log of data batches by storing
    their Merkle roots on a blockchain. This acts as a high-integrity
    notarization service.
    """

    def __init__(self, db: Session):
        """
        Initializes the Notary service.
        Args:
            db (Session): The SQLAlchemy session for database interaction.
        """
        self.db = db
        self.current_transactions = []
        
        # Load any pending transactions already in the database
        pending_txs = self.db.query(Transaction).filter(Transaction.block_id == None).all()
        self.current_transactions.extend(pending_txs)

        if not self.db.query(Block).filter(Block.index == 1).first():
            # Create the genesis block if no blocks exist
            # Genesis block has proof=100 in tests, and merkle_root=None
            self.new_block(proof=100, previous_hash="1", merkle_root=None)
            self.db.commit()

    @staticmethod
    def hash(block_data: Any) -> str:
        """Creates a SHA-256 hash of a block's structural header fields."""
        if hasattr(block_data, "to_dict"):
            block_dict = block_data.to_dict()
        elif isinstance(block_data, dict):
            block_dict = block_data
        else:
            # Fallback for SQLAlchemy objects or custom objects
            block_dict = {
                "index": getattr(block_data, "index", None),
                "timestamp": getattr(block_data, "timestamp", None),
                "proof": getattr(block_data, "proof", None),
                "merkle_root": getattr(block_data, "merkle_root", None),
                "previous_hash": getattr(block_data, "previous_hash", None),
            }

        # Standardize timestamp to ISO format string (timezone-naive, microsecond-stable)
        ts = block_dict.get("timestamp")
        if isinstance(ts, datetime.datetime):
            ts_str = ts.replace(tzinfo=None, microsecond=0).isoformat()
        else:
            ts_str = str(ts)

        hash_dict = {
            "index": block_dict.get("index"),
            "timestamp": ts_str,
            "proof": block_dict.get("proof"),
            "merkle_root": block_dict.get("merkle_root"),
            "previous_hash": block_dict.get("previous_hash"),
        }
        
        block_string = json.dumps(hash_dict, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self) -> Block | None:
        """Returns the last Block in the database."""
        return self.db.query(Block).order_by(Block.index.desc()).first()

    def new_block(self, proof: int, previous_hash: str = None, merkle_root: str = None) -> Block:
        """
        Creates a new Block and adds it to the database session.
        """
        last_block = self.last_block
        block_index = (last_block.index + 1) if last_block else 1
        
        # If no merkle_root is provided, calculate from pending transactions
        if merkle_root is None:
            tx_data_list = []
            for tx in self.current_transactions:
                tx_data_list.append(str(tx.transaction_hash))
            if tx_data_list:
                merkle_root = get_merkle_root(tx_data_list)
            else:
                # Genesis block has merkle_root=None, subsequent empty blocks have dummy root
                merkle_root = None if block_index == 1 else get_merkle_root(["EMPTY_BLOCK"])

        # Timezone-naive stable UTC timestamp
        block_timestamp = datetime.datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
        
        block_for_hashing = {
            "index": block_index,
            "timestamp": block_timestamp.isoformat(),
            "proof": proof,
            "merkle_root": merkle_root,
            "previous_hash": previous_hash or (last_block.block_hash if last_block else "1"),
        }
        
        block_hash = self.hash(block_for_hashing)

        new_db_block = Block(
            index=block_index,
            timestamp=block_timestamp,
            proof=proof,
            previous_hash=block_for_hashing["previous_hash"],
            merkle_root=merkle_root,
            block_hash=block_hash,
        )
        self.db.add(new_db_block)
        
        # We need to persist the block so it gets an ID
        self.db.flush()
        
        # Associate pending transactions with this block
        for tx in self.current_transactions:
            tx.block_id = new_db_block.id
            self.db.add(tx)
        
        self.current_transactions = []
        return new_db_block

    def new_transaction(
        self,
        sender: str,
        recipient: str,
        amount: float,
        data: Any = None,
        attack_type: str = None,
        confidence_score: float = None,
        alert_id: int = None,
        normalized_event_id: int = None,
        forensic_record_id: int = None,
        data_type: str = None,
    ) -> Transaction:
        """Creates a new transaction and adds it to the database and current pending transactions."""
        # Timezone-naive stable UTC timestamp
        tx_timestamp = datetime.datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
        
        # Standardize data to dict or serializable representation for transaction hashing
        serialized_data = None
        if data:
            if isinstance(data, dict):
                serialized_data = data
            elif isinstance(data, str):
                try:
                    serialized_data = json.loads(data)
                except Exception:
                    serialized_data = {"raw_data": data}
            else:
                serialized_data = {"raw_data": str(data)}

        # Build structure for hashing
        tx_data = {
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
            "data": serialized_data,
            "attack_type": attack_type,
            "confidence_score": confidence_score,
            "alert_id": alert_id,
            "normalized_event_id": normalized_event_id,
            "forensic_record_id": forensic_record_id,
            "data_type": data_type,
            "timestamp": tx_timestamp.isoformat(),
        }
        
        tx_string = json.dumps(tx_data, sort_keys=True).encode()
        tx_hash = hashlib.sha256(tx_string).hexdigest()
        
        new_tx = Transaction(
            sender=sender,
            recipient=recipient,
            amount=amount,
            data=serialized_data,
            attack_type=attack_type,
            confidence_score=confidence_score,
            alert_id=alert_id,
            normalized_event_id=normalized_event_id,
            forensic_record_id=forensic_record_id,
            data_type=data_type,
            timestamp=tx_timestamp,
            transaction_hash=tx_hash,
        )
        
        self.db.add(new_tx)
        self.current_transactions.append(new_tx)
        return new_tx

    def proof_of_work(self, last_proof: int) -> int:
        """Simple Proof of Work Algorithm."""
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof: int, proof: int) -> bool:
        """Validates the proof: does hash(last_proof, proof) have 4 leading zeroes?"""
        guess = f"{last_proof}{proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def commit_audit_batch(self, data_batch: List[Any]) -> Block:
        """
        Takes a batch of audit data, calculates its Merkle root, mines a new block,
        and commits it to the chain.
        """
        if not data_batch:
            raise ValueError("Cannot commit an empty batch.")

        last_block = self.last_block
        last_proof = last_block.proof if last_block else 100
        new_proof = self.proof_of_work(last_proof)
        
        merkle_root = get_merkle_root(data_batch)

        previous_hash = last_block.block_hash if last_block else "1"
        new_block = self.new_block(
            proof=new_proof, previous_hash=previous_hash, merkle_root=merkle_root
        )
        
        # Commit the session to save the new block
        self.db.commit()
        return new_block

    def is_chain_valid(self) -> bool:
        """
        Determines if the entire blockchain in the database is valid.
        """
        blocks = self.db.query(Block).order_by(Block.index).all()
        if not blocks:
            return True

        last_block = blocks[0]
        for i in range(1, len(blocks)):
            block = blocks[i]
            
            # Check if the block's hash is correct
            if block.block_hash != self.hash(block):
                return False
            
            # Check if the previous_hash link is correct
            if block.previous_hash != last_block.block_hash:
                return False
            
            # Check if the proof of work is valid
            if not self.valid_proof(last_block.proof, block.proof):
                return False
                
            # Validate transaction integrity inside the block
            for tx in block.transactions:
                ts_val = tx.timestamp
                if isinstance(ts_val, datetime.datetime):
                    ts_str = ts_val.replace(tzinfo=None, microsecond=0).isoformat()
                else:
                    ts_str = str(ts_val)
                    
                tx_data = {
                    "sender": tx.sender,
                    "recipient": tx.recipient,
                    "amount": tx.amount,
                    "data": tx.data,
                    "attack_type": tx.attack_type,
                    "confidence_score": tx.confidence_score,
                    "alert_id": tx.alert_id,
                    "normalized_event_id": tx.normalized_event_id,
                    "forensic_record_id": tx.forensic_record_id,
                    "data_type": tx.data_type,
                    "timestamp": ts_str,
                }
                
                # Check for tampered transaction hash
                tx_string = json.dumps(tx_data, sort_keys=True).encode()
                expected_hash = hashlib.sha256(tx_string).hexdigest()
                if tx.transaction_hash != expected_hash:
                    return False
            
            last_block = block
            
        return True

# Alias for backward compatibility and tests
Blockchain = BlockchainNotary