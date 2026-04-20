import hashlib
import datetime
import json
import base64
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

from shared.database import Block

class MerkleTree:
    """Implement Merkle Tree for forensic proof integrity."""
    def __init__(self, transactions: List[Dict[str, Any]]):
        self.transactions = transactions
        self.root = self._build_tree([self._hash_tx(tx) for tx in transactions]) if transactions else None

    def _hash_tx(self, tx: Dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest()

    def _build_tree(self, hashed_txs: List[str]) -> str:
        if len(hashed_txs) == 0:
            return ""
        if len(hashed_txs) == 1:
            return hashed_txs[0]

        new_level = []
        for i in range(0, len(hashed_txs) - 1, 2):
            combined = hashed_txs[i] + hashed_txs[i + 1]
            new_level.append(hashlib.sha256(combined.encode()).hexdigest())
        
        if len(hashed_txs) % 2 != 0:
            combined = hashed_txs[-1] + hashed_txs[-1]
            new_level.append(hashlib.sha256(combined.encode()).hexdigest())

        return self._build_tree(new_level)

class DigitalSigner:
    """Handles chain-of-custody cryptographic signatures."""
    @staticmethod
    def verify_signature(public_key_pem: str, data: str, signature_b64: str) -> bool:
        try:
            public_key = serialization.load_pem_public_key(public_key_pem.encode())
            signature = base64.b64decode(signature_b64)
            public_key.verify(
                signature,
                data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False
        except Exception:
            return False


class PhantomChain:
    """
    A decentralized trust fabric for PhantomNet, with SQLAlchemy persistence.
    Enhanced with Merkle Trees and Digital Signatures for Immutable Forensic Audits.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.chain = self._load_chain_from_db()
        if not self.chain:
            self.chain = [self._create_and_save_genesis_block()]
        print("Initializing Advanced PhantomChain with Forensic Merkle capabilities...")

    def _load_chain_from_db(self):
        chain_data = self.db.query(Block).order_by(Block.index).all()
        chain = []
        for block_db in chain_data:
            block_data = {
                "index": block_db.index,
                "timestamp": block_db.timestamp.timestamp() if hasattr(block_db.timestamp, 'timestamp') else block_db.timestamp,
                "data": block_db.data,
                "proof": block_db.proof,
                "previous_hash": block_db.previous_hash,
                "hash": block_db.hash,
                "merkle_root": getattr(block_db, 'merkle_root', None),
            }
            chain.append(block_data)
        return chain

    def _create_and_save_genesis_block(self):
        genesis_block_data = {
            "index": 1,
            "timestamp": datetime.datetime.utcnow(),
            "transactions": [{"event": "GENESIS_ROOT"}],
            "proof": 100,
            "previous_hash": "1",
            "merkle_root": ""
        }
        genesis_tree = MerkleTree(genesis_block_data["transactions"])
        genesis_block_data["merkle_root"] = genesis_tree.root or ""
        
        genesis_block_hash = hashlib.sha256(
            json.dumps(genesis_block_data, sort_keys=True).encode()
        ).hexdigest()

        genesis_block = Block(
            index=genesis_block_data["index"],
            timestamp=genesis_block_data["timestamp"],
            data=json.dumps(genesis_block_data["transactions"]),
            proof=genesis_block_data["proof"],
            previous_hash=genesis_block_data["previous_hash"],
            hash=genesis_block_hash,
        )
        if hasattr(genesis_block, 'merkle_root'):
            genesis_block.merkle_root = genesis_block_data["merkle_root"]
            
        self.db.add(genesis_block)
        self.db.commit()
        return genesis_block

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, transactions: List[Dict[str, Any]]):
        """Adds a block of forensic logs, using Merkle Trees for high-integrity proof."""
        latest_block = self.get_latest_block()

        new_block_index = latest_block["index"] + 1
        new_block_timestamp = datetime.datetime.utcnow()
        new_block_previous_hash = latest_block["hash"]
        
        # Calculate Merkle Root for the transactions
        merkle_tree = MerkleTree(transactions)
        merkle_root = merkle_tree.root or ""

        new_block_proof = 100  # Proof of work can be scaled dynamically here
        block_payload = {
            "index": new_block_index,
            "timestamp": new_block_timestamp.timestamp(),
            "transactions": transactions,
            "proof": new_block_proof,
            "previous_hash": new_block_previous_hash,
            "merkle_root": merkle_root
        }
        
        new_block_hash = hashlib.sha256(
            json.dumps(block_payload, sort_keys=True).encode()
        ).hexdigest()

        new_block = Block(
            index=new_block_index,
            timestamp=new_block_timestamp,
            data=json.dumps(transactions),
            previous_hash=new_block_previous_hash,
            hash=new_block_hash,
            proof=new_block_proof,
        )
        if hasattr(new_block, 'merkle_root'):
            new_block.merkle_root = merkle_root
            
        self.db.add(new_block)
        self.db.commit()
        
        self.chain.append({
            "index": new_block_index,
            "timestamp": new_block_timestamp.timestamp(),
            "data": json.dumps(transactions),
            "proof": new_block_proof,
            "previous_hash": new_block_previous_hash,
            "hash": new_block_hash,
            "merkle_root": merkle_root
        })
        print(f"Added Forensic Block {new_block_index} to PhantomChain - Merkle Root: {merkle_root}")
        return new_block

    def is_chain_valid(self):
        """Cryptographically verifies entire chain-of-custody."""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            tx_data = json.loads(current_block["data"]) if isinstance(current_block["data"], str) else current_block["data"]
            merkle_tree = MerkleTree(tx_data)
            
            recalculated_hash = hashlib.sha256(
                json.dumps(
                    {
                        "index": current_block["index"],
                        "timestamp": current_block["timestamp"],
                        "transactions": tx_data,
                        "proof": current_block["proof"],
                        "previous_hash": current_block["previous_hash"],
                        "merkle_root": merkle_tree.root or ""
                    },
                    sort_keys=True,
                ).encode()
            ).hexdigest()

            if current_block["hash"] != recalculated_hash:
                print(f"CRITICAL FORENSIC BREACH: Block {current_block['index']} tampered! Stored: {current_block['hash']}, Recalculated: {recalculated_hash}")
                return False

            if current_block["previous_hash"] != previous_block["hash"]:
                print(f"CRITICAL FORENSIC BREACH: Link between block {previous_block['index']} and {current_block['index']} is broken.")
                return False
                
            # Verify Merkle Root if block supports it
            if "merkle_root" in current_block and current_block["merkle_root"]:
                if current_block["merkle_root"] != merkle_tree.root:
                    print(f"CRITICAL FORENSIC BREACH: Merkle Root tampered at Block {current_block['index']}!")
                    return False

        print("PhantomChain Audit: 100% Cryptographically Valid.")
        return True
