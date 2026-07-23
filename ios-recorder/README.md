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

## Files

| File | Role |
|---|---|
| `RutasRecorderApp.swift` | `@main` app entry; owns the `RouteStore` + `LocationRecorder`. |
| `Models.swift` | `Route` (segments = one array per ride), `Stop`, `StopKind`, `StopSchedule`, `DaySchedule`, `TrackPoint`. |
| `LocationRecorder.swift` | Core Location; background recording (Always auth + background mode). |
| `RouteStore.swift` | JSON persistence + join / snip / prune ops. |
| `ContentView.swift` | Main map + record/stop + save-or-join sheet. |
| `RouteEditor.swift` | Route list + detail map with snip/join/prune + stop editing. |
| `StopEditView.swift` | Per-stop schedule editor (weekday/Sat/Sun first-last-interval). |
| `Info.plist` | Location usage strings + `UIBackgroundModes: location`. |

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
