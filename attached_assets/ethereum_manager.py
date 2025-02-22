from web3 import Web3
from typing import Tuple
from datetime import datetime

class EthereumManager:
    def __init__(self):
        # For testing purposes, we'll use Sepolia testnet
        self.w3 = Web3(Web3.HTTPProvider('https://eth-sepolia.g.alchemy.com/v2/demo'))
        self.configured_wallet = None
        self.private_key = None

        # Simulated balances for demo
        self.demo_balances = {
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e": 5.0,  # Admin wallet
            "0x941C3C374f856C6e86c44F929491338B": 0.1,         # Alice's wallet
            "0xA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6": 0.2          # Bob's wallet
        }

    def configure_wallet(self, wallet_address: str, private_key: str):
        """Configure the wallet for transactions"""
        self.configured_wallet = wallet_address
        self.private_key = private_key

    def check_balance(self, address: str) -> float:
        """Check the balance of an Ethereum address"""
        try:
            # For demo, return simulated balance
            return self.demo_balances.get(address, 0.0)
        except Exception as e:
            raise Exception(f"Error checking balance: {str(e)}")

    def transfer_eth(self, from_address: str, to_address: str, amount: float) -> Tuple[bool, str]:
        """Transfer ETH from one address to another"""
        try:
            # Check if sender has sufficient balance
            sender_balance = self.check_balance(from_address)
            if sender_balance < amount:
                return False, f"Insufficient balance. Available: {sender_balance} ETH"

            # Update simulated balances
            self.demo_balances[from_address] = sender_balance - amount
            self.demo_balances[to_address] = self.demo_balances.get(to_address, 0.0) + amount

            # Simulate successful transaction
            return True, f"Successfully transferred {amount} ETH"

        except Exception as e:
            return False, str(e)

eth_manager = EthereumManager()