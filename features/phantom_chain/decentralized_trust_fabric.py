from __future__ import annotations

import base64
import datetime
import hashlib
import json
from typing import Any, Dict, List, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from sqlalchemy.orm import Session

from backend_api.shared.database import Block


class MerkleTree:
    """Calculate deterministic Merkle roots for a sequence of JSON-compatible transactions."""

    def __init__(self, transactions: List[Dict[str, Any]]):
        self.transactions = transactions
        self.root = self._build_tree([self._hash_tx(transaction) for transaction in transactions]) if transactions else ""

    @staticmethod
    def _hash_tx(transaction: Dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(transaction, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def _build_tree(self, hashes_at_level: List[str]) -> str:
        if not hashes_at_level:
            return ""
        if len(hashes_at_level) == 1:
            return hashes_at_level[0]
        next_level: List[str] = []
        for index in range(0, len(hashes_at_level), 2):
            left = hashes_at_level[index]
            right = hashes_at_level[index + 1] if index + 1 < len(hashes_at_level) else left
            next_level.append(hashlib.sha256(f"{left}{right}".encode()).hexdigest())
        return self._build_tree(next_level)


class DigitalSigner:
    """Verify externally supplied forensic signatures without retaining private key material."""

    @staticmethod
    def verify_signature(public_key_pem: str, data: str, signature_b64: str) -> bool:
        try:
            public_key = serialization.load_pem_public_key(public_key_pem.encode())
            public_key.verify(
                base64.b64decode(signature_b64),
                data.encode(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )
            return True
        except (ValueError, TypeError, InvalidSignature):
            return False


class PhantomChain:
    """Append-only forensic ledger with deterministic hash-link and Merkle-root verification.

    The ledger operates in memory when no database session is supplied. A session is optional and
    persists block metadata only; transaction payload retention remains the caller's responsibility.
    """

    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session
        self.chain = self._load_chain_from_db() if self.db is not None else []
        if not self.chain:
            self.chain = [self._create_genesis_block()]

    @staticmethod
    def _hash_block(payload: Dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def _load_chain_from_db(self) -> List[Dict[str, Any]]:
        assert self.db is not None
        chain: List[Dict[str, Any]] = []
        for row in self.db.query(Block).order_by(Block.index).all():
            transactions = [transaction.data for transaction in row.transactions]
            timestamp = row.timestamp.timestamp() if hasattr(row.timestamp, "timestamp") else float(row.timestamp)
            chain.append(
                {
                    "index": row.index,
                    "timestamp": timestamp,
                    "data": transactions,
                    "proof": row.proof,
                    "previous_hash": row.previous_hash,
                    "hash": row.block_hash,
                    "merkle_root": row.merkle_root or "",
                }
            )
        return chain

    def _persist_block_metadata(self, block: Dict[str, Any]) -> None:
        if self.db is None:
            return
        self.db.add(
            Block(
                index=block["index"],
                timestamp=datetime.datetime.fromtimestamp(block["timestamp"], datetime.timezone.utc),
                previous_hash=block["previous_hash"],
                block_hash=block["hash"],
                proof=block["proof"],
                merkle_root=block["merkle_root"],
            )
        )
        self.db.commit()

    def _create_genesis_block(self) -> Dict[str, Any]:
        timestamp = datetime.datetime.now(datetime.timezone.utc).timestamp()
        transactions = [{"event": "GENESIS_ROOT"}]
        merkle_root = MerkleTree(transactions).root
        payload = {
            "index": 1,
            "timestamp": timestamp,
            "transactions": transactions,
            "proof": 100,
            "previous_hash": "1",
            "merkle_root": merkle_root,
        }
        block = {
            "index": payload["index"],
            "timestamp": timestamp,
            "data": transactions,
            "proof": payload["proof"],
            "previous_hash": payload["previous_hash"],
            "hash": self._hash_block(payload),
            "merkle_root": merkle_root,
        }
        self._persist_block_metadata(block)
        return block

    def get_latest_block(self) -> Dict[str, Any]:
        return self.chain[-1]

    def add_block(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(transactions, list) or not all(isinstance(transaction, dict) for transaction in transactions):
            raise ValueError("transactions must be a list of JSON-compatible dictionaries")
        latest_block = self.get_latest_block()
        timestamp = datetime.datetime.now(datetime.timezone.utc).timestamp()
        merkle_root = MerkleTree(transactions).root
        payload = {
            "index": latest_block["index"] + 1,
            "timestamp": timestamp,
            "transactions": transactions,
            "proof": 100,
            "previous_hash": latest_block["hash"],
            "merkle_root": merkle_root,
        }
        block = {
            "index": payload["index"],
            "timestamp": timestamp,
            "data": transactions,
            "proof": payload["proof"],
            "previous_hash": payload["previous_hash"],
            "hash": self._hash_block(payload),
            "merkle_root": merkle_root,
        }
        self._persist_block_metadata(block)
        self.chain.append(block)
        return block

    def is_chain_valid(self) -> bool:
        for index in range(1, len(self.chain)):
            current = self.chain[index]
            previous = self.chain[index - 1]
            transactions = current["data"]
            merkle_root = MerkleTree(transactions).root
            payload = {
                "index": current["index"],
                "timestamp": current["timestamp"],
                "transactions": transactions,
                "proof": current["proof"],
                "previous_hash": current["previous_hash"],
                "merkle_root": merkle_root,
            }
            if current["hash"] != self._hash_block(payload):
                return False
            if current["previous_hash"] != previous["hash"]:
                return False
            if current.get("merkle_root", "") != merkle_root:
                return False
        return True
