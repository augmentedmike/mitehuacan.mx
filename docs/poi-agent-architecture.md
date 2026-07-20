# POI curation agent — Google Maps–backed

## What we have today

| source | scope | update | format |
|---|---|---|---|
| OSM Overpass API | ~500 public service POIs (schools, clinics, gov) | weekly (GH Actions) | `map/pois.js` — `{n,c,k}` |
| OSM Overpass API | ~400 commercial places | weekly (GH Actions) | `map/places.js` — `{n,c,k}` |
| INEGI DENUE | ~28K registered businesses in service area | ~2x/yr manual CSV | `map/denue.js` — `{n,c,k}` |
| Google Maps | **nothing** | — | — |

All three layers are **reactive** — they use whatever the source has. No validation, no dedup quality checks, no closed detection, no AI.

## What the agent does

The agent runs on your dev machine (macOS), multiple times a day, and owns the end-to-end POI curation pipeline using Google Maps Places API.

It is a **separate script** from the existing pipeline — it feeds into it.

### 1. Category tree (the master list)

A deep hierarchy of what to search for. Lives in a config file (YAML/JSON). Radiates from town center, category by category.

```yaml
categories:
  - slug: escuela_primaria
    label: Escuelas primarias
    google_type: primary_school
    map_type: edu
    priority: 1
    radius: 500  # meters per search circle
  - slug: escuela_secundaria
    label: Escuelas secundarias
    google_type: secondary_school
    map_type: edu
    priority: 1
    radius: 500
  - slug: preparatoria
    label: Preparatorias / bachilleratos
    google_type: high_school
    map_type: edu
    radius: 500
  - slug: universidad
    label: Universidades
    google_type: university
    map_type: edu
    radius: 1000
  - slug: hospital
    label: Hospitales
    google_type: hospital
    map_type: salud
    radius: 1000
  - slug: clinica
    label: Clínicas
    google_type: doctor
    map_type: salud
    radius: 500
  - slug: farmacia
    label: Farmacias
    google_type: pharmacy
    map_type: salud  # or a new commercial tier
    radius: 300
  - slug: banco
    label: Bancos
    google_type: bank
    map_type: comercial
    radius: 300
  - slug: supermercado
    label: Supermercados
    google_type: supermarket
    map_type: comercial
    radius: 500
  - slug: tortilleria
    label: Tortillerías
    google_type: food  # Google doesn't have tortilleria as a type
    keyword: tortillería
    map_type: comercial
    radius: 300
  # ... hundreds more, structured in groups:
  #   educación → primaria, secundaria, preparatoria, universidad,
  #               biblioteca, escuela de música, escuela de idiomas...
  #   salud → hospital, clínica, farmacia, dentista, optometrista,
  #           laboratorio, veterinaria, psicólogo, fisioterapia...
  #   gobierno → palacio municipal, juzgado, policía, correos, SAT...
  #   servicios → banco, caja de ahorro, casa de empeño, notaría...
  #   comida → supermercado, tortillería, panadería, carnicería,
  #            frutería, pescadería, dulcería, cremería...
  #   tiendas → ropa, zapatos, electrónica, muebles, ferretería,
  #            papelería, regalos, juguetes, deportes...
  #   personales → estética, barbería, uñas, spa, tatuajes...
  #   auto → gasolinera, taller, refacciones, llantera, autolavado...
  #   entretenimiento → cine, gimnasio, parque, museo, teatro...
  #   alojamiento → hotel, motel, posada...
  #   religión → iglesia, templo...
```

Each entry maps a `google_type` (Places API type), optional `keyword`, search `radius`, and the internal `map_type` category (`edu|salud|gob` for public, `comercial` as a new tier, or direct chips like the existing `k`).

### 2. Search grid

Tehuacán centro is approximately `18.462, -97.397`.

