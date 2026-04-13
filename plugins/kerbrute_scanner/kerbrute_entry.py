# plugins/kerbrute_scanner/kerbrute_entry.py
import json
import time
import random


def run_kerbrute_scan(
    target_domain: str, usernames: list, passwords: list = None
) -> dict:
    """
    Simulates a Kerbrute-like scan for valid usernames or password spraying.
    """
    print(f"[{__name__}] Simulating Kerbrute scan on domain: {target_domain}")
    results = {
        "domain": target_domain,
        "valid_users": [],
        "invalid_users": [],
        "locked_out_users": [],
        "spray_attempts": [],
        "errors": [],
    }

    if not usernames:
        results["errors"].append("No usernames provided for scanning.")
        return results

    # Simulate username enumeration
    print(f"[{__name__}] Enumerating usernames...")
    for user in usernames:
        time.sleep(random.uniform(0.1, 0.5))  # Simulate network delay
        if random.random() < 0.7:  # 70% chance of user being valid
            results["valid_users"].append(user)
            print(f"[{__name__}] Found valid user: {user}")
        elif random.random() < 0.9:  # 20% chance of user being invalid
            results["invalid_users"].append(user)
        else:  # 10% chance of user being locked out during enumeration
            results["locked_out_users"].append(user)
            print(f"[{__name__}] User locked out during enumeration: {user}")

    # Simulate password spraying if passwords are provided
    if passwords and results["valid_users"]:
        print(f"[{__name__}] Performing password spraying on valid users...")
        for password in passwords:
            for user in results["valid_users"]:
                time.sleep(random.uniform(0.1, 0.3))  # Simulate network delay
                attempt = {"user": user, "password": password, "success": False}
                if random.random() < 0.05:  # 5% chance of successful spray
                    attempt["success"] = True
                    print(f"[{__name__}] Password spray successful: {user}:{password}")
                results["spray_attempts"].append(attempt)

    print(f"[{__name__}] Kerbrute scan simulation completed.")
    return results


if __name__ == "__main__":
    # Example usage for local testing
    test_domain = "example.com"
    test_usernames = ["jdoe", "admin", "guest", "svc_account", "baduser"]
    test_passwords = ["Summer2023!", "Password123", "P@$$w0rd"]

    print(f"--- Testing Kerbrute Scanner Plugin ---")
    scan_output = run_kerbrute_scan(test_domain, test_usernames, test_passwords)
    print(json.dumps(scan_output, indent=2))
    print("---------------------------------------")
