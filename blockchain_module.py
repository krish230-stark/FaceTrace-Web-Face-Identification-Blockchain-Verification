import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("SEPOLIA_RPC_URL")
PRIVATE_KEY = os.getenv("SEPOLIA_PRIVATE_KEY")

CONTRACT_ADDRESS = "0xc0d6300826d9da999f57fd55812846c027e9e05f"

CONTRACT_ABI = [
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "fingerprint",
                "type": "bytes32"
            }
        ],
        "name": "registerPost",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "fingerprint",
                "type": "bytes32"
            }
        ],
        "name": "verifyPost",
        "outputs": [
            {
                "internalType": "bool",
                "name": "verified",
                "type": "bool"
            },
            {
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            },
            {
                "internalType": "address",
                "name": "uploader",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

w3 = Web3(Web3.HTTPProvider(RPC_URL))

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=CONTRACT_ABI
)


def register_hash(fingerprint_hex):
    fingerprint = bytes.fromhex(fingerprint_hex.replace("0x", ""))

    account = w3.eth.account.from_key(PRIVATE_KEY)

    nonce = w3.eth.get_transaction_count(account.address)

    transaction = contract.functions.registerPost(
        fingerprint
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "chainId": 11155111,
        "gas": 200000,
        "maxFeePerGas": w3.to_wei(30, "gwei"),
        "maxPriorityFeePerGas": w3.to_wei(2, "gwei"),
    })

    signed_transaction = account.sign_transaction(transaction)

    tx_hash = w3.eth.send_raw_transaction(
        signed_transaction.raw_transaction
    )

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return receipt.transactionHash.hex()


def verify_hash(fingerprint_hex):
    fingerprint = bytes.fromhex(fingerprint_hex.replace("0x", ""))

    verified, timestamp, uploader = contract.functions.verifyPost(
        fingerprint
    ).call()

    return {
        "verified": verified,
        "timestamp": timestamp,
        "uploader": uploader,
    }