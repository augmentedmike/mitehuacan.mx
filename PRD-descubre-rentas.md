# PRD — Descubre: Rentas (rental listings discovery agent)

**Status:** Draft v1
**Owner:** Michael
**Date:** 2026-07-24
**Section:** `/descubre/` → **Rentals** (currently "Coming soon")
**Scope of this PRD:** agent + data feed only — a new discovery agent in
`src/scripts/discover/` and a publish script emitting a `.js` feed, matching the existing
`discovery.js` / `events.js` pattern. **No** new D1 table, public API, or UI yet.
**Depends on:** the discovery harness (`discover/lib.py` `DiscoveryAgent` base) ·
[`business/discover-geo-scope.md`](business/discover-geo-scope.md) (hard geo limit) ·
[`business/cold-start-playbook.md`](business/cold-start-playbook.md) (strategy)

---

## 1. Problem

`/descubre/` promises "Rentals — Houses, apartments and storefronts for rent, listed by
local people," but there is **no data behind it.** Meanwhile the actual rental supply for
Tehuacán already exists, scattered across a handful of national portals and — mostly —
inside Facebook. A Tehuacano looking for a departamento today checks 4–5 apps and a
Facebook group. The city has no single, local, map-first view of what's for rent.

We are **not** trying to become a real-estate portal or take a commission. Consistent with
the playbook ("don't fight the incumbents — inject structure into them"), the job is to
**aggregate the local rental supply into one geo-filtered feed on the map and link back to
the original listing.** MiTehuacán becomes the place you *start* the search; the close
still happens on WhatsApp/Facebook/the portal.

## 2. Strategic fit

- **Supply-first, same as everything else.** A populated rentas feed is another reason to
  open the app daily (alongside combis + directory + events) — more DAU into the same
  funnel, at zero sales cost.
- **Reuses built-once rails.** The `discover/` harness, the geo-gate, the publish→`.js`
  pattern, and the map's search index all already exist. This is one more agent, not new
  infrastructure.
- **Later monetization is obvious but out of scope now:** featured/boosted local listings,
  or a self-serve "publica tu renta" intake (mirroring `negocios`), once the feed proves
  daily use. This PRD deliberately stops at data.

## 3. Goals

1. A **rentas agent** that harvests current rental listings across the source set (§5),
   deduped, geo-gated to the 17-town boundary, into its own lifecycle store.
2. A **publish script** emitting `resources/map-data/rentas.js` in a shape the app can map
   + list (see §7), links back to source.
3. **Freshness/expiry:** rentals churn fast; the pipeline marks stale/rented listings dead
   so the feed doesn't show ghosts.
4. **Hard geo limit** per [`discover-geo-scope.md`](business/discover-geo-scope.md) — only
   Tehuacán + the 16 towns; drop everything else at scrape time.

## 4. Non-goals

- No new DB table / API / UI (separate later PRD once data is flowing).
- **No short-term / vacation rentals** (Airbnb, Expedia, hotels, car rental) — different
  product; filtered out by category regardless of geography.
- No lead brokering, no commission, no scraping of buyer/renter personal data — listings
  only.
- No republishing of portal photos at scale (hotlink/thumbnail + link-back only; see §8).

## 5. External data sources (all of them, ranked by local value)

Ordered by how much *net-new, genuinely-local* supply each adds. The informal (Facebook)
sources are the real moat — those listings are on **no** portal.

| # | Source | URL | Tehuacán coverage | Structure | Access notes |
|---|--------|-----|-------------------|-----------|--------------|
| 1 | **Facebook Marketplace** (Propiedades → En renta) | facebook.com/marketplace | **Highest** — most local rentals are FB-only | Loose (title, price, colonia, photos; coords rare) | Signed-in profile (we already do this in `facebook.py`/`fb_events.py`); location=Tehuacán + radius; heavy geo-gate needed |
| 2 | **Local Facebook rental groups** | e.g. "Rentas en Tehuacán", "Casas y deptos en renta Tehuacán" | High, hyper-local | Free-text posts | Same session; per-group feed scrape; text town/colonia match |
| 3 | **Inmuebles24** | inmuebles24.com/inmuebles-en-renta-en-tehuacan | Moderate (dozens) | **Structured** (type, price, m², beds, coords) | Navent portal; ToS forbids scraping — throttle, link back, prefer public listing pages |
| 4 | **Mercado Libre Inmuebles** | inmuebles.mercadolibre.com.mx/rentas-tehuacan-puebla | Moderate | Structured + often geocoded | **Has an official API** (developers.mercadolibre.com.mx) — prefer it over HTML where it exposes real-estate items |
| 5 | **Vivanuncios** | vivanuncios.com.mx/s-renta-inmuebles/tehuacan-puebla | Low–moderate (8–16) | Structured | Classifieds portal; link back |
| 6 | **Lamudi** | lamudi.com.mx/puebla/tehuacan/for-rent | Low (~12) | Structured | Link back |
| 7 | **Propiedades.com** | propiedades.com/tehuacan/renta | Moderate (~92 sale+rent) | Structured | Link back |
| 8 | **Casas y Terrenos** | casasyterrenos.com | Low | Structured | National portal, thin locally |
| 9 | **Meta-aggregators** (Trovit, Mitula, Nestoria) | trovit.com.mx etc. | Mirror of 3–8 | Structured | Convenient single crawl **but** heavy duplication of the portals above — use only if direct-portal coverage is too thin; dedup aggressively |
| 10 | **Local newspaper clasificados** | El Mundo/El Sol de Tehuacán (if web classifieds exist) | Low, offline-origin | Free-text | Investigate; many are print-only |

