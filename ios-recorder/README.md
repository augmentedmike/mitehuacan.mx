# Grabador de Rutas — iOS route recorder

A native iOS app to record combi routes with GPS **in the background** (the phone
can sleep and it keeps recording), then **snip / join / prune** the recordings into
clean routes and attach hand-entered schedule metadata. Built to run as a free
**development build on your own iPhone** — no Apple Developer Program ($99) needed.

## What it does

- **Grabar** — records a ride. Keeps logging while the screen is locked or the app is
  backgrounded (that's the whole reason it's native, not a web app).
- **Unir / join** — a ride you record is saved as a *new route* or *joined onto an
  existing one* as another segment. Partial rides aggregate into one line — record
  half the route today, the rest tomorrow, join them. You can also merge two whole
  saved routes together.
- **Recortar / snip** — trim a segment down to a start–end range with two sliders
  (green preview shows what's kept). Use it to cut the drive-to-the-start or a wrong turn.
- **Prune** — delete a segment, a stop, or a whole route.
- **Paradas + horarios** — tap the map to drop a stop, mark it origen / parada mayor /
  última parada, and enter the schedule by hand: first & last departure and the
  interval (headway) for **weekday, Saturday, and Sunday** separately. This is what you
  fill in on the combi.

## Three sections, one switcher

The app opens on a tab switcher (`RootView`) with three areas, built to grow:

- **Rutas** — record & edit combi routes (everything below).
- **Patrocinadores** — hand-enter sponsors: name, slug, contact, logo, tier
  (intercambio / pagado), and one or more map locations. **No payments** — just data
  entry. Pushed to prod via `POST /api/admin/sponsors`.
- **Calcomanías** — scan a sticker's QR with the camera, mark where it went on the
  map (or leave it blank), and save. **Location is optional**: no location ⇒ the
  sticker is on something that moves (a combi), so the backend stores it as
  `placement = combi`; with a pin it's `fijo`. Pushed to prod via
  `POST /api/admin/stickers` (upsert, so a freshly printed code saves even if it was
  never batch-seeded).

All three use the same unlock (admin PIN) + local-first + reconcile flow. Adding a
future section is one more `.tabItem` in `RootView`.

## Files

| File | Role |
|---|---|
| `RutasRecorderApp.swift` | `@main` app entry; owns the stores + `LocationRecorder` + `AdminAuth`, shows `RootView`. |
| `RootView.swift` | Tab switcher between **Rutas**, **Patrocinadores**, and **Calcomanías** (extensible). |
| `Models.swift` | `Route` (segments = one array per ride), `Stop`, `StopKind`, `StopSchedule`, `DaySchedule`, `TrackPoint`. |
| `LocationRecorder.swift` | Core Location; background recording (Always auth + background mode). |
| `RouteStore.swift` | JSON persistence + join / snip / prune ops. |
| `RouteEditor.swift` | Route list + detail map with snip/join/prune + stop editing. |
| `StopEditView.swift` | Per-stop schedule editor (weekday/Sat/Sun first-last-interval). |
| `Sponsor.swift` | `Sponsor` + `SponsorLocation` models (identity, logo, locations). |
| `SponsorStore.swift` | JSON persistence for sponsors + reconcile bookkeeping. |
| `SponsorSync.swift` | Read/write sponsors to `/api/admin/sponsors` (admin-token gated). |
| `SponsorViews.swift` | Sponsor list, editor (logo picker + locations), map location editor, reconcile. |
| `Sticker.swift` | `StickerPlacement` model + `stickerCode(from:)` (parses `/qr/<id>` or a bare code). |
| `StickerStore.swift` | JSON persistence for placements + reconcile bookkeeping (upsert by code). |
| `StickerSync.swift` | Push placements to `/api/admin/stickers` (lat/lon optional). |
| `StickerScanner.swift` | AVFoundation camera QR scanner (`QRScannerView`). Needs `NSCameraUsageDescription`. |
| `StickerViews.swift` | Scan → locate → save flow, placement list, editor, reconcile. |
| `AdminAuth.swift` | Admin PIN unlock + Keychain token (shared across all sections). |
| `AdminUI.swift` | Unlock + route reconcile sheets. |
| `RouteSync.swift` | Read/write routes to prod (`routes.js` + `/api/admin/lineas`). |
| `Info.plist` | Location usage strings + `UIBackgroundModes: location`. |

> **Backend:** sponsors persist via `functions/api/admin/sponsors.js` (GET list +
> POST upsert with full-replace of locations). Run migration
> `src/migrations/0020_sponsor_logo.sql` (adds the `logo` column) before deploying.
> Sticker placements persist via `functions/api/admin/stickers.js` (GET placed list /
> single lookup + POST upsert). No migration needed — `stickers.placement/lat/lon`
> already exist (migration 0015). The `/qr/<id>` resolver reads the same table, so a
> combi sticker with a `route_id` deep-links to that line on the next scan.

> **Note on editor warnings:** if your editor shows "Cannot find type 'Route'/'Stop'…"
> for these loose `.swift` files, that's expected — they only resolve once they're all
> members of the same Xcode target (below). There is no `.xcodeproj` checked in.

## Build it onto your iPhone (free Apple ID)

1. **Xcode → File → New → Project → iOS → App.**
   - Product Name: `RutasRecorder` · Interface: **SwiftUI** · Language: **Swift**.
   - Save it anywhere (e.g. inside this folder).
2. **Delete** the template's `ContentView.swift` and `…App.swift`, then **drag all the
   `.swift` files from this folder into the project** (check "Copy items if needed" and
   your app target). You now have one target with every file.
3. **Info.plist keys** — open the target's **Info** tab and add (or drag this folder's
   `Info.plist` in and point Build Settings → *Info.plist File* at it):
   - `Privacy - Location When In Use Usage Description`
   - `Privacy - Location Always and When In Use Usage Description`
   - **Signing & Capabilities → + Capability → Background Modes → check *Location updates***.
4. **Signing** — target → **Signing & Capabilities**:
   - Team: **Add an Account…** and sign in with your normal Apple ID → pick the
     *(Personal Team)*.
   - Set a unique **Bundle Identifier** (e.g. `com.mike.rutasrecorder`) if it complains.
5. **Plug in your iPhone**, select it as the run destination, press **▶**.
   - First run: on the phone, **Settings → General → VPN & Device Management** → trust
     your developer certificate.
6. When it asks for location, choose **Allow While Using**, then **Change to Always**
   (Settings → the app → Location → Always) so it records with the screen off.

### Free-account limits (fine for this)
- The signing certificate lasts **7 days** — after that just press ▶ again to reinstall.
- No push, no App Store — irrelevant here; this is a personal recording tool.

## Recording tips
- Start recording **at the real start of the line**, or snip the lead-in afterward.
- Keep the phone where it gets sky — dashboard/window beats a pocket.
- If you only ride part of the route, save it and **join** the rest later.
- Fill in each stop's schedule while you're on the combi; it saves locally immediately.

## Export (later)
Routes are stored as JSON in the app's Documents (`routes.json`). Export to the
`resources/map-data/routes.js` format for the site is a follow-up step — not wired yet.
