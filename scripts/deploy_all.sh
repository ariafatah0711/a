#!/bin/sh
set -eu

for challenge_dir in challenges/*; do
  if [ ! -f "${challenge_dir}/challenge.yml" ]; then
    continue
  fi

  challenge_id="$(basename "$challenge_dir")"
  sh scripts/deploy_one.sh "$challenge_id"
done
