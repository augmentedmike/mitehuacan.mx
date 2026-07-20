# Launch Execution Plan

Based on: MARKETING.md (Phase 0 + Phase 1), PRD-backoffice.md, current production state.

## Status check (prod)

| Check | Status |
|---|---|
| mitehuacan.mx | ✅ 200 |
| mitehuacan.pages.dev | ✅ 200 |
| Routes on map | 80/82 with geometry |
| Geo search / planner | ✅ |
| DENUE (28.7k businesses) | ✅ |
| QR deep-link handler | ✅ `/qr/[id].js` |
| Sponsor pins API | ✅ `/api/sponsor-pins` |
| D1 (sponsors, stickers, contracts) | ✅ schema ready |

## Gaps found

| Gap | Action |
|---|---|
| Zinacatepec (moovit-only, no geometry) | Record with Traccar — see §Recorder |
| Coxcatlán (not in dataset) | Record with Traccar — see §Recorder |
| Tequexco (field report, missing) | Record with Traccar — see §Recorder |
| San José route (field report, missing) | Record with Traccar — see §Recorder |
| Ruta 23 - San Isidro (incomplete) | Re-ride with Traccar |
| Zero stickers generated | 100 QR codes generated in batch 2026-07-A |
| Zero sponsors signed | Top-5 prospect routes identified (§Prospects) |
| Stickers not in D1 | Run `wrangler d1 execute` seed |

---

## 1. QR Sticker Blitz (Phase 0 — Week 1)

### What was done
- **Script**: `tehuacan/scripts/19_generate_stickers.py` — generates QR code PNGs for printable A4 sheets
- **Batch**: `2026-07-A` — 100 stickers printed across 10 A4 sheets
- **Distribution**: evenly across the top-10 highest-prospect-density routes (15, 43, 5-A, 3, 5, 29-san-lorenzo, 4, 28-san-lorenzo, 24-dina, 20)
- **Format**: 30×30 mm stickers, 10 per A4 sheet, 300 DPI

### To finish
1. Print the 10 sheets (`tehuacan/stickers/2026-07-A/sheets/sheet_*.png`)
2. Cut into individual stickers
3. Seed D1:
   ```bash
   wrangler d1 execute mitehuacan --remote \
     --command "$(python3 -c "
       import csv
       for r in csv.DictReader(open('tehuacan/stickers/2026-07-A/stickers.csv')):
         print(f\"INSERT OR IGNORE INTO stickers (id, batch, status, route_id) VALUES ('{r['id']}', '{r['batch']}', '{r['status']}', \\\"{r['route_id']}\\\");\")
     ")"
   ```
4. Install on the highest-value routes first (see placement schedule below)

### Placement schedule

| Day | Route | Stickers | Where to place |
|---|---|---|---|
| Day 1 | Ruta 15 (centro corridors) | 10 | 10 combis at peak hours, centro stops |
| Day 2 | Ruta 43 (San Lorenzo spine) | 10 | Inside top of windshield, upper corner |
| Day 2 | Ruta 5-A (east-west corridor) | 10 | Randomize across 10 different combis |
| Day 3 | Ruta 3 (centro-San Lorenzo) | 10 | 10 combis at base of route |
| Day 3 | Ruta 5 (south corridor) | 10 | Replace any that failed adhesion |
| Day 4 | Ruta 29 San Lorenzo | 10 | Concentrate on combis with San Lorenzo branding |
| Day 4 | Ruta 4 (centro-boulevard) | 10 | Window upper-right corner |
| Day 5 | Ruta 28 San Lorenzo | 10 | Inside rear window |
| Day 5 | Ruta 24 Dina | 10 | Rotate through different times |
| Day 6 | Ruta 20 (centro-zona alta) | 10 | Near driver, visible to all passengers |

### Sticker placement technique
- **Location**: Inside the combi, top-center of the windshield OR upper-right of the driver's partition — visible to all riders, not obstructive
- **Surface**: Clean with alcohol wipe first, apply dry
- **Log**: Install each sticker via the admin panel at `/system/stickers` or record in D1 directly:
  ```sql
  UPDATE stickers SET status='installed', route_id='15', unit_desc='combi blanca placas X', installed_at=datetime('now') WHERE id='2026-07-A-0001';
  ```

