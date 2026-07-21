# Launch — What I Need From You

Stickers go up in 4 days. I've made every fix that didn't need your call (see
"Done" at the bottom). These are the items that need your decision, your local
knowledge, or an action only you can take. Ordered by urgency.

---

## 1. Deploy the fixes to prod — needs your PR merge (blocks everything)

The launch fixes are committed and verified on the **`dev`** branch. Prod
(mitehuacan.mx) still serves the old build — it deploys from **`main`**, which is
protected, so I can't merge. **Prod still loads MapLibre from unpkg until this
merges.**

**Action:** review and merge `dev → main` (or tell me to open/push the PR and you
approve it). Everything below #1 is moot until this ships.

- Verified in the build: MapLibre self-hosted (0 unpkg refs), "verificando" label
  gone, intro suppressed on QR landing, long-walk warning on mobile, town coords
  fixed.

---

## 2. Sticker → route mapping — operational, only you have this (blocks printing)

The deep link only works when each printed sticker's `route_id` in D1 exactly
matches a route slug in `routes.js` (e.g. `coapan-carranza`, `22-san-marcos`).
Right now the admin `combi_lines`/`stickers` tables are **empty on prod** — no
sticker is assigned to any route yet.

**Action before printing:** for every sticker you'll place on a combi, decide
which route it rides and install it (admin QR page → install → pick the route).
Then we verify every sticker id resolves to a real slug. A sticker with no/wrong
`route_id` silently opens the generic map instead of its route.

I can build a one-shot **verifier** that lists every installed sticker and flags
any whose `route_id` isn't in `routes.js` — say the word and it's ready before you
print.

---

## 3. Where do the stickers go? — coverage decision

The map meaningfully serves **~6 of your 17 towns**: Tehuacán (66 routes) +
Ajalpan, Zapotitlán Salinas, San Gabriel Chilac, Santiago Miahuatlán (Azumbilla
near). **11 towns have no mapped route** — several are genuinely outside the combi
network (Coxcatlán 19 km, Tlacotepec 18 km).

**Decision:** place combi stickers where routes exist, or accept that a scan in an
unserved town opens a routeless map. My recommendation: **first sticker wave =
Tehuacán city + the 4–5 served towns.** Don't sticker a combi in a town we can't
route yet.

---

## 4. Zinacatepec & Monte Chiquito routes — include or not?

Two real lines exist in the data but were **excluded from the map for "no
geometry / existence unverified on the ground"**:
- `zinacatepec` — Ramal Zinacatepec–Tehuacán (44 Moovit stops)
- `tehuacan` — Monte Chiquito circuito

San Sebastián Zinacatepec is one of your service-area towns. **Decision:** do you
want these on the map? If yes, someone rides them and records the geometry (the
admin recorder does this) — then we publish. If they're not real/active, leave
them out. Your local call.

---

## 5. "Record a route → it appears on the map" is NOT automatic — set expectations

The admin recorder captures a ride's GPS beautifully, and you can trim/snap it
into a draft. But **going live is a manual engineering step**: import the draft →
edit `master_route_index.csv` → rebuild → deploy. There is no "publish" button.

**Decision:** for launch, is that fine (you tell me "publish route X" and I ship
it), or do you want me to build a **one-click publish** from a recorded draft to
the live map? The latter is ~a day of work; not launch-blocking if you're okay
with engineer-in-the-loop for now.

---

## 6. Admin security & recorder safety — ready to build, needs your go + an admin deploy

These are in the **admin repo** (separate deploy you control). All clear
improvements; I didn't touch the admin auth model without your say-so:

- **Recorder silently stops when the phone locks/backgrounds** (wake-lock
  dependency). Riders can return a truncated route thinking it worked. Fix: add a
  visible "GPS stalled — keep screen on" warning. **Strongly recommend before any
  field recording.**
- **Any field token can DELETE production routes** (no role separation). Fix:
  gate DELETE behind the admin token, or remove delete from the field page.
- **No UI to issue/revoke field tokens** — they're inserted by hand via SQL. If
  you're recruiting recorders (Monse/David), we need a token-minting step.

**Action:** tell me to implement 6a/6b/6c and you deploy the admin, or hand me the
admin deploy and I'll ship them.

---

## 7. Route dedup — needs your local knowledge (nice-to-have)

`7-san-agustin` and `7-tinaco` are 42 m apart on average — **likely the same
physical combi shown as two entries.** Also worth your eye: `c-valle`↔`rc-del-valle`,
`3-de-mayo`↔`25-3-de-mayo`, `32`↔`32-colosio`. **Are any of these the same route?**
Tell me which to merge and I'll do it. (I left them alone — merging distinct
routes is worse than a duplicate.)

---

## Done (no action needed)

Committed on `dev`, verified, ships with the #1 merge:

- ✅ Self-hosted MapLibre + basemap caching (CDN outage can't blank the app)
- ✅ Removed "Ruta 24 (verificando)" internal label
- ✅ Intro coach-mark suppressed on QR-scan landing
- ✅ Long-walk ⚠️ warning now shows on the mobile trip sheet
- ✅ Fixed `towns.json` coordinates (Ajalpan was ~25 km off) — corrects the
  discovery sweep centering
