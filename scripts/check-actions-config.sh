#!/usr/bin/env bash
set -euo pipefail

# Report names only: never print secret values or shell expansions.
missing=0
if [[ -z "${AUTH_KEY:-}" && ( -z "${TS_OAUTH_CLIENT_ID:-}" || -z "${TS_OAUTH_SECRET:-}" ) ]]; then
  echo '::error::Missing Tailscale authentication: set AUTH_KEY, or both TS_OAUTH_CLIENT_ID and TS_OAUTH_SECRET in Actions secrets.'
  missing=1
fi
for name in SSH_PRIVATE_KEY SSH_KNOWN_HOSTS TELEGRAM_BOT_TOKEN DEPLOY_HOST DEPLOY_USER DOCKER_CONTAINER; do
  if [[ -z "${!name:-}" ]]; then
    echo "::error::Missing Actions configuration: $name. Set it under repository Settings > Secrets and variables > Actions."
    missing=1
  fi
done
if ((missing)); then
  exit 2
fi
