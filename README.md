# NXBCL Challenge Repository

This repository contains only blockchain challenge source files. NXBCL owns the shared Anvil runtime, RPC proxy, deploy scripts, credentials, and metadata generation.

Preferred layout:

```text
challenges/
  01-convergence-seed/
    challenge.yml
    contracts/
      Challenge.sol
      ChallengeFactory.sol
      Setup.sol
    foundry.toml
    solve.py
    README.md
  02-convergence/
    challenge.yml
    contracts/
    foundry.toml
    solve.py
    README.md
```

Do not include runtime infrastructure in this repo:

```text
docker-compose.yml
scripts/deploy_one.sh
scripts/rpc_proxy.py
metadata/
artifacts/
```

Those files are generated or managed by the NXBCL launcher.

## Challenge Contract Shape

Each challenge should provide a factory contract with:

```solidity
function spawnFor(address player) external returns (address setup);
```

The launcher deploys one factory per challenge, creates a disposable wallet per participant, funds it, calls `spawnFor(player)`, and returns:

```text
RPC_URL
PRIVKEY
SETUP_ADDR
```

The setup contract should expose:

```solidity
function isSolved() external view returns (bool);
```

Flags must stay in the launcher/backend. Do not put real flags in contracts, public scripts, or `challenge.yml`.

## `challenge.yml`

Minimal example:

```yaml
id: 01-convergence-seed
name: Convergence Seed
kind: blockchain_rpc
factory_contract: contracts/ChallengeFactory.sol:ChallengeFactory
setup_contract: contracts/Setup.sol:Setup
spawn_function: spawnFor(address)
checker: Setup.isSolved()
```

If omitted, NXBCL defaults to:

```text
factory_contract = contracts/ChallengeFactory.sol:ChallengeFactory
setup_contract   = contracts/Setup.sol:Setup
spawn_function   = spawnFor(address)
checker          = Setup.isSolved()
```

## Local Solver

Solvers should consume launcher-provided environment variables:

```bash
export RPC_URL=http://localhost:8545
export PRIVKEY=0x...
export SETUP_ADDR=0x...
python3 solve.py
```
