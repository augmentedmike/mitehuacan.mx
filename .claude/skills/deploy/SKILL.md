---
name: deploy
description: Ship MiTehuacán to prod, apply D1 migrations, or make ANY database schema change. Use whenever you edit functions/ that read or write the DB, add a src/migrations file, need a new table/column, or push to prod. Encodes the schema-before-code rule and the three independent deploy channels so a function never ships ahead of its table again.
---

# Deploying MiTehuacán without breaking it

There are **three independent deploy channels** and nothing auto-coordinates
them. This is the trap: it is easy to ship code that needs a table/column the
prod DB does not have yet.

| Channel | What it serves on mitehuacan.mx | How it deploys |
|---|---|---|
| **D1 migrations** | the database schema (tables/columns) | `wrangler d1 migrations apply` — MANUAL |
| **Cloudflare Pages** | `/api/*` and `/qr/*` **functions** | `wrangler pages deploy build` — MANUAL (git push does NOT do this) |
| **Vercel** | the static site (`/`, `/directorio`, the map app) | auto on push to `main` |

The account that owns the D1 dbs + CF Pages project is **mauriciotellezdev**
(`CLOUDFLARE_ACCOUNT_ID=46e7500b33be08b5e4a9847facbf6911`). wrangler is OAuth-authed to it.
Prod DB = `mitehuacan`, staging = `mitehuacan-staging`, backup = `mitehuacan-backup`.

## The one rule: schema before code

**Never deploy a function that needs a table/column before that migration is
applied to the target DB.** Real incident: `functions/api/negocios.js` shipped
needing `negocios`, but migration `0017` was never applied to prod, so every
business signup 500'd silently. Nothing caught it because schema and code deploy
on different channels.

## Every schema change is a numbered migration file — never ad-hoc SQL

- Add a new file `src/migrations/00NN_thing.sql`. Prefer idempotent DDL
  (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`). `ALTER TABLE ADD
  COLUMN` is NOT idempotent — it errors if re-run, so it must be applied exactly once.
- Apply it with `wrangler d1 migrations apply <db> --remote` so it is recorded in
  the `d1_migrations` table. **Do NOT apply schema with a raw
  `wrangler d1 execute --file`** — that changes the DB without recording it, which
  is exactly how the tracking table went stale (it only knew about 0001–0016 while
  0017–0021 had been hand-applied). If you ever must hand-apply, immediately
  `INSERT OR IGNORE INTO d1_migrations (name) VALUES ('00NN_thing.sql')` to reconcile.

## Commands

```bash
# 1. Is prod (or staging) missing any migration?  Exit 1 = drift.
python3 src/scripts/check_migrations.py production

# 2. Canonical deploy: migrations -> build -> CF Pages -> verify, in order.
src/scripts/deploy.sh production        # or: staging

# 3. Apply migrations only (what deploy.sh step 1 runs):
bunx wrangler d1 migrations apply mitehuacan --remote
```

`src/scripts/deploy.sh` is the safe path — it applies pending migrations FIRST,
then rebuilds `build/`, then `wrangler pages deploy build`, then re-checks drift.
Use it instead of running `wrangler pages deploy` by hand.

## Guardrail already in place

A **pre-push git hook** (`.githooks/pre-push`, enabled via
`git config core.hooksPath .githooks`) blocks any push that advances `main` while
prod has unapplied migrations. If it blocks you: apply the migration, then push.
Bypass only with `git push --no-verify` and only when you mean it.

## Promoting to prod static (Vercel) — main is protected

Pushing to `main` triggers Vercel. `main` has branch protection with enforce_admins,
so the flow is:
```bash
gh api -X DELETE repos/augmentedmike/mitehuacan.mx/branches/main/protection/enforce_admins
git push origin dev:main
gh api -X POST  repos/augmentedmike/mitehuacan.mx/branches/main/protection/enforce_admins
```
If the push adds a migration, the pre-push hook forces you to apply it to prod first.

## After any deploy, verify on the real domain

- Static change → `curl -s https://mitehuacan.mx/<path>` for a marker.
- Function change → hit the endpoint (`curl` the `/api` or `/qr` route) and check
  the response, because CF Pages is a SEPARATE manual deploy from the git push.
- Schema change → `python3 src/scripts/check_migrations.py production` must be clean,
  and exercise the feature end-to-end (e.g. POST a throwaway row, confirm it lands,
  delete it).

## The backup follows schema automatically

`mitehuacan-backup` is rebuilt nightly by the `mitehuacan-db-backup` Worker
(`backup/src/index.js`, cron `0 9 * * *`, deploy with `cd backup && bunx wrangler deploy`):
it drops and recreates every table from the SOURCE's live `sqlite_master` schema, so it
mirrors whatever prod is within ≤24h — including new tables/columns and the
`d1_migrations` table. There is no separate migration path for the backup, and it cannot
drift. D1 Time Travel covers the sub-24h point-in-time gap.

Each run also writes a **gzipped point-in-time archive** into the backup DB
(`_snapshots`, chunked BLOB rows — free, no R2), keeps ~10 days, and purges older.
Token-gated endpoints on the Worker (`?token=$BACKUP_TOKEN`): `&list` enumerates
archives, `&download=latest|<ts>` returns the `.json.gz` (a full JSON dump of every
table + indexes, recoverable). BACKUP_TOKEN is a Worker secret (`cd backup && bunx
wrangler secret put BACKUP_TOKEN`) AND a GitHub repo secret; it is NOT in the repo or memory.

**Restore** (a backup you can't restore isn't a backup):
`BACKUP_TOKEN=... python3 src/scripts/restore.py --from-worker latest --target staging`
rebuilds every table + rows + indexes into the target D1. Defaults to staging; prod
needs `--target production --yes`. Rehearse into staging periodically.

**Off-site + monitoring**: `.github/workflows/db-backup-offsite.yml` (daily 10:00 UTC)
copies the archive OFF the Cloudflare account onto the `db-backups` branch, and FAILS
(emailing the repo owner) if the backup is missing/stale/corrupt — so a dead backup
gets noticed. Prod, backup DB, and archives otherwise all live in the one CF account.

## The MapLibre testing gotcha (unrelated but costly)

When verifying the map app in the Chrome automation tab, the MapLibre map loads
very slowly (black canvas, `map.loaded()` false for 15–30s) even though the network
is fine. Take spaced screenshots to drive the render; do not conclude a deep-link or
map feature is broken until the map has actually finished loading. Never hammer
`map.redraw()` in a loop — it freezes the renderer.
