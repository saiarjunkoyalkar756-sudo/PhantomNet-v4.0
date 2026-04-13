# security/integrity.py
import hashlib
import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)

def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> Union[str, None]:
    """
    Calculates the hash of a given file.
    Returns None if the file does not exist or an error occurs.
    """
    if not file_path.is_file():
        logger.warning(f"File not found for hash calculation: {file_path}")
        return None

    try:
        hasher = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            while chunk := f.read(4096):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return None

def verify_file_integrity(file_path: Path, expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verifies the integrity of a file by comparing its calculated hash
    with an expected hash value.
    """
    actual_hash = calculate_file_hash(file_path, algorithm)
    if actual_hash is None:
        return False
    
    if actual_hash == expected_hash:
        logger.info(f"Integrity check passed for {file_path}")
        return True
    else:
        logger.warning(f"Integrity check FAILED for {file_path}. Expected: {expected_hash}, Actual: {actual_hash}")
        return False

def verify_config_signature(config_path: Path, signature_path: Path, public_key_path: Path) -> bool:
    """
    Verifies the digital signature of a configuration file.
    This is a placeholder as it requires a robust PKI implementation.
    """
    logger.warning("Configuration signature verification is a placeholder. Real implementation needed.")
    if not config_path.is_file():
        logger.error(f"Config file not found for signature verification: {config_path}")
        return False
    if not signature_path.is_file():
        logger.error(f"Signature file not found for signature verification: {signature_path}")
        return False
    if not public_key_path.is_file():
        logger.error(f"Public key file not found for signature verification: {public_key_path}")
        return False
    
    # In a real system, you would:
    # 1. Load the public key.
    # 2. Read the config file content.
    # 3. Read the signature.
    # 4. Use a cryptographic library (e.g., cryptography) to verify the signature
    #    of the config content using the public key and the signature.

    logger.info(f"Simulating signature verification for {config_path}. Assuming valid for now.")
    return True # Simulate success for placeholder

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    # --- File Hash Calculation ---
    test_file_path = Path("test_integrity.txt")
    test_file_path.write_text("This is some content for integrity check.")

    calculated_hash = calculate_file_hash(test_file_path)
    print(f"Calculated hash for '{test_file_path}': {calculated_hash}")
    
    # --- File Integrity Verification ---
    expected_hash = calculate_file_hash(test_file_path) # Get the correct hash
    print(f"Verifying integrity with correct hash: {verify_file_integrity(test_file_path, expected_hash)}")
    assert verify_file_integrity(test_file_path, expected_hash)

    wrong_hash = "a" * 64
    print(f"Verifying integrity with incorrect hash: {verify_file_integrity(test_file_path, wrong_hash)}")
    assert not verify_file_integrity(test_file_path, wrong_hash)

    # --- Config Signature Verification (Placeholder) ---
    dummy_config_path = Path("dummy_config.yml")
    dummy_config_path.write_text("agent:\n  id: test")
    dummy_signature_path = Path("dummy_config.sig")
    dummy_signature_path.write_text("fake_signature")
    dummy_public_key_path = Path("dummy_public.pem")
    dummy_public_key_path.write_text("fake_public_key")

    print(f"Verifying config signature (placeholder): {verify_config_signature(dummy_config_path, dummy_signature_path, dummy_public_key_path)}")
    assert verify_config_signature(dummy_config_path, dummy_signature_path, dummy_public_key_path)

    # Clean up
    test_file_path.unlink()
    dummy_config_path.unlink()
    dummy_signature_path.unlink()
    dummy_public_key_path.unlink()
