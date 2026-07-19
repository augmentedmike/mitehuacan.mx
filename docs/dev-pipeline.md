# Development pipeline (2026-07-19)

Prod domain: mitehuacan.mx → Cloudflare (Namecheap NS → Cloudflare zone).
Vercel = frontend preview mirror. Cloudflare = staging + production + all data.

## Branches
- `dev`  — all day-to-day work lands here first (agent + human).
- `main` — production. Only receives dev merges when staging has been approved.

## The loop
1. **Local**: `bunx wrangler pages dev site --port 8788 --ip 0.0.0.0`
   (full backend: functions + local D1; LAN URL for phone testing — no HTTPS,
   so geolocation flows need staging).
2. **Push to `dev`** → Vercel auto-builds a preview URL (git integration).
   Previews are DATA-LIVE: vercel.json proxies /api/* to the Cloudflare data
   plane, so schedules/fares/sponsor pins render real values. HTTPS → location
   services testable on the phone. Frontend-only: no local D1, no admin.
3. **Cloudflare staging** (backend-real): rebuild then
   `bunx wrangler pages deploy site --branch staging` → staging.mitehuacan.pages.dev.
   Use for anything touching functions/, migrations, redirects.
4. **Promote to production**: merge dev → main, push, then
   `bunx wrangler pages deploy site --branch main`. The domain serves this.
5. **Admin app** deploys independently:
   `cd backoffice && bunx wrangler pages deploy public --project-name mitehuacan-admin --branch main`.

## Databases — fully separated environments (2026-07-19)
- LOCAL:      local D1 (wrangler state) — `... apply quecombi --local`
- STAGING:    `quecombi-staging` (89f04f58…) — bound to the PREVIEW env of both
              Pages projects. `bunx wrangler d1 migrations apply quecombi-staging --remote --env preview`
- PRODUCTION: `quecombi` (b0a959fa…) — bound to the PRODUCTION env only.
              At promote time: `bunx wrangler d1 migrations apply quecombi --remote --env production`
Staging deploys can NEVER touch production data — different database, enforced
by per-environment bindings in both wrangler.toml files.

## Rules of thumb
- Never edit `site/` by hand — it's generated (`tehuacan/scripts/09_build_site.py`).
- Data files (routes/sponsors/pois) regenerate via scripts 06/12/15 before 09.
- Vercel "production" (main) is NOT the product's production — Cloudflare is.
  Vercel main deploys are just the stable preview of main.
