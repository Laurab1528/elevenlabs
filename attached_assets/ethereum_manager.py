from web3 import Web3
from typing import Tuple
from datetime import datetime
import os

class EthereumManager:
    def __init__(self):
        # Connect to Sepolia testnet using environment variable
        infura_project_id = os.getenv("INFURA_PROJECT_ID")
        if not infura_project_id:
            raise ValueError("INFURA_PROJECT_ID environment variable not set")

        self.w3 = Web3(Web3.HTTPProvider(f'https://sepolia.infura.io/v3/{infura_project_id}'))
        self.configured_wallet = None
        self.private_key = None

    def configure_wallet(self, wallet_address: str, private_key: str):
        """Configure the wallet for transactions"""
        self.configured_wallet = wallet_address
        self.private_key = private_key

    def check_balance(self, address: str) -> float:
        """Check the balance of an Ethereum address"""
        try:
            if not Web3.is_address(address):
                raise ValueError("Invalid Ethereum address")

            balance_wei = self.w3.eth.get_balance(address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            return float(balance_eth)
        except Exception as e:
            raise Exception(f"Error checking balance: {str(e)}")

    def transfer_eth(self, from_address: str, to_address: str, amount: float) -> Tuple[bool, str]:
        """Transfer ETH from one address to another on Sepolia testnet"""
        try:
            if not self.private_key:
                return False, "Wallet not configured"

            if not Web3.is_address(from_address) or not Web3.is_address(to_address):
                return False, "Invalid Ethereum address"

            # Convert ETH to Wei
            amount_wei = self.w3.to_wei(amount, 'ether')

            # Get the nonce (transaction count)
            nonce = self.w3.eth.get_transaction_count(from_address)

            # Check balance
            balance = self.check_balance(from_address)
            if balance < amount:
                return False, f"Insufficient balance. Available: {balance} ETH"

            # Estimate gas
            gas_price = self.w3.eth.gas_price
            gas_limit = 21000  # Standard ETH transfer gas limit

            # Build transaction
            transaction = {
                'nonce': nonce,
                'to': to_address,
                'value': amount_wei,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': 11155111  # Sepolia chain ID
            }

            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)

            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            return True, f"Transaction successful. Hash: {receipt['transactionHash'].hex()}"

        except Exception as e:
            return False, f"Transaction failed: {str(e)}"

eth_manager = EthereumManager()