### Barter placards (storefront QR stickers)
- **Format**: Slightly larger QR (8×8 cm) with "Encuentra esta ruta en mitehuacan.mx" text
- **Targets**: 10-15 tienditas, tortillerías, mercados along the top-10 routes
- **Seed sponsors**: These barter pins populate the map BEFORE paid sales calls
- **Script**: `tehuacan/scripts/19_generate_stickers.py` can be adapted — run with `--batch 2026-07-A-barter --count 20 --route <specific-route>`

---

## 2. Sponsorship: Top 5 Routes to Sell First

From `tehuacan/prospects/_summary.csv` — ranked by priority-1 prospects (foot-traffic businesses within 150 m):

| Rank | Route | Total prospects | Priority-1 targets | Best first targets |
|---|---|---|---|---|
| 1 | Ruta 15 | 5,460 | 1,901 | Farmacias, restaurantes, estéticas on Av. Independencia corridor |
| 2 | Ruta 43 | 4,997 | 1,730 | Consultorios/dentistas, papelerías near San Lorenzo |
| 3 | Ruta 5-A | 4,339 | 1,721 | Abarrotes, ferreterías, talleres on east-west spine |
| 4 | Ruta 3 | 4,295 | 1,699 | Farmacias, veterinarias, gimnasios centro-San Lorenzo |
| 5 | Ruta 5 | 4,248 | 1,669 | Restaurantes, refaccionarias, llanteras on south corridor |

### Sales strategy per route
- **Ruta 15**: Dense centro corridor. Walk Av. Independencia from 3 Sur to 9 Oriente. Lead with the demo: open the route on your phone, show their block, close on the spot.
- **Ruta 43**: San Lorenzo residential-commercial mix. Target consultorios and estéticas near the market.
- **Ruta 5-A**: Long east-west. Split into segments — hit 3 blocks per afternoon.
- **Ruta 3**: Mix of residential and commercial. Target farmacias first (most likely to say yes at $250/mo founding rate).
- **Ruta 5**: South corridor to San Nicolás Tetitzintla. Target the refaccionarias and llanteras.

### Barter seed targets (free pins, wall space in return)
- Tortillerías on each of the top 10 routes (one per route = 10)
- Mercado 16 de Marzo vendors
- Known neighborhood references (panaderías, abarrotes with 20+ year history)

---

## 3. Missing Routes: Record the Tehuacán-Zinacatepec-Coxcatlán Corridor

### What's known from field reports
- The "Tecoxteo" combis serve: Tehuacán → Tequexco → San Sebastián Zinacatepec → Coxcatlán
- At least 2 variants exist (one via Ajalpan corridor, one direct)
- Zinacatepec exists in the dataset as moovit-only with no geometry

### Recording workflow

1. **Install Traccar Client** on a phone (see `traccar-rider-guide.md`)
2. **Configure** with device ID like `mauricio-1`, server URL from the coordinator
3. **Record the following rides** (at minimum):

| Ride | Route to follow | Expected duration |
|---|---|---|
| Ida | Tehuacán centro → Zinacatepec (main route) | ~45-60 min |
| Vuelta | Zinacatepec → Tehuacán centro | ~45-60 min |
| Ida | Zinacatepec → Coxcatlán (continuation) | ~30-45 min |
| Vuelta | Coxcatlán → Zinacatepec | ~30-45 min |
| Variant | Tehuacán → Tequexco → Zinacatepec | ~60 min |

4. **Export** after each ride (note the time window):
   ```bash
   python3 tehuacan/scripts/13_traccar_export.py \
     --device mauricio-1 \
     --from "2026-07-20T09:00" --to "2026-07-20T10:00" \
     --slug tecoxteo-zinacatepec-ida
   ```