```
start at center
for each category:
    # get all search circles that cover the rectangle
    for each circle in the grid that hasn't been checked recently:
        1. Places API Nearby Search (type + keyword, radius, 60 results/page)
        2. paginate through all pages
        3. for each result:
            a. deduplicate against ALL existing layers (OSM pois + places + DENUE)
            b. if new → add to "pending_add" queue with Google Place ID
        4. sleep 0.2s between calls (free tier: ~50 QPS allowed, stay safe)
```

The grid uses hex or square packing so circles overlap at edges and no area is missed. Radius per category varies (farmacias are dense — 300m; hospitales are sparse — 1000m).

### 3. Deduplication logic

```
given a Google Place result (name, lat, lng, types):
    name_normalized = strip_accents(name).lower()
    for each existing POI in any layer:
        dist = haversine(lat, lng, poi.lat, poi.lng)
        name_similar = (
            name_normalized == poi.name_normalized
            or name_normalized in poi.name_normalized
            or poi.name_normalized in name_normalized
        )
        if dist < 50 and name_similar:
            it's a duplicate → skip
            optionally: if Google name is better → flag for update
    if no match:
        POI is genuinely new → add to pending
```

50m radius + name overlap catches chains (two "Farmacia Guadalajara" branches 200m apart are distinct). Adjustable per category.

### 4. Pruning engine

The inverse: check existing POIs against Google to see if they're still open.

```
for each known POI, oldest-first:
    call Places API Place Details (Place ID if we stored it,
    otherwise Nearby Search at its location)
    if Place Details says permanently_closed → flag for removal
    if Nearby Search finds nothing at that location for 3 consecutive runs
      → flag for removal (maybe it moved, maybe it's a false negative)
    if place has new name → flag as "renamed"
```

Run at a lower frequency than the add crawl (e.g., once per category per day). Stale checks are cheaper because you have a fixed set to iterate.

### 5. Output

The agent writes a **delta file** that the existing build pipeline can consume:

```
poi/gmaps_add.json  — {n, c, k, google_place_id, google_types, source_url}
poi/gmaps_remove.json  — {google_place_id, reason: closed|renamed|bogus}
```

The existing `15_build_pois.py` and `16_refresh_pois.py` get a new step: merge in GMaps additions before the route-proximity pass, and filter out removals.

### 6. Scheduler

macOS `launchd` plist (or just a cron-like `launchctl` job). Example schedule:

| window | job |
|---|---|
| 06:00–07:00 | high-priority categories (farmacias, tortillerías, etc.) |
| 10:00–11:00 | medium-priority (schools, clinics, banks) |
| 14:00–15:00 | low-priority (everything else) |
| 22:00–23:00 | pruning run — check N oldest unknown POIs |
| 01:00–02:00 | merge & rebuild → commit + push to dev |

Each window is ~500-1000 Places API calls (well within the $200/mo free credit at $5/1000 for Places Details, or $32/1000 for Nearby Search — stay under 6000 calls/day total).

### 7. Files to create

```
tehuacan/
  poi/
    gmaps_categories.json      — the master category tree
    gmaps_add.json             — pending additions (output)
    gmaps_remove.json          — pending removals (output)
    gmaps_seen.json            — dedup tracking (Google Place IDs checked + dates)
  scripts/
    20_poi_gmaps_crawl.py      — the crawl agent itself
    21_poi_gmaps_prune.py      — the pruning agent
    22_poi_gmaps_merge.py      — merge GMaps data into the build pipeline
```

No changes to the existing scripts — the merge step feeds into them. The agent is additive.

### 8. Cost management

Google Maps Places API is not free but has a $200/mo credit:
- Nearby Search: $32/1000 calls (basic) or $40/1000 (advanced)
- Place Details: $5/1000 calls (basic) or $5/1000 (advanced)

At 6000 calls/day (200 calls/category × 30 categories), that's about $6/day for Nearby Search, $180/mo — just within the credit. Keep most calls at basic SKU (no reviews, no photos).

Text Search (keyword-based) can supplement where type-based search misses (e.g., "tortillería" is not a Google type but Text Search finds them).
