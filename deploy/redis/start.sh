#!/bin/sh
set -eu

case "${REDIS_PASSWORD:-}" in
  ''|*[!A-Za-z0-9+/=_-]*) echo 'A generated Redis password is required.' >&2; exit 1 ;;
esac

# Rate-limit keys expire; account and email records live durably in MySQL.
# Read configuration from stdin so the password stays out of process arguments.
exec redis-server - <<CONFIG
bind 0.0.0.0
port 6379
protected-mode yes
requirepass ${REDIS_PASSWORD}
save ""
appendonly no
maxmemory 128mb
maxmemory-policy noeviction
CONFIG
