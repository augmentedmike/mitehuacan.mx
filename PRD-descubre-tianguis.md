# PRD — Descubre: Mi Tianguis (marketplace discovery agent)

**Status:** Draft v1
**Owner:** Michael
**Date:** 2026-07-24
**Section:** `/descubre/` → **Mi Tianguis** (currently "Coming soon")
**Scope of this PRD:** agent + data feed only — a new discovery agent in
`src/scripts/discover/` and a publish script emitting a `.js` feed, matching the existing
`discovery.js` / `events.js` pattern. **No** new D1 table, public API, or UI yet.
**Depends on:** `discover/lib.py` `DiscoveryAgent` base ·
[`business/discover-geo-scope.md`](business/discover-geo-scope.md) (hard geo limit) ·
[`business/cold-start-playbook.md`](business/cold-start-playbook.md)

---

## 1. Problem

`/descubre/` promises "Mi Tianguis — Tehuacán's online marketplace: buy and sell between
neighbors, commission-free," with no data behind it. Local buy/sell already happens at
enormous volume — but almost entirely inside **Facebook Marketplace** and local FB
buy/sell groups, plus some Mercado Libre and Vivanuncios. There is no local-first,
geo-filtered view; Marketplace's own radius bleeds in Puebla-capital and beyond.

Posture matches the other verticals: **aggregate the local buy/sell supply into one
geo-filtered feed and link back to the seller's listing.** The "commission-free" promise is
literally true because we don't intermediate the sale at all — we make local inventory
legible and hand the buyer to the seller's existing channel (Marketplace/WhatsApp). A
first-party self-serve "publica tu artículo" intake can come later; this PRD is discovery
only.

> **Note — biggest surface, noisiest.** Marketplace is the highest-volume and lowest-signal
> of the three missing sections. Expect to lean hardest on the geo-gate and on category
> curation here. Recommend sequencing this **after** rentas/empleos prove the pattern.

## 2. Strategic fit

- **Everyday-habit surface.** Buy/sell is the most frequent casual reason to browse — big
  DAU potential into the same organic funnel.
- **Pure aggregation, zero rake** — consistent with "never a rake on the cash close" and
  "inject structure into the incumbents." We're a local lens on Marketplace, not a
  competitor to it.
- **Reuses built-once rails** (harness, geo-gate, publish→`.js`, and the *exact* Facebook
  session machinery already in `facebook.py`/`fb_events.py`).

## 3. Goals

1. A **tianguis agent** harvesting current local buy/sell listings across the source set
   (§5), deduped, geo-gated to the 17-town boundary, category-tagged, into its own store.
2. A **publish script** → `resources/map-data/tianguis.js` (§7), link-back to the listing.
3. **Expiry:** sold/removed items demoted quickly (marketplace churns fastest of all).
4. **Hard geo limit** per [`discover-geo-scope.md`](business/discover-geo-scope.md).

## 4. Non-goals

- No new DB table / API / UI (later PRD).
- No first-party listing intake yet; no payments, no escrow, no messaging relay.
- No scraping of buyer messages, seller profiles, or group membership — public item
  listings only.
- No bulk re-hosting of item photos (thumbnail hotlink + link-back only).

## 5. External data sources (all of them, ranked by local value)

Facebook is overwhelmingly dominant for local C2C; the rest are secondary.

| # | Source | URL | Tehuacán coverage | Structure | Access notes |
|---|--------|-----|-------------------|-----------|--------------|
| 1 | **Facebook Marketplace** (Tehuacán, all categories) | facebook.com/marketplace/… | **Dominant** — the local marketplace | Loose (title, price, category, colonia, photos; coords rare) | Signed-in profile (proven); location=Tehuacán + smallest radius; **geo-gate does the real enforcement** |
| 2 | **Local Facebook buy/sell groups** | "Compra Venta Tehuacán", "Bazar Tehuacán", "Se vende en Tehuacán", etc. | High, hyper-local | Free-text posts | Same session; per-group feed; text town/colonia match |
| 3 | **Mercado Libre** | listado.mercadolibre.com.mx (+ `inmuebles`/`vehiculos` verticals) | Moderate; national but filterable to Puebla/Tehuacán sellers | **Structured**; **official API** | **Prefer the API** (developers.mercadolibre.com.mx) — items search, seller location, categories — cleanest + best-licensed source |
| 4 | **Vivanuncios** (general classifieds, not just inmuebles) | vivanuncios.com.mx (vehículos, electrónica, hogar…) | Low–moderate | Structured | Classifieds portal; link back |
| 5 | **Marketplace/classifieds aggregators** | (various) | Mirror of above | Structured | Only if needed; dedup-heavy |
| 6 | **Segundamano / vibbo** | — | ~defunct in MX (redirected/closed) | — | Historic; skip unless a live MX successor exists |
| 7 | **Local newspaper clasificados** | El Mundo/El Sol de Tehuacán | Low, offline-origin | Free-text | Investigate web classifieds |

