from web3 import Web3
from solcx import compile_source, install_solc
import json


class Blockchain:
    def __init__(self, db):
        self.db = db
        self.w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
        self.contract = self._deploy_contract()

    def _deploy_contract(self):
        install_solc("0.8.0")
        with open("backend_api/blockchain_service/AuditTrail.sol", "r") as f:
            source = f.read()
        compiled_sol = compile_source(source)
        contract_interface = compiled_sol["<stdin>:AuditTrail"]
        contract = self.w3.eth.contract(
            abi=contract_interface["abi"], bytecode=contract_interface["bin"]
        )
        tx_hash = contract.constructor().transact({"from": self.w3.eth.accounts[0]})
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return self.w3.eth.contract(
            address=tx_receipt.contractAddress, abi=contract_interface["abi"]
        )

    def add_event(self, data: str):
        tx_hash = self.contract.functions.addEvent(data).transact(
            {"from": self.w3.eth.accounts[0]}
        )
        self.w3.eth.wait_for_transaction_receipt(tx_hash)

    def get_events(self):
        return self.contract.functions.events().call()
