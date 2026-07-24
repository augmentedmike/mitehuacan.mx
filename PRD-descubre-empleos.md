# PRD — Descubre: Empleos (jobs discovery agent)

**Status:** Draft v1
**Owner:** Michael
**Date:** 2026-07-24
**Section:** `/descubre/` → **Jobs** (currently "Coming soon")
**Scope of this PRD:** agent + data feed only — a new discovery agent in
`src/scripts/discover/` and a publish script emitting a `.js` feed, matching the existing
`discovery.js` / `events.js` pattern. **No** new D1 table, public API, or UI yet.
**Depends on:** `discover/lib.py` `DiscoveryAgent` base ·
[`business/discover-geo-scope.md`](business/discover-geo-scope.md) (hard geo limit) ·
[`business/cold-start-playbook.md`](business/cold-start-playbook.md)

---

## 1. Problem

`/descubre/` promises "Jobs — Local work: openings around the region and a place to offer
your skills," with nothing behind it. Local job supply is real but fragmented across
national boards (Computrabajo, OCC, Talenteca, Indeed), the **government** portal (SNE /
empleo.gob.mx), and — for the informal majority — Facebook groups like *Empleos Tehuacán
(Actuales)*. A Tehuacano job-seeker has no single local view; the national boards bury
Tehuacán under Puebla-state and remote listings.

Same posture as the other verticals: **aggregate the local openings into one geo-filtered
feed and link back to apply.** We are not an ATS and not a recruiter — we make the city's
jobs legible in one place, terminating in the employer's own apply flow / WhatsApp.

## 2. Strategic fit

- **Daily-habit surface.** Jobs are a high-intent recurring reason to open the app —
  another feed into the same organic funnel, zero sales cost.
- **Public-interest angle.** The government SNE board (empleo.gob.mx) is *designed* to be
  redistributed — a clean, uncontroversial anchor source, and a credible civic framing for
  the whole section.
- **Reuses built-once rails** (harness, geo-gate, publish→`.js`). One more agent.

## 3. Goals

1. An **empleos agent** harvesting current local openings across the source set (§5),
   deduped, geo-gated to the 17-town boundary, into its own lifecycle store.
2. A **publish script** → `resources/map-data/empleos.js` (§7), link-back to apply.
3. **Expiry:** demote filled/closed/stale postings so the feed stays current.
4. **Hard geo limit** per [`discover-geo-scope.md`](business/discover-geo-scope.md) — the
   employer's work location must be Tehuacán + the 16 towns; drop Puebla-capital-only and
   generic-remote postings (remote handled in §8).

## 4. Non-goals