**Excluded:** anything outside the C2C buy/sell scope — the rentas and empleos verticals
have their own agents; a Marketplace "Propiedades/Empleos" hit should be routed to (or left
to) those agents, not duplicated here.

**Source strategy:** **#1 + #2 (Facebook)** are the product — start there. **#3 (Mercado
Libre API)** for clean structured supply. #4 only if it adds local volume.

## 6. Agent design

New `src/scripts/discover/tianguis.py`, subclassing `DiscoveryAgent`:

- **`build_plan()`** — plan is **category × location**. A marketplace taxonomy (own file,
  like the businesses' `taxonomy.json`): vehículos, electrónica y celulares, hogar y
  muebles, ropa y calzado, herramientas, bebés y niños, mascotas, deportes, agro/campo,
  otros. Facebook Marketplace has native categories + a location/radius UI; Mercado Libre
  uses category IDs + a Tehuacán/Puebla geo filter via API.
- **`scrape_item()`** — per-source adapter → `{key, title, price, currency, category,
  condition?, colonia?, lat?, lon?, url, source, photo?, posted_at, contact?}`.
- **Geo-gate** — `geo.scope_of()`; store resolved `town`; drop non-matches; log drops. This
  is the **most-loaded** geo-gate of the three — Marketplace radius overshoots hard.
- **`_key()`** — Marketplace item id / group-post id / ML item id; idempotent upsert.
- **`verify_record()`** — re-open the listing; "artículo vendido" / removed / 404 →
  **dead.** Also age-out (items go stale fast — e.g. 30-day max).
- Store `resources/discovery/tianguis.db`; standard lifecycle.

**Dedup:** cross-post of the same item to Marketplace **and** several groups is rampant.
Key on normalized (title, price, seller-or-colonia); collapse to one record, keep all
links.

## 7. Publish feed — `resources/map-data/tianguis.js`

```js
const TIANGUIS = {"tianguis":[
  {t, p, mo, k, cond, col, town, c:[lon,lat], u, src, ph, d, x}
]}
// t=title  p=price  mo=currency("MXN")  k=category  cond=condition(nuevo|usado|null)
// col=colonia(optional)  town=resolved town
// c=[lon,lat] (omit if none — listed, not pinned)  u=listing URL  src=source id
// ph=thumb URL(optional)  d=posted/seen ISO date  x=1 when location approximate
```

Most items will be **listed, not pinned** (Marketplace rarely exposes coordinates) — the
feed is primarily a browsable/searchable list with an optional map for the geocoded subset.
Publish script `src/scripts/28_publish_tianguis.py`.

## 8. Legal / ToS / ethics

- **Prefer the Mercado Libre API** over any HTML scraping where it covers the need.
- Facebook Marketplace/groups: same posture as the existing FB agents — signed-in
  human-paced sessions, low throttle, minimal fields, **no bulk media re-hosting**, and
  **link back** to the seller's listing (we send buyers to them). This is the highest-ToS-
  risk source; keep volume modest and human-like.
- **No personal data** beyond the public listing + the seller's chosen public contact; no
  group-membership or buyer-message capture.
- Attribution + takedown honored. Human legal review before launch given Marketplace is the
  most sensitive surface.

## 9. Metrics / done

- **Coverage:** ≥ N live, geo-valid local items across the top categories.
- **Locality precision:** sample audit ~0 out-of-scope items (the hardest geo-gate — watch
  this closely).
- **Freshness:** sold/removed items demoted within a cycle; low ghost rate.
- **Signal:** category-tag accuracy on a sample (marketplace titles are messy).

## 10. Open questions

1. Which **local FB buy/sell groups** to seed (need real group IDs)? → promotor input.
2. **Mercado Libre API**: does the public items-search expose a usable Tehuacán/Puebla geo
   filter without per-seller auth? → spike (shared with the rentas PRD's ML question).
3. Category taxonomy — adopt Facebook Marketplace's categories, Mercado Libre's, or a
   MiTehuacán-native short list? Recommend a small native list mapped from both.
4. Given noise + ToS risk, confirm **sequencing after rentas/empleos** (recommended in §1).
