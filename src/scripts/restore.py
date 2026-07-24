#!/usr/bin/env python3
"""Restore a gzipped backup archive into a D1 database.

The other half of the backup story: a backup you cannot restore is not a backup.
Reads a `.json.gz` archive produced by the `mitehuacan-db-backup` Worker and
rebuilds every table (DROP + CREATE from the archived schema + INSERT all rows +
recreate indexes) in the target D1.

Archive source (pick one):
  --file PATH                 a local archive.json.gz
  --from-worker latest|<ts>   download it from the backup Worker (needs BACKUP_TOKEN env)

Target (SAFETY: defaults to staging; production requires --yes):
  --target staging | production        (default: staging)

Examples:
  BACKUP_TOKEN=... python3 src/scripts/restore.py --from-worker latest --target staging
  python3 src/scripts/restore.py --file /tmp/snap.json.gz --target staging
  # a real disaster restore to prod is deliberate and loud:
  BACKUP_TOKEN=... python3 src/scripts/restore.py --from-worker latest --target production --yes

By default it prints a plan and the generated SQL path, then applies it with
`wrangler d1 execute --remote --file`. Pass --dry-run to stop before applying.
"""
import argparse
import base64
import gzip
import io
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

WORKER = "https://mitehuacan-db-backup.mauriciotellezdev.workers.dev"
DBS = {"staging": "mitehuacan-staging", "production": "mitehuacan"}
ACCOUNT_ID = "46e7500b33be08b5e4a9847facbf6911"

def sql_lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, dict) and "$b64" in v:          # BLOB column -> hex literal
        return "X'" + base64.b64decode(v["$b64"]).hex() + "'"
    return "'" + str(v).replace("'", "''") + "'"

def load_archive(args):
    if args.file:
        with gzip.open(args.file) as f:
            return json.load(f)
    tok = os.environ.get("BACKUP_TOKEN")
    if not tok:
        sys.exit("set BACKUP_TOKEN to download from the worker (or use --file)")
    url = f"{WORKER}/?token={tok}&download={args.from_worker}"
    # Cloudflare's edge 403s the default python-urllib UA; send a normal one
    req = urllib.request.Request(url, headers={"User-Agent": "mitehuacan-restore/1.0"})
    raw = urllib.request.urlopen(req, timeout=60).read()
    return json.load(gzip.open(io.BytesIO(raw)))

def build_sql(dump):
    out = ["PRAGMA defer_foreign_keys = TRUE;"]
    for t in dump["tables"]:
        name = t["name"]
        out.append(f'DROP TABLE IF EXISTS "{name}";')
        out.append(t["sql"].rstrip().rstrip(";") + ";")
        rows = t["rows"]
        if not rows:
            continue
        cols = list(rows[0].keys())
        collist = ",".join(f'"{c}"' for c in cols)
        # batch INSERTs so no single statement gets huge
        for i in range(0, len(rows), 200):
            chunk = rows[i:i + 200]
            values = ",".join("(" + ",".join(sql_lit(r.get(c)) for c in cols) + ")" for r in chunk)
            out.append(f'INSERT INTO "{name}" ({collist}) VALUES {values};')
    for idx in dump.get("indexes", []):
        out.append(idx.rstrip().rstrip(";") + ";")
    return "\n".join(out) + "\n"

def main():
    ap = argparse.ArgumentParser(description="Restore a D1 backup archive.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="local archive.json.gz")
    src.add_argument("--from-worker", metavar="latest|<ts>", help="download from the backup Worker")
    ap.add_argument("--target", choices=list(DBS), default="staging")
    ap.add_argument("--yes", action="store_true", help="required to target production")
    ap.add_argument("--dry-run", action="store_true", help="write the SQL but do not apply")
    args = ap.parse_args()

    if args.target == "production" and not args.yes:
        sys.exit("refusing to restore to PRODUCTION without --yes (this overwrites live data)")

    dump = load_archive(args)
    n_rows = dump.get("meta", {}).get("rows", sum(len(t["rows"]) for t in dump["tables"]))
    print(f"archive ts={dump.get('ts')}  tables={len(dump['tables'])}  rows={n_rows}  indexes={len(dump.get('indexes', []))}")
    print(f"target: {args.target} ({DBS[args.target]})")

    sql = build_sql(dump)
    path = os.path.join(tempfile.gettempdir(), f"restore-{args.target}.sql")
    with open(path, "w") as f:
        f.write(sql)
    print(f"generated SQL: {path} ({len(sql)} bytes)")

    if args.dry_run:
        print("--dry-run: not applying.")
        return

    print(f"applying to {DBS[args.target]} …")
    env = dict(os.environ, CLOUDFLARE_ACCOUNT_ID=ACCOUNT_ID)
    cmd = ["bunx", "wrangler", "d1", "execute", DBS[args.target], "--remote", "--file", path]
    # D1 --file is atomic (failed applies roll back) but can transiently fail — retry.
    for attempt in range(1, 4):
        if subprocess.run(cmd, env=env).returncode == 0:
            print(f"OK: restored {n_rows} rows into {args.target}.")
            return
        print(f"attempt {attempt} failed (DB rolled back to its prior state); retrying…" if attempt < 3 else "")
    sys.exit("restore FAILED after 3 attempts")

if __name__ == "__main__":
    main()
