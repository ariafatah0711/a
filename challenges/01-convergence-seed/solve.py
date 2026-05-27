#!/usr/bin/env python3
"""Solver for 01-convergence-seed.

Required env:
  RPC_URL     launcher RPC URL
  PRIVKEY     launcher-generated disposable private key
  SETUP_ADDR  launcher-generated setup address

Optional env:
  SECRET      bytes32 value, defaults to 0x...1337
"""

import os
import sys

from web3 import Web3


DEFAULT_SECRET = "0x" + ("0" * 60) + "1337"

SETUP_ABI = [
    {
        "inputs": [],
        "name": "challenge",
        "outputs": [{"internalType": "contract Challenge", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "isSolved",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
]

CHALLENGE_ABI = [
    {
        "inputs": [{"internalType": "bytes32", "name": "secret", "type": "bytes32"}],
        "name": "solve",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "solved",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        print(f"missing env: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def normalize_private_key(value: str) -> str:
    return value if value.startswith("0x") else f"0x{value}"


def parse_bytes32(value: str) -> bytes:
    raw = value[2:] if value.startswith("0x") else value
    if len(raw) != 64:
        raise ValueError("SECRET must be a bytes32 hex value")
    return bytes.fromhex(raw)


def send_tx(w3: Web3, account, tx):
    tx.setdefault("from", account.address)
    tx.setdefault("nonce", w3.eth.get_transaction_count(account.address))
    tx.setdefault("gas", 300_000)
    tx.setdefault("chainId", w3.eth.chain_id)

    dynamic_fee = (
        "maxFeePerGas" in tx
        or "maxPriorityFeePerGas" in tx
        or tx.get("type") in (2, "0x2")
    )
    if dynamic_fee:
        tx.pop("gasPrice", None)
    else:
        tx.setdefault("gasPrice", w3.eth.gas_price)

    signed = account.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    tx_hash = w3.eth.send_raw_transaction(raw)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status != 1:
        raise RuntimeError(f"transaction failed: {tx_hash.hex()}")
    return receipt


def main():
    rpc_url = require_env("RPC_URL")
    private_key = normalize_private_key(require_env("PRIVKEY"))
    setup_addr = Web3.to_checksum_address(require_env("SETUP_ADDR"))
    secret = parse_bytes32(os.getenv("SECRET", DEFAULT_SECRET).strip() or DEFAULT_SECRET)

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise RuntimeError(f"could not connect to RPC: {rpc_url}")

    account = w3.eth.account.from_key(private_key)
    player = Web3.to_checksum_address(account.address)
    setup = w3.eth.contract(address=setup_addr, abi=SETUP_ABI)
    challenge_addr = Web3.to_checksum_address(setup.functions.challenge().call())
    challenge = w3.eth.contract(address=challenge_addr, abi=CHALLENGE_ABI)

    print(f"rpc:       {rpc_url}")
    print(f"chain:     {w3.eth.chain_id}")
    print(f"player:    {player}")
    print(f"setup:     {setup_addr}")
    print(f"challenge: {challenge_addr}")

    if not challenge.functions.solved().call():
        receipt = send_tx(
            w3,
            account,
            challenge.functions.solve(secret).build_transaction({"from": player}),
        )
        print(f"solve tx:  {receipt.transactionHash.hex()}")

    solved = setup.functions.isSolved().call()
    print(f"solved:    {solved}")


if __name__ == "__main__":
    main()
