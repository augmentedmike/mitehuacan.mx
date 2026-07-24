#!/usr/bin/env python3
"""Detect D1 schema drift.

Compares the migration files in src/migrations/*.sql against what a given
environment's DB actually records in its `d1_migrations` table, and exits
non-zero if any local migration hasn't been applied.

This is the guard that would have caught the missing `negocios` table: a
function shipped that needed it, but the migration was never applied to prod
and nothing noticed. Run it in the pre-push hook and at the end of a deploy.

Usage:  python3 src/scripts/check_migrations.py [production|staging]
        (default: production)

Requires: bun + wrangler, authenticated to the Cloudflare account that owns
the mitehuacan D1 databases (mauriciotellezdev).
"""
import glob
import json
import os
import subprocess
import sys

ENVS = {"production": "mitehuacan", "staging": "mitehuacan-staging"}
ACCOUNT_ID = "46e7500b33be08b5e4a9847facbf6911"  # mauriciotellezdev — owns the D1 dbs

def main():
    env = sys.argv[1] if len(sys.argv) > 1 else "production"
    db = ENVS.get(env)
    if not db:
        sys.exit(f"unknown env '{env}' — use: {' | '.join(ENVS)}")

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    local = sorted(os.path.basename(p) for p in glob.glob(os.path.join(root, "src/migrations/*.sql")))
    if not local:
        sys.exit("no migrations found in src/migrations/ — wrong working dir?")

    e = dict(os.environ, CLOUDFLARE_ACCOUNT_ID=ACCOUNT_ID)
    proc = subprocess.run(
        ["bunx", "wrangler", "d1", "execute", db, "--remote", "--json",
         "--command", "SELECT name FROM d1_migrations"],
        capture_output=True, text=True, env=e, cwd=root)
    if proc.returncode != 0:
        sys.exit(f"could not query {db} (is wrangler authed?):\n{proc.stderr[-400:]}")

    # wrangler may print a banner before the JSON array — slice from the first '['
    txt = proc.stdout
    i = txt.find("[")
    if i < 0:
        sys.exit(f"unexpected wrangler output:\n{txt[-400:]}")
    data = json.loads(txt[i:])
    applied = {r["name"] for res in data for r in res.get("results", [])}

    pending = [m for m in local if m not in applied]
    if pending:
        print(f"SCHEMA DRIFT on {env} ({db}) — {len(pending)} unapplied migration(s):")
        for m in pending:
            print(f"   - {m}")
        print(f"\nApply them before deploying code that needs them:")
        print(f"   bunx wrangler d1 migrations apply {db} --remote")
        sys.exit(1)

    print(f"OK: {env} schema in sync ({len(local)} migrations tracked)")

if __name__ == "__main__":
    main()
