from web3 import Web3
import json
import os
from eth_account import Account
import secrets

# Connect to EduChain (replace with your node URL)
EDUCHAIN_URL = os.getenv("EDUCHAIN_URL", "http://localhost:8545")
w3 = Web3(Web3.HTTPProvider(EDUCHAIN_URL))

# Contract ABIs (replace with your actual contract ABIs)
RENTAL_AGREEMENT_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "address", "name": "renter", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "uint256", "name": "duration", "type": "uint256"}
        ],
        "name": "createAgreement",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

ESCROW_PAYMENT_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "recipient", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "releasePayment",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

REVIEW_SYSTEM_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "propertyId", "type": "string"},
            {"internalType": "uint256", "name": "rating", "type": "uint256"},
            {"internalType": "string", "name": "comment", "type": "string"}
        ],
        "name": "submitReview",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def create_wallet():
    """Create a new Ethereum wallet."""
    # Generate a random private key
    private_key = "0x" + secrets.token_hex(32)
    account = Account.from_key(private_key)
    
    return {
        "address": account.address,
        "private_key": private_key
    }

def get_wallet_balance(address):
    """Get the balance of a wallet in ETH."""
    try:
        balance_wei = w3.eth.get_balance(address)
        return w3.from_wei(balance_wei, 'ether')
    except Exception as e:
        print(f"Error getting wallet balance: {e}")
        return 0

def send_transaction(private_key, recipient, amount):
    """Send ETH from one address to another."""
    try:
        # Convert amount to Wei
        amount_wei = w3.to_wei(amount, 'ether')
        
        # Get the nonce
        account = Account.from_key(private_key)
        nonce = w3.eth.get_transaction_count(account.address)
        
        # Build transaction
        transaction = {
            'nonce': nonce,
            'to': recipient,
            'value': amount_wei,
            'gas': 21000,
            'gasPrice': w3.eth.gas_price
        }
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            "success": True,
            "transaction_hash": receipt['transactionHash'].hex()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def create_rental_agreement(owner_address, renter_address, amount, duration):
    """Create a rental agreement on the blockchain."""
    try:
        # Load contract
        contract_address = os.getenv("RENTAL_AGREEMENT_CONTRACT")
        contract = w3.eth.contract(address=contract_address, abi=RENTAL_AGREEMENT_ABI)
        
        # Convert amount to Wei
        amount_wei = w3.to_wei(amount, 'ether')
        
        # Create transaction
        transaction = contract.functions.createAgreement(
            owner_address,
            renter_address,
            amount_wei,
            duration
        ).build_transaction({
            'from': owner_address,
            'nonce': w3.eth.get_transaction_count(owner_address),
            'gas': 200000,
            'gasPrice': w3.eth.gas_price
        })
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            "success": True,
            "contract_address": receipt['contractAddress'],
            "transaction_hash": receipt['transactionHash'].hex()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def process_escrow_payment(escrow_address, amount):
    """Process a payment through the escrow contract."""
    try:
        # Load contract
        contract = w3.eth.contract(address=escrow_address, abi=ESCROW_PAYMENT_ABI)
        
        # Convert amount to Wei
        amount_wei = w3.to_wei(amount, 'ether')
        
        # Create transaction
        transaction = contract.functions.deposit().build_transaction({
            'from': w3.eth.accounts[0],
            'value': amount_wei,
            'nonce': w3.eth.get_transaction_count(w3.eth.accounts[0]),
            'gas': 100000,
            'gasPrice': w3.eth.gas_price
        })
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            "success": True,
            "transaction_hash": receipt['transactionHash'].hex()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def release_escrow_payment(escrow_address, recipient, amount):
    """Release a payment from the escrow contract."""
    try:
        # Load contract
        contract = w3.eth.contract(address=escrow_address, abi=ESCROW_PAYMENT_ABI)
        
        # Convert amount to Wei
        amount_wei = w3.to_wei(amount, 'ether')
        
        # Create transaction
        transaction = contract.functions.releasePayment(
            recipient,
            amount_wei
        ).build_transaction({
            'from': w3.eth.accounts[0],
            'nonce': w3.eth.get_transaction_count(w3.eth.accounts[0]),
            'gas': 100000,
            'gasPrice': w3.eth.gas_price
        })
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            "success": True,
            "transaction_hash": receipt['transactionHash'].hex()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def submit_review_to_blockchain(property_id, rating, comment):
    """Submit a review to the blockchain."""
    try:
        # Load contract
        contract_address = os.getenv("REVIEW_SYSTEM_CONTRACT")
        contract = w3.eth.contract(address=contract_address, abi=REVIEW_SYSTEM_ABI)
        
        # Create transaction
        transaction = contract.functions.submitReview(
            property_id,
            rating,
            comment
        ).build_transaction({
            'from': w3.eth.accounts[0],
            'nonce': w3.eth.get_transaction_count(w3.eth.accounts[0]),
            'gas': 200000,
            'gasPrice': w3.eth.gas_price
        })
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            "success": True,
            "transaction_hash": receipt['transactionHash'].hex()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        } 