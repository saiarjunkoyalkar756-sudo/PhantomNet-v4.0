# backend_api/shared/merkle.py
import hashlib
import json
from typing import List, Any

def _hash_data(data: Any) -> str:
    """
    Serializes data to a consistent JSON string and returns its SHA-256 hash.
    """
    # Use sort_keys=True to ensure the JSON string is always the same for the same data
    serialized_data = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(serialized_data).hexdigest()

def build_merkle_tree(data_list: List[Any]) -> List[List[str]]:
    """
    Constructs a Merkle tree from a list of data items.
    Returns the full tree (a list of lists representing levels).
    """
    if not data_list:
        return [[]]

    # 1. Hash the initial data blocks (leaves)
    leaves = [_hash_data(item) for item in data_list]
    
    # If there's an odd number of leaves, duplicate the last one
    if len(leaves) % 2 == 1:
        leaves.append(leaves[-1])
        
    tree = [leaves]
    current_level = leaves

    # 2. Build the tree level by level
    while len(current_level) > 1:
        next_level = []
        # Combine pairs of hashes to create the next level
        for i in range(0, len(current_level), 2):
            pair_hash = _hash_data(current_level[i] + current_level[i+1])
            next_level.append(pair_hash)
            
        # If the new level is odd, duplicate the last hash
        if len(next_level) % 2 == 1 and len(next_level) > 1:
            next_level.append(next_level[-1])
            
        tree.append(next_level)
        current_level = next_level

    return tree

def get_merkle_root(data_list: List[Any]) -> str:
    """
    Calculates the Merkle root for a list of data items.
    """
    if not data_list:
        return _hash_data("") # Return hash of an empty string for empty list

    tree = build_merkle_tree(data_list)
    # The root is the single hash at the top level of the tree
    return tree[-1][0]

# Example Usage
if __name__ == "__main__":
    # Some example audit logs
    audit_logs = [
        {"action": "isolate_host", "target": "host-123", "timestamp": "2025-12-13T10:00:00Z"},
        {"action": "block_ip", "target": "1.2.3.4", "timestamp": "2025-12-13T10:01:00Z"},
        {"action": "create_ticket", "ticket_id": "INC-001", "timestamp": "2025-12-13T10:02:00Z"},
        {"action": "notify_user", "user": "admin", "timestamp": "2025-12-13T10:03:00Z"},
    ]

    root = get_merkle_root(audit_logs)
    print(f"Audit Logs: {json.dumps(audit_logs, indent=2)}")
    print(f"\nMerkle Root: {root}")

    # --- Verification Example ---
    # To prove 'log_to_verify' was part of the batch, you only need the log itself
    # and a "proof" (the sibling hashes up to the root).
    
    log_to_verify = audit_logs[1] # The "block_ip" action
    hashed_log = _hash_data(log_to_verify)
    print(f"\nVerifying log: {log_to_verify}")
    print(f"Its hash: {hashed_log}")

    # The proof would be constructed by the service and sent to the verifier.
    # Here, we simulate getting it from the generated tree.
    tree = build_merkle_tree(audit_logs)
    proof = [
        tree[0][0], # Hash of the first log
        tree[1][1]  # Hash of the second pair in the second level
    ]
    print(f"Proof (sibling hashes): {proof}")

    # The verifier reconstructs the root
    # 1. Hash the log with its sibling
    reconstructed_hash_level_1 = _hash_data(proof[0] + hashed_log)
    # 2. Hash that result with the next sibling in the proof
    reconstructed_root = _hash_data(reconstructed_hash_level_1 + proof[1])

    print(f"Reconstructed Root: {reconstructed_root}")
    print(f"Original Root:      {root}")
    print(f"\nVerification Successful: {reconstructed_root == root}")
