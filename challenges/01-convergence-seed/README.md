# Convergence Seed

Small launcher-compatible EVM challenge.

The launcher deploys `ChallengeFactory`, generates a disposable wallet, then calls:

```solidity
spawnFor(address player)
```

That creates a private `Setup` instance for the player. The player receives:

```text
RPC_URL
PRIVKEY
SETUP_ADDR
```

Solve locally after launch:

```bash
export RPC_URL=http://localhost:8545
export PRIVKEY=0x...
export SETUP_ADDR=0x...
python3 solve.py
```

The backend should only return the flag after `Setup.isSolved()` returns `true` for the user's stored setup instance.
