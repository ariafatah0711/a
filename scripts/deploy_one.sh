#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: sh scripts/deploy_one.sh <challenge_id>" >&2
  exit 1
fi

CHALLENGE_ID="$1"
CHALLENGE_DIR="challenges/${CHALLENGE_ID}"
RPC_URL="${RPC_URL:-http://anvil:8545}"
PUBLIC_RPC_URL="${PUBLIC_RPC_URL:-http://localhost:8545}"
RPC_PORT="${RPC_PORT:-8545}"
CHAIN_ID="${CHAIN_ID:-31337}"
DEPLOYER_PRIVATE_KEY="${DEPLOYER_PRIVATE_KEY:-}"

if [ -z "$DEPLOYER_PRIVATE_KEY" ]; then
  echo "DEPLOYER_PRIVATE_KEY is required" >&2
  exit 1
fi

if [ ! -f "${CHALLENGE_DIR}/challenge.yml" ]; then
  echo "challenge not found: ${CHALLENGE_ID}" >&2
  exit 1
fi

yml_value() {
  sed -n "s/^[[:space:]]*$1:[[:space:]]*//p" "${CHALLENGE_DIR}/challenge.yml" \
    | head -n 1 \
    | tr -d '\r"'
}

FACTORY_CONTRACT="$(yml_value factory_contract)"
SETUP_CONTRACT="$(yml_value setup_contract)"
SPAWN_FUNCTION="$(yml_value spawn_function)"
CHECKER="$(yml_value checker)"

FACTORY_CONTRACT="${FACTORY_CONTRACT:-contracts/ChallengeFactory.sol:ChallengeFactory}"
SETUP_CONTRACT="${SETUP_CONTRACT:-contracts/Setup.sol:Setup}"
SPAWN_FUNCTION="${SPAWN_FUNCTION:-spawnFor(address)}"
CHECKER="${CHECKER:-Setup.isSolved()}"

OUT_DIR="$(pwd)/metadata/challenges/${CHALLENGE_ID}"
ARTIFACTS_DIR="${OUT_DIR}/artifacts"

mkdir -p "$ARTIFACTS_DIR"

echo "[deploy:${CHALLENGE_ID}] waiting for RPC at ${RPC_URL}"
i=0
until cast chain-id --rpc-url "$RPC_URL" >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -gt 60 ]; then
    echo "[deploy:${CHALLENGE_ID}] RPC did not become ready" >&2
    exit 1
  fi
  sleep 1
done

echo "[deploy:${CHALLENGE_ID}] building"
(
  cd "$CHALLENGE_DIR"
  forge build
  forge inspect "$FACTORY_CONTRACT" abi > "${ARTIFACTS_DIR}/ChallengeFactory.abi.json"
  forge inspect "$SETUP_CONTRACT" abi > "${ARTIFACTS_DIR}/Setup.abi.json"
)

echo "[deploy:${CHALLENGE_ID}] deploying ${FACTORY_CONTRACT}"
DEPLOY_OUTPUT="$(
  cd "$CHALLENGE_DIR"
  forge create \
    --rpc-url "$RPC_URL" \
    --private-key "$DEPLOYER_PRIVATE_KEY" \
    --broadcast \
    "$FACTORY_CONTRACT"
)"

echo "$DEPLOY_OUTPUT"
FACTORY_ADDRESS="$(printf "%s\n" "$DEPLOY_OUTPUT" | sed -n 's/^Deployed to: //p' | tail -n 1)"

if [ -z "$FACTORY_ADDRESS" ]; then
  echo "[deploy:${CHALLENGE_ID}] failed to parse factory address" >&2
  exit 1
fi

cat > "${OUT_DIR}/metadata.json" <<EOF
{
  "challenge_id": "${CHALLENGE_ID}",
  "kind": "blockchain_rpc",
  "protocol": "http",
  "chain_family": "evm",
  "chain_id": ${CHAIN_ID},
  "rpc_url": "${PUBLIC_RPC_URL}",
  "rpc_port": ${RPC_PORT},
  "factory_address": "${FACTORY_ADDRESS}",
  "factory_abi": "metadata/challenges/${CHALLENGE_ID}/artifacts/ChallengeFactory.abi.json",
  "setup_abi": "metadata/challenges/${CHALLENGE_ID}/artifacts/Setup.abi.json",
  "deployment_mode": "static_factory",
  "isolation_scope": "shared_chain_per_user_setup",
  "spawn_function": "${SPAWN_FUNCTION}",
  "checker": "${CHECKER}"
}
EOF

echo "[deploy:${CHALLENGE_ID}] wrote ${OUT_DIR}/metadata.json"
cat "${OUT_DIR}/metadata.json"
