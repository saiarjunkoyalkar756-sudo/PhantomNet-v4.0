import time
from typing import Dict, Any
# from backend_api.blockchain_service.blockchain import Blockchain # Import Blockchain - REMOVED TOP-LEVEL IMPORT
from shared.database import get_db # Assuming get_db is the db_session_generator


class PhantomExchange:
    """
    Global platform for AI-driven threat intelligence and detection modules.
    Third-party developers earn rewards for validated contributions.
    """

    def __init__(self, db_session_generator: callable):
        self.developers = {}
        self.modules = {}
        self.validated_modules = set()
        self.db_session_generator = db_session_generator
        print("Initializing PhantomExchange (AI Threat Marketplace)...")

    def register_developer(self, developer_id: str):
        """
        Registers a new developer on the platform.
        """
        if developer_id not in self.developers:
            self.developers[developer_id] = {"reputation": 100, "submissions": []}
            print(f"Developer {developer_id} registered successfully.")
            return {"status": "success", "developer_id": developer_id}
        else:
            print(f"Developer {developer_id} is already registered.")
            return {"status": "error", "message": "Developer already registered"}

    def submit_module(self, developer_id: str, module_name: str, module_code: str):
        """
        Allows a registered developer to submit a new threat detection module.
        """
        if developer_id not in self.developers:
            print("Developer not registered. Please register first.")
            return {"status": "error", "message": "Developer not registered"}

        module_id = f"{developer_id}_{module_name}"
        self.modules[module_id] = {
            "code": module_code,
            "developer": developer_id,
            "validated": False,
        }
        self.developers[developer_id]["submissions"].append(module_id)
        print(f"Module {module_id} submitted successfully.")
        return {"status": "success", "module_id": module_id}

    async def validate_module(self, module_id: str): # Made async
        """
        Simulates the validation of a submitted module and records it on the PhantomChain.
        """
        if module_id not in self.modules:
            print("Module not found.")
            return {"status": "error", "message": "Module not found"}

        print(f"Validating module {module_id}...")
        await asyncio.sleep(1)  # Simulate validation time

        if self.modules[module_id]["code"]:
            self.modules[module_id]["validated"] = True
            self.validated_modules.add(module_id)
            developer_id = self.modules[module_id]["developer"]
            self.developers[developer_id]["reputation"] += 10
            print(f"Module {module_id} validated successfully.")

            # Add the validation event to the PhantomChain
            from backend_api.blockchain_service.blockchain import Blockchain # IMPORT MOVED HERE

            async with self.db_session_generator() as db:
                blockchain = Blockchain(db)
                transaction_data = {
                    "type": "module_validation",
                    "module_id": module_id,
                    "developer": developer_id,
                    "status": "validated",
                    "reputation_reward": 10,
                }
                last_block_obj = blockchain.last_block
                last_proof = (
                    last_block_obj.proof if last_block_obj else 0
                )
                previous_hash = (
                    blockchain.hash(last_block_obj.to_dict()) if last_block_obj else "1"
                )
                
                # Placeholder for proof of work
                proof = 123 # This would be calculated via PoW

                new_block_obj = blockchain.new_block(proof, previous_hash, transactions=[transaction_data])
                db.add(new_block_obj)
                await db.commit() # Needs to be awaited
                await db.refresh(new_block_obj) # Needs to be awaited

            return {"status": "success", "message": f"Module {module_id} validated and recorded on chain"}
        else:
            print(f"Module {module_id} validation failed.")
            return {"status": "error", "message": "Module validation failed"}
