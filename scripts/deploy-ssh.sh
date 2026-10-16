#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in start|stop) action="$1" ;; *) echo 'Invalid action' >&2; exit 2 ;; esac
: "${SSH_PRIVATE_KEY:?}" "${SSH_KNOWN_HOSTS:?}" "${DEPLOY_HOST:?}" "${DEPLOY_USER:?}" "${DOCKER_CONTAINER:?}"
port="${DEPLOY_PORT:-22}"
[[ "$DEPLOY_HOST" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*$ && "$DEPLOY_USER" =~ ^[a-zA-Z_][a-zA-Z0-9_-]*$ ]] || exit 2
[[ "$port" =~ ^[0-9]{1,5}$ ]] && ((10#$port >= 1 && 10#$port <= 65535)) || exit 2
[[ "$DOCKER_CONTAINER" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]] || exit 2
temporary="$(mktemp -d)"
trap 'rm -rf "$temporary"' EXIT
chmod 700 "$temporary"
printf '%s\n' "$SSH_PRIVATE_KEY" > "$temporary/key"
printf '%s\n' "$SSH_KNOWN_HOSTS" > "$temporary/known_hosts"
chmod 600 "$temporary/key" "$temporary/known_hosts"
script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Upload a fixed repository script over stdin. All interpolated parameters have strict allowlists.
timeout 110 ssh -T -i "$temporary/key" -p "$port" \
  -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o "UserKnownHostsFile=$temporary/known_hosts" -o ConnectTimeout=10 \
  -o ServerAliveInterval=10 -o ServerAliveCountMax=2 \
  "$DEPLOY_USER@$DEPLOY_HOST" "flock -w 30 /tmp/tgbot-docker-control.lock timeout 60 bash -s -- '$DOCKER_CONTAINER'" \
  < "$script_directory/../$action-docker.sh"
