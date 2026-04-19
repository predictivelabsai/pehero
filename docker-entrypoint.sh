#!/usr/bin/env sh
# Container entrypoint for PEHero.
#
# On start we run `db.migrate` (idempotent — safe on every deploy) so fresh
# Coolify deploys end up with the schemas + pgvector extension without a
# manual terminal step. Synthetic data seeding stays manual so we never
# clobber real data; run once after the first deploy:
#
#   docker compose exec web python -m synthetic.generate --seed 42
#
# Set PEHERO_SKIP_MIGRATE=1 to bypass migration (e.g. read-only replicas).

set -eu

if [ "${PEHERO_SKIP_MIGRATE:-0}" != "1" ]; then
    echo "[entrypoint] running db.migrate"
    python -m db.migrate || {
        echo "[entrypoint] migrate failed — continuing to start so logs are visible" >&2
    }
fi

exec "$@"
