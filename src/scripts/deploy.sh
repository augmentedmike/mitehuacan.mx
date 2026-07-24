#!/usr/bin/env bash
# Canonical deploy for the public site + functions + schema, IN THE RIGHT ORDER.
#
# The bug this prevents: functions/api/negocios.js shipped needing the `negocios`
# table, but the migration was never applied to prod, so every real signup 500'd.
# Three things deploy independently here — D1 migrations, CF Pages functions, and
# Vercel static — and nothing tied "code that needs a table" to "table exists".
# This script makes SCHEMA go first, always.
#
# Usage:  src/scripts/deploy.sh [production|staging]   (default: production)
# Requires: bun + wrangler authed to mauriciotellezdev (owns the D1 dbs).
# Note: Vercel static is deployed by pushing to `main` (see docs/dev-pipeline.md);
#       this script owns the D1 + Cloudflare Pages side, which is the part that
#       was manual and un-coordinated.
set -euo pipefail
cd "$(dirname "$0")/../.."
export CLOUDFLARE_ACCOUNT_ID=46e7500b33be08b5e4a9847facbf6911

TARGET="${1:-production}"
case "$TARGET" in
  production) DB=mitehuacan;         BRANCH=main ;;
  staging)    DB=mitehuacan-staging; BRANCH=staging ;;
  *) echo "usage: $0 [production|staging]"; exit 2 ;;
esac

echo "==> [1/4] apply pending migrations to $TARGET ($DB) — schema before code"
bunx wrangler d1 migrations apply "$DB" --remote

echo "==> [2/4] rebuild static site (build/)"
python3 src/scripts/09_build_site.py

echo "==> [3/4] deploy Cloudflare Pages (static + functions) to branch $BRANCH"
bunx wrangler pages deploy build --project-name mitehuacan --branch "$BRANCH"

echo "==> [4/4] verify no schema drift remains"
python3 src/scripts/check_migrations.py "$TARGET"

echo "OK: $TARGET deploy complete (D1 + Cloudflare Pages)."
echo "    Vercel static updates on push to main — remember to promote if this was a content change."
