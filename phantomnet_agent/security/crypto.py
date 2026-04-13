# security/crypto.py
import hashlib
import hmac
import os
import logging
from typing import Union, Optional

logger = logging.getLogger(__name__)

def generate_key(length: int = 32) -> bytes:
    """Generates a cryptographically strong random key."""
    return os.urandom(length)

def hash_data(data: Union[str, bytes], algorithm: str = "sha256") -> str:
    """Hashes data using the specified algorithm."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    if algorithm == "sha256":
        return hashlib.sha256(data).hexdigest()
    elif algorithm == "md5":
        return hashlib.md5(data).hexdigest()
    else:
        raise ValueError(f"Unsupported hashing algorithm: {algorithm}")

def sign_data(data: Union[str, bytes], key: bytes) -> bytes:
    """
    Signs data using HMAC-SHA256.
    In a real-world scenario, this might involve asymmetric encryption (RSA, ECC).
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    signature = hmac.new(key, data, hashlib.sha256).digest()
    logger.debug("Data signed.")
    return signature

def verify_signature(data: Union[str, bytes], signature: bytes, key: bytes) -> bool:
    """
    Verifies a data signature using HMAC-SHA256.
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    expected_signature = hmac.new(key, data, hashlib.sha256).digest()
    is_valid = hmac.compare_digest(expected_signature, signature)
    if is_valid:
        logger.debug("Signature verified successfully.")
    else:
        logger.warning("Signature verification failed.")
    return is_valid

def encrypt_data(data: Union[str, bytes], key: bytes) -> bytes:
    """
    Encrypts data (placeholder - simplified AES-like encryption).
    For actual encryption, use a library like 'cryptography'.
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    # This is NOT a secure encryption implementation. It's a placeholder.
    # In a real system, use AES-GCM with a proper library.
    encrypted_data = bytes([d ^ k for d, k in zip(data, key * (len(data) // len(key) + 1))])
    logger.warning("Using a placeholder encryption method. Replace with a robust crypto library.")
    return encrypted_data

def decrypt_data(encrypted_data: bytes, key: bytes) -> bytes:
    """
    Decrypts data (placeholder - simplified AES-like decryption).
    """
    # This is NOT a secure decryption implementation. It's a placeholder.
    decrypted_data = bytes([d ^ k for d, k in zip(encrypted_data, key * (len(encrypted_data) // len(key) + 1))])
    return decrypted_data


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    # --- Hashing ---
    test_data = "This is some sensitive data."
    hashed_data = hash_data(test_data)
    print(f"Original data: {test_data}")
    print(f"SHA256 Hash: {hashed_data}")
    assert len(hashed_data) == 64 # SHA256 hexdigest is 64 chars

    # --- Signing and Verification ---
    signing_key = generate_key(16) # 16 bytes for HMAC-SHA256
    signature = sign_data(test_data, signing_key)
    print(f"Signature: {signature.hex()}")

    # Valid verification
    is_valid = verify_signature(test_data, signature, signing_key)
    print(f"Signature valid (expected True): {is_valid}")
    assert is_valid

    # Invalid verification (data changed)
    modified_data = "This is some sensitive data. (modified)"
    is_valid_modified = verify_signature(modified_data, signature, signing_key)
    print(f"Signature valid with modified data (expected False): {is_valid_modified}")
    assert not is_valid_modified

    # Invalid verification (key changed)
    wrong_key = generate_key(16)
    is_valid_wrong_key = verify_signature(test_data, signature, wrong_key)
    print(f"Signature valid with wrong key (expected False): {is_valid_wrong_key}")
    assert not is_valid_wrong_key

    # --- Simple Encryption/Decryption (Placeholder) ---
    encryption_key = generate_key(32)
    encrypted_payload = encrypt_data(test_data, encryption_key)
    print(f"Encrypted payload: {encrypted_payload.hex()}")
    decrypted_payload = decrypt_data(encrypted_payload, encryption_key)
    print(f"Decrypted payload: {decrypted_payload.decode('utf-8')}")
    assert decrypted_payload.decode('utf-8') == test_data

    try:
        hash_data("data", algorithm="unsupported")
    except ValueError as e:
        print(f"Caught expected error for unsupported algorithm: {e}")
