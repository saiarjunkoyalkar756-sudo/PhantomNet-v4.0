# phantomnet_agent/self_healing_ai/patch_manager.py

import logging
import os
import hashlib
import shutil
import asyncio
import httpx # For downloading patches
from datetime import datetime # Import datetime
from typing import Dict, Any, Optional, Tuple

from utils.logger import get_logger
from shared.platform_utils import SAFE_MODE

logger = get_logger(__name__)

class PatchManager:
    """
    Manages downloading, validating, applying, and rolling back patches for agent components.
    """
    def __init__(self, patch_storage_dir: str = "patches"):
        self.patch_storage_dir = patch_storage_dir
        os.makedirs(self.patch_storage_dir, exist_ok=True)
        self.safe_mode = SAFE_MODE

    async def _download_patch(self, patch_url: str, patch_id: str) -> Optional[str]:
        """Downloads a patch file from a given URL."""
        if self.safe_mode:
            logger.warning(f"SAFE_MODE: Skipping patch download from {patch_url}.")
            return None

        local_path = os.path.join(self.patch_storage_dir, f"{patch_id}.zip") # Assuming zip for now
        logger.info(f"Downloading patch {patch_id} from {patch_url} to {local_path}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(patch_url, timeout=30.0)
                response.raise_for_status()
                with open(local_path, "wb") as f:
                    f.write(response.content)
            logger.info(f"Patch {patch_id} downloaded successfully.")
            return local_path
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to download patch {patch_id} - HTTP Error: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Failed to download patch {patch_id} - Network Error: {e}")
            return None

    def _validate_patch(self, patch_path: str, expected_hash: str) -> bool:
        """Validates a downloaded patch file against its expected hash."""
        logger.info(f"Validating patch file: {patch_path}")
        if not os.path.exists(patch_path):
            logger.error(f"Patch file not found for validation: {patch_path}")
            return False
        
        try:
            with open(patch_path, "rb") as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
            
            if current_hash == expected_hash:
                logger.info(f"Patch {os.path.basename(patch_path)} validation successful.")
                return True
            else:
                logger.error(f"Patch {os.path.basename(patch_path)} hash mismatch. Expected: {expected_hash}, Got: {current_hash}")
                return False
        except Exception as e:
            logger.error(f"Error validating patch {patch_path}: {e}")
            return False

    async def _apply_patch(self, patch_path: str, target_dir: str, backup_dir: Optional[str] = None) -> bool:
        """Applies a patch (e.g., extracts a zip file) to the target directory."""
        if self.safe_mode:
            logger.warning(f"SAFE_MODE: Skipping patch application to {target_dir}.")
            return False

        logger.info(f"Applying patch {patch_path} to {target_dir}")
        try:
            # Create backup if specified
            if backup_dir:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                backup_path_full = os.path.join(backup_dir, f"backup_{timestamp}_{os.path.basename(target_dir)}")
                logger.info(f"Creating backup of {target_dir} to {backup_path_full}")
                shutil.copytree(target_dir, backup_path_full, dirs_exist_ok=True) # copytree to preserve metadata
            
            # Assuming patch is a zip file containing files to extract
            shutil.unpack_archive(patch_path, target_dir, 'zip')
            logger.info(f"Patch {os.path.basename(patch_path)} applied successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to apply patch {patch_path} to {target_dir}: {e}")
            return False

    async def _rollback_patch(self, backup_path: str, target_dir: str) -> bool:
        """Rolls back a patch by restoring from a backup."""
        if self.safe_mode:
            logger.warning(f"SAFE_MODE: Skipping patch rollback from {backup_path}.")
            return False

        logger.info(f"Rolling back changes in {target_dir} from backup {backup_path}")
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Backup not found for rollback: {backup_path}")
                return False
            
            # Remove current (potentially broken) state
            shutil.rmtree(target_dir)
            # Restore from backup
            shutil.copytree(backup_path, target_dir)
            logger.info("Patch rollback successful.")
            return True
        except Exception as e:
            logger.error(f"Failed to rollback patch from {backup_path} to {target_dir}: {e}")
            return False

    async def process_patch(self, patch_info: Dict[str, Any], target_dir: str, backup_dir: Optional[str] = None) -> Tuple[bool, str]:
        """
        Main function to orchestrate downloading, validating, and applying a patch.
        Returns (success: bool, status_message: str).
        """
        patch_id = patch_info.get("id")
        patch_url = patch_info.get("url")
        expected_hash = patch_info.get("hash")

        if not all([patch_id, patch_url, expected_hash]):
            return False, "Invalid patch_info provided (missing id, url, or hash)."

        logger.info(f"Processing patch {patch_id}...")

        # 1. Download
        downloaded_path = await self._download_patch(patch_url, patch_id)
        if not downloaded_path:
            return False, f"Failed to download patch {patch_id}."

        # 2. Validate
        if not self._validate_patch(downloaded_path, expected_hash):
            return False, f"Patch {patch_id} failed validation."

        # 3. Apply
        if not await self._apply_patch(downloaded_path, target_dir, backup_dir):
            return False, f"Failed to apply patch {patch_id}."
        
        logger.info(f"Patch {patch_id} successfully applied.")
        return True, "Patch applied successfully."

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running PatchManager example...")
    
    manager = PatchManager()

    async def run_example():
        # Create a dummy target directory
        dummy_target_dir = "temp_agent_code"
        os.makedirs(dummy_target_dir, exist_ok=True)
        with open(os.path.join(dummy_target_dir, "old_file.txt"), "w") as f:
            f.write("Old content")
        
        # Simulate a patch info (would come from backend)
        # Create a dummy zip file
        dummy_patch_zip = "test_patch.zip"
        with zipfile.ZipFile(dummy_patch_zip, 'w') as zf:
            zf.writestr("new_file.txt", "New content from patch")
            zf.writestr("old_file.txt", "Updated old content")
        
        # Calculate its hash
        with open(dummy_patch_zip, "rb") as f:
            dummy_patch_hash = hashlib.sha256(f.read()).hexdigest()

        patch_info = {
            "id": "patch_123",
            "url": "file://" + os.path.abspath(dummy_patch_zip), # Use file:// for local test
            "hash": dummy_patch_hash,
        }
        
        # Test downloading from a local file path using httpx and file:// schema
        # (This won't work with httpx as it expects HTTP/HTTPS. A real scenario would use a web server.)
        # For a truly local test, you'd directly extract or copy.
        # Let's mock download for this example:
        mock_download_path = os.path.join(manager.patch_storage_dir, "patch_123.zip")
        shutil.copy(dummy_patch_zip, mock_download_path)

        with patch('phantomnet_agent.self_healing_ai.patch_manager.PatchManager._download_patch', AsyncMock(return_value=mock_download_path)):
            success, message = await manager.process_patch(patch_info, dummy_target_dir, "temp_backup")
            print(f"\nPatch Process Result - Success: {success}, Message: {message}")
            if success:
                print(f"Old file content after patch: {open(os.path.join(dummy_target_dir, 'old_file.txt')).read()}")
                print(f"New file content after patch: {open(os.path.join(dummy_target_dir, 'new_file.txt')).read()}")

            # Test rollback (conceptual)
            if success and os.path.exists("temp_backup"):
                print("\nAttempting rollback...")
                rollback_success = await manager._rollback_patch("temp_backup", dummy_target_dir)
                print(f"Rollback Result - Success: {rollback_success}")
                if rollback_success:
                    print(f"Old file content after rollback: {open(os.path.join(dummy_target_dir, 'old_file.txt')).read()}")
        
        # Cleanup
        shutil.rmtree(dummy_target_dir, ignore_errors=True)
        shutil.rmtree("temp_backup", ignore_errors=True)
        os.remove(dummy_patch_zip)


    # Mock zipfile for direct local testing (as httpx file:// won't work as expected)
    import zipfile
    with patch('shutil.unpack_archive') as mock_unpack:
        try:
            asyncio.run(run_example())
        except KeyboardInterrupt:
            logger.info("PatchManager example stopped.")
