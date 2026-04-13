import logging
import asyncio
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

from utils.logger import get_logger # Use the structured logger

class EvidenceVault:
    """
    Manages the storage, hashing, and indexing of forensic evidence.
    Stores evidence files on disk and maintains an in-memory metadata index.
    """
    def __init__(self, base_dir: Path):
        self.logger = get_logger("phantomnet_agent.evidence_vault")
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_index: Dict[str, Dict[str, Any]] = {} # {evidence_id: metadata}
        self.logger.info(f"EvidenceVault initialized at: {self.base_dir.resolve()}")

    def _generate_id(self) -> str:
        """Generates a unique ID for evidence."""
        return str(uuid.uuid4())

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculates the SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192): # Read in chunks to handle large files
                hasher.update(chunk)
        return hasher.hexdigest()

    async def _store_evidence_file(self, evidence_id: str, content: bytes, file_extension: str = ".bin") -> Path:
        """Stores the raw evidence content to a file and returns its path."""
        file_path = self.base_dir / f"{evidence_id}{file_extension}"
        try:
            # Using asyncio.to_thread for blocking I/O to not block the event loop
            await asyncio.to_thread(lambda: file_path.write_bytes(content))
            self.logger.debug(f"Evidence file saved to {file_path}")
            return file_path
        except Exception as e:
            self.logger.error(f"Failed to save evidence file for {evidence_id} to {file_path}: {e}", exc_info=True)
            raise

    async def store_evidence(self, data: Union[bytes, str], source: str, tags: Optional[List[str]] = None, filename: Optional[str] = None) -> str:
        """
        Stores given data as evidence, hashes it, and adds metadata to the index.
        Returns the generated evidence ID.
        """
        evidence_id = self._generate_id()
        file_extension = ".txt" if isinstance(data, str) else ".bin"
        if filename:
            # Try to infer extension from filename, or append if not present
            if '.' in filename:
                file_extension = Path(filename).suffix
            elif not file_extension: # If filename has no extension and data type didn't suggest one
                file_extension = ".dat"
        elif source == "log":
            file_extension = ".log"
        elif source == "packet_capture":
            file_extension = ".pcap"
        elif source == "json":
            file_extension = ".json"

        content_bytes = data.encode('utf-8') if isinstance(data, str) else data

        try:
            file_path = await self._store_evidence_file(evidence_id, content_bytes, file_extension)
            file_hash = self._calculate_hash(file_path)

            metadata = {
                "id": evidence_id,
                "hash": file_hash,
                "timestamp": datetime.now().isoformat(),
                "source": source,
                "tags": tags if tags is not None else [],
                "file_path": str(file_path),
                "file_extension": file_extension,
                "size_bytes": len(content_bytes)
            }
            self.evidence_index[evidence_id] = metadata
            self.logger.info(f"Evidence stored successfully (ID: {evidence_id})", extra=metadata)
            return evidence_id
        except Exception as e:
            self.logger.error(f"Failed to store evidence: {e}", exc_info=True, extra={"source": source, "tags": tags})
            raise

    def get_evidence_metadata(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves metadata for a stored evidence by its ID.
        """
        metadata = self.evidence_index.get(evidence_id)
        if metadata:
            self.logger.debug(f"Retrieved metadata for evidence ID: {evidence_id}")
        else:
            self.logger.warning(f"Metadata not found for evidence ID: {evidence_id}")
        return metadata

    async def verify_evidence(self, evidence_id: str) -> bool:
        """
        Verifies the integrity of stored evidence by re-calculating its hash
        and comparing it with the stored hash.
        """
        metadata = self.get_evidence_metadata(evidence_id)
        if not metadata:
            self.logger.warning(f"Cannot verify evidence: ID {evidence_id} not found.")
            return False
        
        stored_hash = metadata.get("hash")
        file_path = Path(metadata.get("file_path", ""))

        if not file_path.exists():
            self.logger.error(f"Evidence file not found on disk for ID {evidence_id} at {file_path}.")
            return False
        
        try:
            current_hash = await asyncio.to_thread(self._calculate_hash, file_path)
            if current_hash == stored_hash:
                self.logger.info(f"Evidence integrity verified for ID {evidence_id}.", extra={"evidence_id": evidence_id, "status": "verified"})
                return True
            else:
                self.logger.warning(f"Evidence integrity check failed for ID {evidence_id}: hashes do not match.", extra={"evidence_id": evidence_id, "stored_hash": stored_hash, "current_hash": current_hash})
                return False
        except Exception as e:
            self.logger.error(f"Error during evidence integrity verification for ID {evidence_id}: {e}", exc_info=True)
            return False