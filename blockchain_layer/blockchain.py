# backend_api/blockchain_layer/blockchain.py
import os
import json
import hashlib
import datetime
from datetime import timezone
from typing import List, Any

from sqlalchemy.orm import Session
from backend_api.database import Block
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
        if not self.db.query(Block).filter(Block.index == 1).first():
            # Create the genesis block if no blocks exist
            genesis_root = get_merkle_root(["GENESIS_BLOCK"])
            self.new_block(proof=1, previous_hash="1", merkle_root=genesis_root)
            self.db.commit()

    @staticmethod
    def hash(block_data: dict) -> str:
        """Creates a SHA-256 hash of a dictionary representing a block."""
        block_string = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self) -> Block | None:
        """Returns the last Block in the database."""
        return self.db.query(Block).order_by(Block.index.desc()).first()

    def new_block(self, proof: int, merkle_root: str, previous_hash: str = None) -> Block:
        """
        Creates a new Block and adds it to the database session.
        """
        last_block = self.last_block
        block_index = (last_block.index + 1) if last_block else 1
        
        block_for_hashing = {
            "index": block_index,
            "timestamp": datetime.datetime.now(timezone.utc).isoformat(),
            "proof": proof,
            "merkle_root": merkle_root,
            "previous_hash": previous_hash or (self.hash(last_block.to_dict()) if last_block else "1"),
        }
        
        block_hash = self.hash(block_for_hashing)

        new_db_block = Block(
            index=block_index,
            timestamp=datetime.datetime.fromisoformat(block_for_hashing["timestamp"]),
            proof=proof,
            previous_hash=block_for_hashing["previous_hash"],
            merkle_root=merkle_root,
            block_hash=block_hash,
        )
        self.db.add(new_db_block)
        return new_db_block

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
        
        Args:
            data_batch (List[Any]): A list of serializable data items (e.g., dicts).

        Returns:
            Block: The new block that was added to the chain.
        """
        if not data_batch:
            raise ValueError("Cannot commit an empty batch.")

        last_block = self.last_block
        last_proof = last_block.proof
        new_proof = self.proof_of_work(last_proof)
        
        merkle_root = get_merkle_root(data_batch)

        previous_hash = last_block.block_hash
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
            
            # Re-create the dictionary that was hashed for this block
            block_for_hashing = {
                "index": block.index,
                "timestamp": block.timestamp.isoformat(),
                "proof": block.proof,
                "merkle_root": block.merkle_root,
                "previous_hash": block.previous_hash,
            }
            
            # Check if the block's hash is correct
            if block.block_hash != self.hash(block_for_hashing):
                return False
            
            # Check if the previous_hash link is correct
            if block.previous_hash != last_block.block_hash:
                return False
            
            # Check if the proof of work is valid
            if not self.valid_proof(last_block.proof, block.proof):
                return False
            
            last_block = block
            
        return True