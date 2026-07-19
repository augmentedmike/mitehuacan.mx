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

## Migrations (D1)
- Apply locally first: `bunx wrangler d1 migrations apply quecombi --local`.
- Apply remotely AT PROMOTE TIME: `... --remote`.
- KNOWN TRADEOFF: staging and production share ONE remote D1. Migrations are
  additive-only by convention; destructive changes ship with their code in the
  same promote. (A separate staging DB is future work.)

## Rules of thumb
- Never edit `site/` by hand — it's generated (`tehuacan/scripts/09_build_site.py`).
- Data files (routes/sponsors/pois) regenerate via scripts 06/12/15 before 09.
- Vercel "production" (main) is NOT the product's production — Cloudflare is.
  Vercel main deploys are just the stable preview of main.
