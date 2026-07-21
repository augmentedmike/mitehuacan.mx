# Combi Route System — Full Audit (pre-sticker-launch)

Audit of everything related to combi routes and their admin, 4 days before the
sticker launch. Three subsystems reviewed: the public app's route experience,
the route dataset, and the admin route-management/recording system. Findings
verified against live prod and the code, not just field values.

## Verdict

The **rider-facing route experience is genuinely well-built and launch-ready** —
scan-to-route deep link, tiered search, trip planning, and all 77 routes render
correctly and are phone-appropriate. Prod is live and current. The launch risks
are **not** in the route UX; they are (a) two infrastructure/data-hygiene items
that can break the first scan, (b) a coverage-vs-promise decision, and (c) an
admin system whose *capture* half is solid but whose *publish* half is a manual
engineering pipeline with all-or-nothing auth.

## Verified working

- Domain live (200); prod `routes.js` MD5-matches local build — riders see current data.
- QR redirect never 404s (unknown code → home map). Sticker→route→`/?ruta=` chain wired; app pre-selects and highlights the route, shows a compact sheet, fits the map. `route_id` format matches route slugs.
- Admin `/api/lineas` returns 200 on prod → migrations 0007–0009 are applied, backend alive.
- 77 routes, all valid MultiLineString geometry, adequate point density, dual-sourced from real operator/aggregator data (rutastehuacan KML + queruta traces). No placeholder/straight-line routes.
- Recorder (`grabar.html`) is thoughtfully built for the field: GPS pre-warm, wake lock, offline buffering, crash recovery, localStorage persistence.

---

## Launch-blocking (fix before stickers go up)

1. **🔴 MapLibre + basemap load from CDN and are NOT service-worker cached.**
   `maplibre-gl@4.7.1` JS/CSS come from `unpkg.com` (index.html:21,24); tiles
   from `openfreemap.org` (780). `sw.js` precaches only same-origin shell. If
   unpkg is slow/down during a sticker blitz, first-time scanners on mobile data
   get a blank app. **Fix:** self-host maplibre JS+CSS in `/combis/`, add to SW
   `SHELL`. Highest-value hardening.

2. **🔴 The sticker→route table must be seeded and verified before printing.**
   The deep link preselects only when D1 `stickers.route_id` *exactly* matches a
   `routes.js` slug (lowercase, e.g. `coapan-carranza`). A missing/stale slug
   silently degrades to the generic map. **Action:** verify every printed
   sticker id maps to a `route_id` that exists in `routes.js`. This is the line
   between "scan → your route" and "scan → generic map."

3. **🔴 Route "24 (verificando)" leaks an internal QA label to riders.** Renders
   as name *and* alias "Ruta 24 (verificando)" (2 occurrences in routes.js). Its
   geometry is self-flagged uncertain. **Fix:** clean the label; confirm the shape.

## Coverage decision (yours to make)

4. **🔴 The map serves ~6 of the 17 service-area towns.** Directly served:
   Tehuacán (66 local routes) + Ajalpan, Zapotitlán Salinas, San Gabriel Chilac,
   Santiago Miahuatlán; Azumbilla near. **11 towns have zero mapped route**
   (Zinacatepec, San José Miahuatlán, San Antonio Cañada, Tepanco, Santa María
   del Monte, Santa Ana Teloxtoc, Cacaloapan, Santa María la Alta, Tlacotepec,
   Coxcatlán, Caipan) — several are genuinely far outside the combi network.
   **Notable:** a real `zinacatepec` line (Ramal Zinacatepec–Tehuacán, 44 Moovit
   stops) and `tehuacan` Monte Chiquito circuito exist in
   `master_route_index.csv` but were **excluded for "no geometry / existence
   unverified on the ground."** **Action:** place stickers where routes exist, or
   set expectations for the unserved towns. Don't put a combi sticker in a town
   whose scan opens a routeless map.

## Admin — capture solid, publish manual, auth all-or-nothing

5. **🟠 A recorded route does not become a live public route without a manual
   off-app pipeline.** record → edit-to-draft (`route_drafts` in D1) →
   `14_import_drafts.py` → hand-edit `master_route_index.csv` → rebuild → commit
   → deploy. No "publish" button; the public app reads static `routes.js`, never
   D1 geometry. `combi_lines` is currently **empty on prod** (0 lines, 0 drafts).
   **Action:** treat publishing a recorded route as an engineer-in-the-loop task;
   don't message "record a route and it appears."

6. **🟠 Recording silently stops when the phone backgrounds/locks.** The whole
   capture depends on `navigator.wakeLock`; on iOS a locked/backgrounded page
   suspends `watchPosition` and the upload interval with no on-screen warning —
   the rider returns a truncated route believing it worked. **Fix:** add a
   "GPS stalled — keep screen on" warning + staleness detection to the recorder.

7. **🟠 No role separation — any active field token can DELETE production lines
   and drafts.** `delLine()` is one `confirm()` tap from both the admin and the
   field recorder page. A shared/lost field token = destructive access. **Fix:**
   gate DELETE behind `STATS_TOKEN`, or remove delete from the field page.

8. **🟠 No UI to issue/revoke field tokens.** `field_tokens` rows are inserted by
   hand via SQL. Plan the token-minting step before recruiting recorders.

## Quick wins / polish

9. **🟡 Likely un-merged duplicate `7-san-agustin` ↔ `7-tinaco`** (42 m mean NN,
   below the 60 m merge threshold — same physical combi shown twice). Also check
   `c-valle`↔`rc-del-valle`, `3-de-mayo`↔`25-3-de-mayo`, `32`↔`32-colosio`.

10. **🟡 `towns.json` has wrong coordinates** for Ajalpan (~25 km off), San José
    Miahuatlán, San Gabriel Chilac (introduced this session via Nominatim). Does
    NOT affect route rendering (routes use accurate place coords) but mis-centers
    the discovery sweep for those towns. **Fix:** correct the coords.

11. **🟡 First-run intro popover collides with the QR landing** — a first scan
    opens the route sheet, then the coach-mark fires ~1.4 s later over an
    already-answered screen. **Fix:** early-return the intro when `?ruta=` is set.

12. **🟡 The promised long-walk ⚠️ warning never renders on mobile.** The
    `longWalk` caveat only fires in the dead desktop planner; the live mobile
    trip sheet shows raw "camina 2.0 km" with no warning. **Fix:** surface it in
    `renderTripSheet`.

## Non-blocking notes

- Editor uses the public OSRM demo server (rate-limited) and fetches published
  geometry from pages.dev — both degrade gracefully.
- `denue`/`calles` search tiers lazy-load at +2.5 s (business/street search is
  thin for the first moments after a scan).
- `stop_events` (PARADA taps) captured but unused downstream. Dead desktop
  search/planner code exists but is unreachable (`isMobile` always true).

---

## Recommended pre-launch order

**Must fix (technical, ~half a day):** #1 self-host maplibre + SW, #3 clean the
"verificando" label, #11 intro guard, #12 long-walk warning. **Then rebuild +
deploy.**
**Must decide (yours):** #4 sticker placement policy, #5 publish expectations.
**Must verify (operational):** #2 seed & check the sticker→route table before
printing.
**Should fix soon:** #7 lock down DELETE, #6 recorder GPS-stall warning.
**Nice:** #9 dedup, #10 towns.json coords.
