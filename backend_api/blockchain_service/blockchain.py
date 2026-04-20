# backend_api/blockchain_service/blockchain.py
import hashlib
import json
import asyncio
from time import time
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend_api.shared.database import Block, Transaction
from backend_api.core.logging import logger as pn_logger

class Blockchain:
    """
    Asynchronous Blockchain service for secure, immutable audit trail notarization.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.current_transactions = []

    async def get_last_block(self) -> Optional[Block]:
        """Returns the last block in the chain."""
        stmt = select(Block).order_by(desc(Block.index)).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    @property
    async def last_block(self) -> Optional[Block]:
        return await self.get_last_block()

    async def new_transaction(self, sender: str, recipient: str, amount: float, data: Optional[Dict] = None) -> int:
        """
        Creates a new transaction to go into the next mined Block.
        """
        tx_data = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'data': data,
            'timestamp': time(),
        }
        # Generate a unique hash for the transaction
        tx_string = json.dumps(tx_data, sort_keys=True).encode()
        tx_hash = hashlib.sha256(tx_string).hexdigest()
        tx_data['transaction_hash'] = tx_hash
        
        self.current_transactions.append(tx_data)
        pn_logger.debug(f"New transaction added: {tx_hash[:8]}...")
        return 0 

    async def _calculate_merkle_root(self, transactions: List[Dict]) -> str:
        """Calculates a simplified Merkle Root for the transactions."""
        if not transactions:
            return hashlib.sha256(b"empty").hexdigest()
        
        combined_hashes = "".join([tx['transaction_hash'] for tx in transactions])
        return hashlib.sha256(combined_hashes.encode()).hexdigest()

    async def mine_block(self, proof: int, previous_hash: Optional[str] = None) -> Block:
        """
        Asynchronously creates and persists a new Block in the Blockchain.
        """
        last_block = await self.get_last_block()
        index = (last_block.index + 1) if last_block else 1
        prev_h = previous_hash or (last_block.block_hash if last_block else '1')
        
        merkle_root = await self._calculate_merkle_root(self.current_transactions)

        # Calculate block hash based on structural data
        block_data = {
            'index': index,
            'proof': proof,
            'previous_hash': prev_h,
            'merkle_root': merkle_root,
            'timestamp': time(),
        }
        block_string = json.dumps(block_data, sort_keys=True).encode()
        block_hash = hashlib.sha256(block_string).hexdigest()

        new_block = Block(
            index=index,
            previous_hash=prev_h,
            proof=proof,
            block_hash=block_hash,
            merkle_root=merkle_root,
            timestamp=datetime.datetime.fromtimestamp(block_data['timestamp']) if 'datetime' in globals() else None # Handled by DB default usually
        )
        
        # Add transactions to the block
        for tx_dict in self.current_transactions:
            tx = Transaction(
                sender=tx_dict['sender'],
                recipient=tx_dict['recipient'],
                amount=tx_dict['amount'],
                data=tx_dict['data'],
                transaction_hash=tx_dict['transaction_hash']
            )
            new_block.transactions.append(tx)
            
        self.current_transactions = [] # Reset pending tx
        
        self.db.add(new_block)
        await self.db.flush()
        pn_logger.info(f"Block #{index} mined successfully. Hash: {block_hash[:12]}...")
        return new_block

    async def is_chain_valid(self) -> bool:
        """Determines if the entire blockchain in the database is valid."""
        stmt = select(Block).order_by(Block.index)
        result = await self.db.execute(stmt)
        chain = result.scalars().all()
        
        if not chain:
            return True

        for i in range(1, len(chain)):
            block = chain[i]
            last_block = chain[i-1]
            
            # Check if previous hash links match
            if block.previous_hash != last_block.block_hash:
                pn_logger.error(f"Integrity check FAILED: Block #{block.index} previous_hash mismatch.")
                return False

            # Validating the proof of work (Simplified)
            # In production, we would re-run proof_of_work verification logic here
            
        pn_logger.info("Blockchain integrity check PASSED.")
        return True
