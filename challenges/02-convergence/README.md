# Convergence

Full Convergence challenge adapted for the NXBCL launcher flow.

The important launcher contract shape is:

```solidity
function spawnFor(address player) external returns (address setup);
```

The backend should call `spawnFor()` from the factory owner/deployer key, store the returned setup address for the current user and challenge, then return this to the player:

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

The flag must remain in the launcher/backend. The on-chain check is only:

```solidity
Setup.isSolved()
```
