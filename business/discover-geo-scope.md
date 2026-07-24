# Discovery Geo-Scope — the hard Tehuacán boundary

*2026-07-24. The single, shared geographic gate for **every** discovery agent — the
existing business/event agents (`google`, `instagram`, `facebook`, `fb_events`,
`gov_events`) and the three new classifieds agents (`rentas`, `empleos`, `tianguis`)
specced in [`PRD-descubre-rentas.md`](../PRD-descubre-rentas.md),
[`PRD-descubre-empleos.md`](../PRD-descubre-empleos.md),
[`PRD-descubre-tianguis.md`](../PRD-descubre-tianguis.md).*

> **The rule, in one line:** a record is kept **only** if it resolves to Tehuacán or one
> of its 16 surrounding service-area towns. Everything else is dropped at scrape time —
> not published, not stored as a candidate. When in doubt, drop it.

This is a **hard limit on purpose.** The whole product thesis (see
[`cold-start-playbook.md`](cold-start-playbook.md) §4, "win one corridor completely") is
depth in one place, not a thin national layer. A Puebla-capital rental or a CDMX job
posting is noise here and actively hurts trust. Better to show 30 real local listings
than 3,000 that make a Tehuacano feel the app isn't for them.

## 1. The canonical town set

The boundary is defined **once**, by `src/scripts/discover/towns.json` — the 17 towns the
combi map already serves (Tehuacán + 16). No agent hardcodes its own list; they all read
this file. Adding/removing a town is a one-file edit that every agent inherits.

Current set: Tehuacán (center), Ajalpan, Azumbilla, Caipan, Coxcatlán, San Andrés
Cacaloapan, San Antonio Cañada, San Gabriel Chilac, San José Miahuatlán, San Sebastián
Zinacatepec, Santa Ana Teloxtoc, Santa María del Monte, Santa María la Alta, Santiago
Miahuatlán, Tepanco de López, Tlacotepec de Benito Juárez, Zapotitlán Salinas.

Tehuacán is the anchor; the rest are the ring the promotor's network and the transit map
already cover. **Anything outside this list is out of scope**, including nearby-but-bigger
places (Puebla capital, Orizaba, Tecamachalco unless added).

## 2. Two-layer gate

Every agent applies the same two checks, in order. A record must pass **both**.

**Layer A — query scoping (before the request).** Constrain the source so it returns
mostly-local results in the first place: town-name search terms, portal location filters
set to Tehuacán, Facebook Marketplace location = Tehuacán with the **smallest** radius the
UI allows that still covers the ring (~30 km from center reaches the outer towns but also
overshoots — Layer B is what actually enforces the boundary). Query scoping reduces waste;
it is **not** trusted to enforce the limit.

**Layer B — the geofence (after parsing, before upsert).** The authoritative gate,
implemented once in `src/scripts/discover/geo.py`:

```
scope_of(record) -> town_name | None

  if record has (lat, lon):
      # coordinate path — the strong signal
      if not inside BBOX:                  return None      # fast reject
      t = nearest town within its radius;  return t or None
  else:
      # text path — for listings with no coordinates (most FB posts)
      return town_match(title + " " + location_text + " " + body)
```

- **BBOX** = bounding box of `towns.json` extremes + ~0.03° (~3 km) margin.
  Currently ≈ **lat [18.23, 18.72], lon [-97.69, -97.11]**. Recomputed from the file, not
  a magic constant, so it tracks town edits.
- **Per-town radius** for the coordinate path: **8 km** for Tehuacán (large city), **6 km**
  for each smaller town. A coordinate must fall inside *some* town's ring, not just the box
  (the box's corners are empty desert).
- **`town_match(text)`** for the no-coordinate path: normalize (lowercase, strip accents)
  and require a whole-word hit on a town name **or** a Tehuacán colonia/fraccionamiento
  from a gazetteer (§3). "renta centro tehuacan" ✓, "depto valle de las flores" ✓ (known
  colonia), "renta en puebla" ✗, "renta cdmx" ✗. A post that names *only* an out-of-scope
  place is dropped even if it also says "Puebla" (the state) — state-level mentions don't
  count.

Records that return `None` are **discarded, not stored** — they never become candidates,
so they can't leak into a publish feed later.

## 3. The Tehuacán colonia gazetteer

Most informal listings (Facebook especially) have **no coordinates** and only a colonia
name. To resolve those, `geo.py` loads a gazetteer of in-scope colonias/fraccionamientos.

- **Seed it from data we already have:** the DENUE Tehuacán extract
  (`resources/poi/denue_*.csv`, 28k+ rows) carries `cve_ent`/`cve_mun`/colonia fields —
  derive the set of colonia names inside the Tehuacán municipio (and the other towns'
  localidades) and cache them to `discover/colonias.json`. This reuses the built-once
  national layer instead of hand-typing neighborhoods.
- Fold in colonias already present in the `negocios`/`places` tables (field-captured,
  authoritative).
- Treat the gazetteer as **allow-list, not reject-list**: a colonia we don't recognize
  falls back to requiring a town-name hit. Unknown-and-no-town → drop.

## 4. What each agent must expose

To keep the gate honest and auditable, every agent:

1. Calls `geo.scope_of()` and **stores the resolved town** on the record (`town` column).
   A published record always knows which town it belongs to.
2. Counts and logs drops by reason (`out_of_bbox`, `no_town_match`, `out_of_state`) so we
   can see how much a source is over-reaching and tune Layer A.
3. Never publishes a record whose `town` is null.

## 5. Non-goals / edge cases

- **Vacation/short-term rentals (Airbnb, Expedia), car rentals, hotels** are out of scope
  for the rentas agent regardless of geography — different product. Geo-gate is orthogonal
  to the per-agent category filter.
- **Remote jobs** ("home office / remoto") that are otherwise local-employer are a judgment
  call handled in the empleos PRD, not here — the geo-gate keys on employer location when
  present, else town_match, else drop.
- **State vs. city ambiguity:** "Puebla" alone is the state or the capital, never assume
  Tehuacán. Only the explicit town/colonia tokens count.