5. **Add to master index** — create rows in `tehuacan/data/master_route_index.csv`:
   ```
   tecoxteo-zinacatepec,Tecoxteo - Tehuacán → Zinacatepec (Ida),foránea,field-ride,yes,geojson/field/tecoxteo-zinacatepec-ida.geojson,no,no,no,no,,,,
   tecoxteo-zinacatepec-vuelta,Tecoxteo - Zinacatepec → Tehuacán (Vuelta),foránea,field-ride,yes,geojson/field/tecoxteo-zinacatepec-vuelta.geojson,no,no,no,no,,,,
   coxcatlan-ida,Tecoxteo - Zinacatepec → Coxcatlán (Ida),foránea,field-ride,yes,geojson/field/coxcatlan-ida.geojson,no,no,no,no,,,,
   coxcatlan-vuelta,Tecoxteo - Coxcatlán → Zinacatepec (Vuelta),foránea,field-ride,yes,geojson/field/coxcatlan-vuelta.geojson,no,no,no,no,,,,
   tequexco-var,Tecoxteo - Tehuacán → Tequexco (Variante),foránea,field-ride,yes,geojson/field/tequexco-var.geojson,no,no,no,no,,,,
   ```

6. **Rebuild the map**:
   ```bash
   python3 tehuacan/scripts/06_build_map.py
   python3 tehuacan/scripts/12_build_sponsors.py
   python3 tehuacan/scripts/15_build_pois.py
   python3 tehuacan/scripts/09_build_site.py
   python3 tehuacan/scripts/18_prospects.py
   ```

7. **Deploy**:
   ```bash
   wrangler pages deploy site --branch main
   ```

### Boundary note
Coxcatlán is ~[-97.14, 18.27] — about 30 km south of Tehuacán's current boundary center. The boundary auto-recomputes in `06_build_map.py` (radius_km). Adding Coxcatlán traces will grow the circle automatically.

---

## 4. Weekly Operations Cadence

### Monday — Route recording
- Ride any routes flagged `needs human review` or `field report` pending
- Priority: Coxcatlán corridor, then San José route, then Ruta 23 San Isidro re-ride

### Tuesday — Sales (field)
- 2 afternoon hours, 8-10 visits
- Work one of the top-5 routes per session
- Demo: open the route, show their block, ask for WhatsApp

### Wednesday — Sales (field or follow-up)
- Follow up with "let me think about it" leads from Tuesday
- 2 afternoon hours, 5-6 visits

### Thursday — Stickers
- Install 10-20 stickers per week (20 remaining per batch after day 1)
- Check on existing stickers (are they still there? clean? peeling?)
- Log status changes in D1

### Friday — Ops & data
- Check DAU, scans, and sponsor impressions in the hub
- Run `18_prospects.py` if new routes were added
- Review dead stickers (0 scans in 30 days → move)
- Prepare Monday's ride list

### Daily
- Check `mitehuacan.mx` is up
- Check sticker scans (are any routes getting traction?)
- Check contract pipeline

---

## 5. Contracts & Pricing (from MARKETING.md)

| | Founding (first 100) | Standard (after) |
|---|---|---|
| Pin, per location / month | **$250-400 MXN** | $500-800 MXN |
| Minimum term | 6 months | 3 months |
| Barter placard | wall space + placard stays up | (phased out) |
| Founding lock | rate frozen while active | — |

### Sales script (10-minute visit)
1. Walk in at quiet hour, ask for owner, phone out with app open
2. Select the route that passes the door, zoom to their block
3. *"Todos los días, cientos de personas toman esta ruta. Cuando abren mitehuacan.mx para ver su combi, ven los negocios que están sobre la ruta."*
4. Show a seeded (or barter) sponsor pin, tap it
5. *"Su negocio está aquí. Por $X al mes, su logo aparece a cada persona que ve esta ruta."*
6. Close: *"¿A qué WhatsApp le mando el contrato?"* — send from `/patrocinios`, watch them sign

---

## Appendix: File reference

| Path | Purpose |
|---|---|
| `tehuacan/scripts/19_generate_stickers.py` | QR sticker generator (batch + CSV + sheets) |
| `tehuacan/scripts/13_traccar_export.py` | Export Traccar rides to geojson |
| `tehuacan/scripts/14_import_drafts.py` | Import drafts from the editor |
| `tehuacan/scripts/18_prospects.py` | Generate sales prospect lists per route |
| `tehuacan/prospects/_summary.csv` | All routes ranked by prospect density |
| `tehuacan/prospects/15.csv` | Ruta 15 prospect list (door-knock sheet) |
| `tehuacan/data/master_route_index.csv` | Every route — add new ones here |
| `tehuacan/data/field_reports.json` | Known data gaps requiring field work |