- No new DB table / API / UI (later PRD).
- Not an applicant tracker; **no seeker/applicant personal data** — public postings only.
- No "offer your skills" seeker-side intake yet (that's a self-serve feature, future).
- No résumé handling.

## 5. External data sources (all of them, ranked by local value)

The Facebook groups are the informal moat (openings that never touch a job board); the
government board is the cleanest structured anchor.

| # | Source | URL | Tehuacán coverage | Structure | Access notes |
|---|--------|-----|-------------------|-----------|--------------|
| 1 | **Facebook groups** — "Empleos Tehuacán (Actuales)" & peers | facebook.com/groups/1458432271042909 (+ more) | **Highest** informal — tiendas, obra, meseros, choferes | Free-text posts | Signed-in profile (proven in `facebook.py`); per-group feed scrape; text geo-match |
| 2 | **Computrabajo** | mx.computrabajo.com/empleos-en-tehuacan | **High** (~119) | **Structured** (title, company, salary?, location, apply URL) | Largest LATAM board; ToS forbids scraping — throttle + link back |
| 3 | **OCC Mundial** | occ.com.mx/empleos/en-puebla/en-la-ciudad-de-tehuacan | High | Structured | Throttle + link back |
| 4 | **empleo.gob.mx** (Portal del Empleo / SNE, STPS) | empleo.gob.mx/vacantes/puebla | Moderate | Structured, **public/government** | Best-licensed source; check for open-data/API/CSV; SNE Tehuacán unit is local |
| 5 | **Talenteca** | talenteca.com/empleos-en-tehuacan-puebla | Moderate | Structured | Link back |
| 6 | **Indeed MX** | mx.indeed.com (q=…, l=Tehuacán) | Moderate (aggregator) | Structured | Aggregates 2/3/5 → dedup heavy; has a (gated) Publisher API |
| 7 | **SEDETRA Puebla / municipal bolsa** | sedetra.puebla.gob.mx/bolsa-de-trabajo | Low, official | Varies | State labor dept; ferias de empleo announcements |
| 8 | **SNE Puebla / Tehuacán Facebook** | facebook.com/SNEPueblaOfi | Low, official | Posts | Government FB page; job-fair + vacancy posts |
| 9 | **Bumeran / LinkedIn** | bumeran.com.mx, linkedin.com/jobs | Low locally | Structured | Thin for Tehuacán; LinkedIn scraping is aggressively blocked — low priority |
| 10 | **Local newspaper clasificados** | El Mundo/El Sol de Tehuacán | Low, offline-origin | Free-text | Investigate web classifieds |

**Source strategy:** anchor on **#4 (government, cleanest license)** + **#2/#3 (Computrabajo,
OCC — the volume)** for structured data, and **#1 (Facebook groups)** for the informal
local moat. Indeed (#6) only if direct-board coverage has gaps, with hard dedup.

## 6. Agent design

New `src/scripts/discover/empleos.py`, subclassing `DiscoveryAgent`:

- **`build_plan()`** — plan is **source × location filter**. Structured boards expose a
  Tehuacán URL/filter directly; Facebook groups are enumerated by group id. Optional
  keyword axis (a small jobs taxonomy: ventas, atención a cliente, chofer, obrero,
  cajero, mesero, seguridad, oficina, salud…) only where a board needs a query.
- **`scrape_item()`** — per-source adapter → `{key, title, company, salary_min, salary_max,
  period, location_text, colonia?, lat?, lon?, kind(category), apply_url, source, posted_at,
  contact?}`. Boards give company + structured location; Facebook gives free-text (parse
  town/colonia + a phone/WhatsApp if present).
- **Geo-gate** — `geo.scope_of()` on the **work location** (employer location text/coords),
  not the company HQ. Remote-only postings without a local employer are dropped (see §8).
  Store resolved `town`; log drops.
- **`_key()`** — board listing id / Facebook post id; idempotent upsert.
- **`verify_record()`** — re-open apply URL; "vacante no disponible" / 404 / expired →
  **dead**. Postings also auto-expire after a max age (e.g. 45 days) since boards leave
  stale ones up.
- Store `resources/discovery/empleos.db`; standard lifecycle.

**Dedup:** the same opening on OCC + Computrabajo + Indeed is common. Key on normalized
(title, company, town); keep all apply links, prefer the government/direct-employer one.

## 7. Publish feed — `resources/map-data/empleos.js`

```js
const EMPLEOS = {"empleos":[
  {t, co, sal, per, k, town, col, c:[lon,lat], u, src, d, x}
]}
// t=title  co=company  sal="$X–$Y" or null  per=salary period(mes|semana|hora|null)
// k=category  town=resolved town  col=colonia(optional)
// c=[lon,lat] (omit if none — listed, not pinned)  u=apply URL  src=source id
// d=posted/seen ISO date  x=1 when location approximate (town-matched, no coords)
```

No-coord postings are listed but not pinned (same convention as `discovery.js`). Publish
script `src/scripts/27_publish_empleos.py`.

## 8. Geo edge case — remote / home-office jobs

Jobs boards surface "remoto / home office" postings that may or may not be local. Rule:

- If the posting names a **local employer or a local work location** (Tehuacán/town) → keep,
  even if hybrid/remote.
- If it is **remote-only with no local tie** (national call-center farming, "trabaja desde
  cualquier ciudad") → **drop.** These flood the boards and aren't "local work."
- Ambiguous → drop (bias to precision, per the geo-scope doc's "when in doubt, drop").

## 9. Legal / ToS / ethics

- **empleo.gob.mx (government)** is the preferred, most-redistributable anchor — check for
  an official feed/API/open-data before scraping HTML.
- Structured boards (Computrabajo/OCC/Talenteca/Indeed) forbid scraping in ToS — same
  posture: throttle, minimal fields, **link back to apply** (we send them applicants, we
  don't clone their board). Indeed offers a gated Publisher API worth evaluating.
- **No applicant data, ever.** Only public postings + the employer's chosen public contact.
- Attribution + takedown honored. Human legal review before non-government board adapters
  go live.

## 10. Metrics / done

- **Coverage:** ≥ N live, geo-valid openings across ≥3 sources for the region.
- **Locality precision:** sample audit ~0 out-of-scope / remote-farm postings.
- **Freshness:** filled/expired postings demoted within a cycle; low ghost rate.
- **Net-new:** count of Facebook-group-only openings (the informal moat).

## 11. Open questions

1. Which **Facebook empleos groups** beyond `1458432271042909` to seed? → promotor input.
2. Does **empleo.gob.mx / SNE** publish an open-data feed or API (it's a federal STPS
   system)? → spike; big licensing win if yes.
3. Indeed **Publisher API** access + terms for a small local aggregator? → evaluate.
4. Salary parsing: boards vary wildly ("sueldo según aptitudes", ranges, weekly vs
   monthly) — normalize or store raw + parsed?
