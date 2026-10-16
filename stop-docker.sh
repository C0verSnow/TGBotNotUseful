#!/usr/bin/env bash
set -euo pipefail
container="${1:?Container is required}"
[[ "$container" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]] || exit 2
docker container inspect -- "$container" >/dev/null
docker container stop --time 20 -- "$container" >/dev/null
[[ "$(docker container inspect --format '{{.State.Running}}' -- "$container")" == false ]]