**Excluded on purpose:** Airbnb, Expedia, VRBO, Booking (vacation/short-term); car-rental
suppliers — all surfaced in search noise, all out of product scope.

**Source strategy:** start with **#1 + #2 (Facebook)** for the local moat and **#4 (Mercado
Libre API)** for clean structured data, then add the HTML portals (#3, #5–#7) as
verified-scrapable. Aggregators (#9) only if direct coverage is thin.

## 6. Agent design (fits the existing `discover/` pattern)

New file `src/scripts/discover/rentas.py`, subclassing `DiscoveryAgent` exactly like
`facebook.py`/`gmaps.py`:

- **`build_plan()`** — the search plan is **geography × listing-type** (renta) rather than
  the business `taxonomy.json`. Types: `casa`, `departamento`, `local`/`comercial`,
  `terreno`, `cuarto`. Points come from `towns.json` (reuse the ring logic in `gmaps.py`).
  Facebook Marketplace uses its own category + location UI; portals use their Tehuacán URL.
- **`scrape_item()`** — per source adapter: parse listing cards → `{key, title, price,
  currency, kind(casa/depto/local…), operation:'renta', beds, baths, m2, colonia, address,
  lat, lon, phone?, url, source, photo?}`. Coordinates when the source gives them; else
  null (Layer-B text gate resolves the town).
- **Geo-gate** — call `geo.scope_of()` (from `discover-geo-scope.md`); store resolved
  `town`; drop non-matches; log drop reasons.
- **`_key()`** — stable per source: portal listing id; for Facebook, the Marketplace item
  id / post permalink id. Idempotent upsert (the base `Store` already dedupes by key).
- **`verify_record()`** — re-open the listing URL; a 404 / "no longer available" / "ya no
  está disponible" marks it **dead** (rented/removed). This is the freshness engine.
- Distinct SQLite store `resources/discovery/rentas.db` (base `Store` schema + rental
  columns), same lifecycle (`candidate|approved|rejected|dead`).

**Cross-source dedup** (the same house on FB *and* a portal): a `unify`-style pass keying
on normalized (price bucket, kind, colonia, ~coord or phone). Prefer the record with
coordinates; keep all source links.

## 7. Publish feed — `resources/map-data/rentas.js`

Mirrors `discovery.js`/`events.js`: a single JS const the app loads and merges. Only
records that are (a) alive and (b) geo-resolved get published.

```js
const RENTAS = {"rentas":[
  {t, p, mo, k, op, br, ba, m2, col, town, c:[lon,lat], u, src, ph, x}
]}
// t=title  p=price  mo=currency("MXN")  k=kind(casa|depto|local|terreno|cuarto)
// op="renta"  br=beds ba=baths m2=area  col=colonia  town=resolved town
// c=[lon,lat] (omitted if no coords — listed but not pinned)  u=source URL
// src=source id (fb|ml|inmuebles24|vivanuncios|lamudi|…)  ph=thumb URL (optional)
// x=1 when location is approximate (town-matched, no exact coords)
```

Records without coordinates are **listed** (searchable in the feed) but not **pinned** —
same convention `23_publish_discovery.py` already uses for no-coord records. Publish script
= `src/scripts/26_publish_rentas.py` (next free number).

## 8. Legal / ToS / ethics

- **Prefer official APIs** where they exist (Mercado Libre). For HTML portals and Facebook,
  respect the same posture the existing agents use: signed-in human-like sessions, low
  throttle, no bulk media re-hosting.
- **Link back, don't replace.** Every published record carries `u` → the original listing.
  We drive traffic to the source, we don't republish their content wholesale. Store
  minimal fields + a thumbnail; the full listing lives at the source.
- **No personal data.** Capture the listing and its public contact (a phone in the post is
  the poster's chosen contact) — never scrape renter/inquirer data, never a private group's
  members.
- **Attribution + takedown:** show the source; honor removal requests. Flag this section
  for a human legal review before the portal (non-Facebook) adapters go live.

## 9. Metrics / done

- **Coverage:** ≥ N live, geo-valid rental listings for Tehuacán across ≥3 sources.
- **Locality precision:** manual audit of a sample shows ~0 out-of-scope listings in the
  feed (the geo-gate is doing its job).
- **Freshness:** verify pass demotes rented/expired listings within one cycle; feed ghost
  rate low.
- **Net-new:** count of FB-only listings (on no portal) — the moat metric.

## 10. Open questions

1. Which **local Facebook rental groups** to seed (need the actual group IDs, like the
   `1458432271042909` empleos group we already found)? → field/promotor input.
2. Does **Mercado Libre's API** expose real-estate items for a Tehuacán geo filter without
   a seller token, or only via seller endpoints? → spike.
3. Portal ToS: which of Inmuebles24 / Vivanuncios / Lamudi / Propiedades tolerate
   rate-limited public-page reads with link-back? → legal review (§8).
4. Photo handling — thumbnail hotlink vs. skip images entirely v1?
