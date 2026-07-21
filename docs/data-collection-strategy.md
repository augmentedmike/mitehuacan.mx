# Data Collection Strategy — Curate the Zone

**Goal:** aggregate *all* local data inside the service-area boundary — every
business, street, and combi route now; every job, fiesta, and service over time.
Outside the boundary we ignore. The data itself is the asset: the most complete,
current picture of Tehuacán and its 16 surrounding towns that exists anywhere.

This document is the plan. It's grounded in what's already built (the `discover/`
package, the lifecycle stores, the town rotation) and lays out how each piece
extends toward "ad infinitum."

---

## 1. The zone is fixed; coverage is a rotation

The service area is **17 towns** (`src/scripts/discover/towns.json`), geocoded
from Mike's boundary. Everything we collect must fall inside it. This is the one
hard filter — it's what makes "complete" a finite, achievable target instead of
an infinite one.

Coverage is a **grid we rotate through**, not a single sweep:

```
        every TOWN  ×  every CATEGORY  ×  every SOURCE
```

- **Towns** — 17 centers (Tehuacán also gets rings, being large). Each is a
  search origin. `towns.json`.
- **Categories** — the shared taxonomy (`taxonomy.json`), 83 subcategories today,
  editable in one place for all agents. Plus **seed names** (`seeds.txt`) for
  brand-named shops that don't rank for category terms (the Yoms! case).
- **Sources** — Google, Instagram, Facebook now; more below.

A run does a bounded batch of this grid and advances a **persistent cursor**, so
repeated runs walk the whole grid without repeating and the daily chain keeps it
moving on its own. Over weeks the cursor laps the grid; each lap catches what's
new or changed. This is the engine that makes the collection *constant and
complete* rather than one-and-done.

---

## 2. Multi-source, because each source sees different data

No single source has everything. The strategy is to aggregate across sources that
each hold a slice, then merge them. What each brings:

| Source | Uniquely strong for | Status |
|---|---|---|
| **Google Maps** | businesses with exact coords, hours, and a live "permanently closed" signal — the backbone for location + verification | ✅ built |
| **Instagram** | IG-native shops that exist on *no* listing service — the long tail (Yoms!) | ✅ built |
| **Facebook** | business Pages, and later **Events** (fiestas), **Marketplace** (jobs/services) | ✅ Pages built; Events/Marketplace next |
| **INEGI DENUE** | the registered-business ground truth (~40k) — free bulk reference | ✅ built |
| **OpenStreetMap** | streets + intersections (the `calles` layer), civic POIs | ✅ built |
| **Delivery platforms** (DiDi Food / Uber Eats / Rappi) | menus, hours, and businesses that only appear where they take orders | ▢ roadmap |
| **Municipal / news / event pages** | fiestas, public services, closures | ▢ roadmap |

**The multiplier is cross-source, not any one source.** The same business shows
on Google + IG + FB with different fields; merged, it becomes one rich record
(location from Google, handle from IG, events from FB). That merged, deduped,
verified dataset is the thing that's worth something — no competitor is building
it for this zone.

---

## 3. Every record is maintained (persist · dedup · verify · prune)

Each source has its own SQLite lifecycle store (`<source>.db`). A record carries
`first_seen / last_seen / times_seen / status(candidate|approved|rejected|dead)`.

- **Discover** upserts by stable key — re-seen records bump `last_seen`, new ones
  insert. Idempotent: re-running finds no duplicates.
- **Dedup** against the map layers (so we don't re-collect what's already mapped)
  and against the store itself.
- **Verify/prune** re-checks live records and marks the gone ones `dead` (Google
  "permanently closed", 404'd handles) — quarantine, never delete, reversible.
- **Admin approval** (`/lugares`) is the gate before anything reaches the public
  map. Discovery produces *leads*, humans confirm.

This is what makes the dataset *stay* accurate as the town changes, instead of
rotting.

---

## 4. Cross-source entity resolution — ✅ built (`unify`)

Each source's store is separate; `unify.py` merges them into a **unified place
table** by name + location proximity:

- one canonical business ← its Google listing + IG handle + FB page
- confidence scored by how many independent sources agree (2+ = strong)
- name-variant matching strips a leading generic category word ("Restaurante
  Casa Vieja" ↔ "Casa Vieja"); a >250 m coord split keeps distinct same-name
  shops apart

This turns three noisy lists into one authoritative record per business — what
lets "Yoms! on Instagram" resolve to a pin with hours and events. **Next lever:**
deepen IG/FB coverage (they're shallow vs google), and push the highest-confidence
unified places into the admin approval queue — the last mile to the live map.

---

## 5. Data types — the road to "ad infinitum"

Same engine (zone × rotation × lifecycle store), new record types. Each is a new
agent that drops into the existing framework:

1. **Businesses** — ✅ the three agents (google/instagram/facebook), merged by
   the `unify` step into one canonical place each (cross-source resolution).
2. **Streets & intersections** — ✅ `calles` from OSM. Extend: DENUE address
   parsing to fill blocks OSM hasn't mapped (Zinacatepec-type gaps).
3. **Combi routes** — ✅ the core product; the admin `record` flow captures live
   telemetry. Discovery angle: FB/community pages that post route info.
4. **Events / fiestas** — ✅ `fb_events` agent — Facebook events per town into
   `fb_events.db`. Extend: municipal calendars; upcoming-only filter.
5. **Services** — ▢ already partly captured as business categories; formalize the
   service taxonomy (plumbers, tutors, repairs) and add the informal ones that
   only advertise on FB Marketplace / IG.
6. **Jobs** — ▢ FB Marketplace jobs, local boards, business "estamos
   contratando" posts.
7. **…** — anything geo-local with a source: transit fares, market days,
   government offices' hours. Each is a taxonomy + a source adapter + a store.

**Current harvest** (visible on the dashboard's harvest bar): ~3.9k canonical
places merged from ~3.2k google + 730 facebook + 95 instagram, plus fiestas.
Growing every run as the cursor laps the zone.

The order is deliberate: businesses first (they anchor everything with a
location), then the things that attach *to* businesses and places (events at a
venue, jobs at a business, services by a provider).

---

## 6. Operating cadence

- **Daily** — the local chain rotates the cursors a batch further through the
  grid and runs the verify/prune pass; failures notify on the desktop.
- **Weekly** — the authoritative bulk refresh (OSM, DENUE) and the cloud
  discovery routine.
- **Continuous** — as the cursor laps the zone, re-sweeps surface new openings and
  the verify pass retires the closed. The dataset trends toward complete-and-current.
- **Human in the loop** — Mike/team hold the platform sessions and approve leads;
  seed names get added as businesses are learned by name.

---

## 7. Why this wins

- **Bounded zone** makes "all the data" a finite, checkable goal.
- **Multi-source + merge** produces a record richer than any single platform.
- **Lifecycle + verify** keeps it current — the hard part competitors skip.
- **One shared config** (towns, taxonomy, seeds) means the whole system retargets
  or expands by editing plain-text files, not code.
- **Free-tier throughout** — static build artifacts for bulk reference, D1 only
  for owned/transactional data.

The moat isn't any one scraper; it's the *maintained, cross-source, zone-complete*
dataset that results — and the combi-route network layered on top of it.
