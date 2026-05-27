#!/usr/bin/env python3
"""Solver for 02-convergence.

Required env:
  RPC_URL     launcher RPC URL
  PRIVKEY     launcher-generated disposable private key
  SETUP_ADDR  launcher-generated setup address

Example:
  export RPC_URL=http://localhost:8545
  export PRIVKEY=0x...
  export SETUP_ADDR=0x...
  python3 solve.py
"""

import os
import sys

from eth_abi import encode
from web3 import Web3


SETUP_ABI = [
    {
        "inputs": [],
        "name": "challenge",
        "outputs": [{"internalType": "contract Challenge", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes", "name": "agreement", "type": "bytes"}],
        "name": "bindPact",
        "outputs": [],
        "stateMutability": "nonpayable",
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
        "inputs": [],
        "name": "registerSeeker",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes", "name": "truth", "type": "bytes"}],
        "name": "transcend",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "ascended",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "", "type": "address"}],
        "name": "seekers",
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


def send_tx(w3: Web3, account, tx):
    tx.setdefault("from", account.address)
    tx.setdefault("nonce", w3.eth.get_transaction_count(account.address))
    tx.setdefault("gas", 1_500_000)
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


def build_truth(player: str) -> bytes:
    fragments = [(player, Web3.to_wei(100, "ether"), b"") for _ in range(10)]
    return encode(
        ["(address,uint256,bytes)[]", "bytes32", "uint32", "address", "address"],
        [fragments, b"\x00" * 32, 0, player, player],
    )


def main():
    rpc_url = require_env("RPC_URL")
    private_key = normalize_private_key(require_env("PRIVKEY"))
    setup_addr = Web3.to_checksum_address(require_env("SETUP_ADDR"))

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise RuntimeError(f"could not connect to RPC: {rpc_url}")

    account = w3.eth.account.from_key(private_key)
    player = Web3.to_checksum_address(account.address)

    print(f"rpc:      {rpc_url}")
    print(f"chain:    {w3.eth.chain_id}")
    print(f"player:   {player}")

    setup = w3.eth.contract(address=setup_addr, abi=SETUP_ABI)
    challenge_addr = Web3.to_checksum_address(setup.functions.challenge().call())
    challenge = w3.eth.contract(address=challenge_addr, abi=CHALLENGE_ABI)

    print(f"setup:    {setup_addr}")
    print(f"challenge:{challenge_addr}")

    if not challenge.functions.seekers(player).call():
        print("[*] registering seeker")
        receipt = send_tx(
            w3,
            account,
            challenge.functions.registerSeeker().build_transaction({"from": player}),
        )
        print(f"register tx: {receipt.transactionHash.hex()}")

    truth = build_truth(player)

    print("[*] binding pact")
    receipt = send_tx(
        w3,
        account,
        setup.functions.bindPact(truth).build_transaction({"from": player}),
    )
    print(f"bind tx: {receipt.transactionHash.hex()}")

    print("[*] transcending")
    receipt = send_tx(
        w3,
        account,
        challenge.functions.transcend(truth).build_transaction({"from": player}),
    )
    print(f"transcend tx: {receipt.transactionHash.hex()}")

    solved = setup.functions.isSolved().call()
    ascended = challenge.functions.ascended().call()
    print(f"ascended: {ascended}")
    print(f"solved:   {solved}")


if __name__ == "__main__":
    main()
