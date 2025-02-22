from web3 import Web3
from typing import Tuple

class EthereumManager:
    def __init__(self):
        # For testing purposes, we'll use Sepolia testnet
        self.w3 = Web3(Web3.HTTPProvider('https://eth-sepolia.g.alchemy.com/v2/demo'))
        self.configured_wallet = None
        self.private_key = None

    def configure_wallet(self, wallet_address: str, private_key: str):
        """Configure the wallet for transactions"""
        self.configured_wallet = wallet_address
        self.private_key = private_key

    def check_balance(self, address: str) -> float:
        """Check the balance of an Ethereum address"""
        try:
            balance = self.w3.eth.get_balance(address)
            return self.w3.from_wei(balance, 'ether')
        except Exception as e:
            raise Exception(f"Error checking balance: {str(e)}")

    def transfer_eth(self, from_address: str, to_address: str, amount: float) -> Tuple[bool, str]:
        """Transfer ETH from one address to another"""
        try:
            # For demo purposes, we'll simulate a successful transaction
            # In production, you would:
            # 1. Get nonce
            # 2. Build transaction
            # 3. Sign with private key
            # 4. Send transaction
            # 5. Wait for confirmation

            # Simulated successful transaction
            return True, "Transaction successful (Demo Mode)"

            # Production code would look like this:
            """
            nonce = self.w3.eth.get_transaction_count(from_address)
            transaction = {
                'nonce': nonce,
                'to': to_address,
                'value': self.w3.to_wei(amount, 'ether'),
                'gas': 21000,
                'gasPrice': self.w3.eth.gas_price
            }

            signed_txn = self.w3.eth.account.sign_transaction(
                transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            return True, receipt.transactionHash.hex()
            """
        except Exception as e:
            return False, str(e)

eth_manager = EthereumManager()