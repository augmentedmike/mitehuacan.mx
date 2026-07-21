# PRD — Data Agents

The programs that keep the MiTehuacán map's search corpus current. They run
**locally on Mike's machine** (never in the cloud), each one gathers a slice of
"what exists in Tehuacán," and the results feed the app's search tiers. This
document describes each agent: what it does, where its data comes from, what it
writes, how it fails, and how it's operated.

- **Runner + console:** `src/scripts/agents.py` (dashboard at
  `http://localhost:8790`)
- **Agent scripts:** `src/scripts/{16,17,20,21}_*.py` + the `denue-dl` shell step
- **Run artifacts:** `.agent-runs/` (gitignored) — one full log per run plus
  `runs.jsonl`, the index the dashboard reads
- **Sessions for the social scrapers:** `.agent-auth/<platform>/` (gitignored)
- **Discovery output:** `resources/discovery/<platform>.jsonl` (gitignored)

---

## Principles

1. **Local only.** These agents run on Mike's machine and write files into the
   repo. Nothing here deploys. Publishing is a separate, later step (rebuild +
   PR). This is deliberate: the machine holds the platform sessions and the raw
   207MB DENUE CSV, neither of which belongs in CI.

2. **Two classes of agent:**
   - **Authoritative sources** (`osm`, `denue`, `calles`) — bulk, licensed,
     coordinate-precise data. They regenerate whole map layers.
   - **Discovery scrapers** (`google`, `instagram`, `facebook`) — find the long
     tail the authoritative sources miss (Instagram-native shops, new openings).
     They never publish; they file *candidates* into a review queue.

3. **Every run is logged and diffed.** The runner snapshots the data layers
   before and after each run and writes a complete `== DATA CHANGES ==` section
   into the log — every added, removed, and modified entry **by name**, nothing
   summarized away. The log is the archive.

4. **Discovery never auto-publishes.** Scraped candidates land in
   `resources/discovery/*.jsonl` and must be approved through the admin
   `/lugares` queue before they reach search. The scrapers are lead generators,
   not a write path to production.

5. **Humans hold auth; agents do the work.** The social scrapers reuse a browser
   session that Mike logs into by hand. The agent never sees or types
   credentials, and never tries to defeat a captcha — it hands the wall back to
   Mike.

---

## The runner — `agents.py`

The wrapper every agent runs through, so each run is logged, timed, diffed, and
visible.

**Commands**

| Command | Effect |
|---|---|
| `python3 src/scripts/agents.py run <name>` | run one agent, fully logged |
| `python3 src/scripts/agents.py run full` | run the whole daily chain in order |
| `python3 src/scripts/agents.py dash` | dashboard at `http://localhost:8790` |
| `python3 src/scripts/agents.py install-cron [hour]` | install the daily launchd job (default 07:00) |
| `python3 src/scripts/agents.py uninstall-cron` | remove it |

**What a run produces**

- `.agent-runs/<stamp>-<name>.log` — the header (`$ command` + start time), the
  agent's full stdout/stderr, then the `== DATA CHANGES ==` section.
- one line appended to `.agent-runs/runs.jsonl`:
  `{name, start, dur_s, exit, log, tail, warns, delta, delta_layers}`.
  - `warns` = count of error/traceback/failed/exception lines in the output
    (before the DATA CHANGES section, so the diff's own words don't inflate it).
  - `delta` = `{"+": added, "-": removed, "~": changed}` totals across all layers.
- On non-zero exit: a macOS notification fires. On dashboard startup, any agent
  whose latest run failed triggers a standing-failure notification.

**The diff.** Before a run, `snapshot_all()` records every entry in
`pois.js / places.js / denue.js / calles.js / sponsors.js` (keyed by
`kind + name + rounded coords`) and every candidate in
`resources/discovery/*.jsonl`. After the run it snapshots again and lists the
exact adds/removes/changes per layer into the log. This is how a run answers
"what did it actually do to the data."

**The dashboard.** Table view — one row per agent with columns: agent (name +
description), status (`ok` / `exit N` / `running` / `never`), last run, duration,
changes (`+N −N ~N` chip or "no changes"), warnings, and a ▶ launch button. A red
banner appears if any agent's latest run failed. Click a row to open that agent's
detail: full run history with the same columns plus the last output line, and
each history row expands to the complete log. A "▶▶ run all" button launches the
chain. Refreshes every 3s and streams the live log while an agent runs. English
only, dark/light aware, `localhost`-only.

**The daily cron.** `install-cron` writes a launchd plist
(`~/Library/LaunchAgents/mx.mitehuacan.agents.plist`) that runs `run full` daily
at 07:00 through this same wrapper — so scheduled runs land in the dashboard with
full logs and diffs, and failures still notify. launchd (not crontab) because it
survives reboots and runs in the Aqua session, which is what lets `osascript`
notifications work.

**The chain (`full`):** `osm → denue-dl → denue → calles → google → instagram →
facebook`. Ordered so the authoritative layers rebuild first (and `denue-dl`
refreshes the CSV before `denue` parses it), then discovery runs against
up-to-date data for cleaner dedup.

---

## Authoritative source agents

### `osm` — OpenStreetMap POIs + places

- **Script:** `src/scripts/16_refresh_pois.py`
- **Source:** OpenStreetMap via the Overpass API (ODbL licensed).
- **What it does:** queries named POIs and places within the route-network
  bounding box and rebuilds `resources/map-data/pois.js` (curated categories:
  education, health, government) and the OSM `places.js` layer.
- **Writes:** `resources/map-data/pois.js`, `resources/map-data/places.js`.
- **Search role:** the `POIS` and `PLACES` tiers.
- **Cost:** free. Overpass has soft rate limits; the script retries across
  mirror endpoints.

### `denue-dl` — download the INEGI DENUE CSV

- **Step:** shell (`curl` + `unzip` + `cp`), defined inline in `agents.py`.
- **Source:** INEGI's national business registry, Puebla state CSV
  (`denue_21_csv.zip`, ~37MB compressed → 207MB CSV). Términos de libre uso MX.
- **What it does:** downloads and unpacks the CSV to
  `resources/poi/denue_puebla.csv` so `denue` has fresh input. The CSV itself is
  gitignored (too big for the repo).
- **Writes:** `resources/poi/denue_puebla.csv` (local only).
- **Why separate:** the download is slow and network-bound; keeping it a distinct
  step means `denue` can re-parse without re-downloading, and a failed download
  is diagnosed on its own row.

### `denue` — INEGI DENUE establishments

- **Script:** `src/scripts/17_build_denue.py`
- **Source:** the CSV that `denue-dl` produced.
- **What it does:** filters the ~40k establishments in the service-area bounding
  box, maps SCIAN activity codes to Spanish search chips (with retail/service/
  work fallbacks so nothing legitimate is dropped), dedupes against the OSM
  layer, and emits the DENUE search layer.
- **Writes:** `resources/map-data/denue.js` (~40,197 establishments, ~2.9MB,
  lazy-loaded in the app ~2.5s after startup).
- **Search role:** the `DENUE` tier — every registered branch of every chain,
  tortillerías, estéticas, consultorios, etc.
- **Cost:** free (static build artifact; the app serves it as a file).

### `calles` — streets + intersections

- **Script:** `src/scripts/20_build_streets.py`
- **Source:** OpenStreetMap via Overpass (ODbL).
- **What it does:** pulls every named street in the service area, finds nodes
  shared by two or more differently-named ways (= intersections), and emits a
  streets + esquinas layer. This is what makes `"reforma nte y 16 ote"` — the way
  locals actually name a spot — resolvable.
- **Writes:** `resources/map-data/calles.js` (~2,701 streets, ~8,061
  intersections).
- **Search role:** the `CALLES` tier (token matching + abbreviation expansion,
  client-side).
- **Cost:** free.

---

## Discovery scraper agents

All three share `src/scripts/21_discovery.py` and the same operating model. They
find businesses that exist on a platform but **not** in our map data, dedupe each
find against `denue.js / places.js / pois.js` **and** previously discovered
candidates, and append only genuinely-new names to
`resources/discovery/<platform>.jsonl`. Nothing they write is published — the
admin `/lugares` approval queue is the gate.

### Operating model — Mike holds the session

- **`21_discovery.py <platform> --login`** opens a real, headed browser on a
  persistent profile in `.agent-auth/<platform>/`. Mike signs in and solves any
  captcha himself, then presses Enter in the terminal. Cookies persist in the
  profile.
- **`21_discovery.py <platform>`** (or launching it from the dashboard) runs
  headless, reusing that saved session. The agent never sees or types Mike's
  credentials.

### Captcha / login-wall handling — never bypass, always hand back

When a headless run hits a captcha, a login wall, or a rate-limit, the agent does
**not** try to get past it. It:

1. screenshots the wall to `.agent-runs/attention-<platform>.png`,
2. fires a desktop notification ("needs you: … — run `<platform> --login`"),
3. exits with code **3**, which shows red in the dashboard.

Mike then runs `--login`, refreshes the session, and re-runs. This keeps the
system honest about platform terms and puts the human exactly where the human is
needed.

### `google` — Google Maps discovery

- **Source:** Google Maps search result feeds for a rotating set of
  category queries ("restaurantes en Tehuacán", "cafeterías…", "estéticas…", new
  openings, etc.).
- **Extracts:** business name and, when present in the result href, lat/lon and a
  place URL — so many Google finds arrive already geocoded.
- **Session:** usually works without login; consent/sorry walls are handled by
  the attention path above.

### `instagram` — Instagram discovery

- **Source:** Instagram's web top-search endpoint for Tehuacán queries, called
  with the saved session's cookies. Keeps users whose handle or full name
  references Tehuacán, plus tagged places (which carry lat/lng).
- **Why it matters:** this is the long tail that OSM and DENUE structurally miss —
  shops that exist only as an Instagram profile (the "where is Yoms!?" case).
- **Session:** required. A `401/403/429` triggers the attention path.

### `facebook` — Facebook discovery

- **Source:** Facebook's places search for Tehuacán queries, reusing the saved
  session. Filters out UI chrome ("me gusta", "compartir", …) and keeps
  page/profile links.
- **Session:** required; checkpoints and login walls trigger the attention path.

---

## Candidate record shape

Each line in `resources/discovery/<platform>.jsonl`:

```json
{"name": "...", "source": "google|instagram|facebook", "query": "...",
 "lat": 18.46, "lon": -97.39, "url": "...", "handle": "..."}
```

`lat`/`lon`/`url`/`handle` are present when the platform exposed them. On import
to the admin queue, a missing location is pinned by hand at approval time (same
posture as the public "¿Es tu negocio?" self-registration intake).

---

## Data flow, end to end

```
authoritative:  Overpass / INEGI ──> osm, denue-dl→denue, calles ──> resources/map-data/*.js
                                                                          │
discovery:      Google / IG / FB  ──> 21_discovery.py ──> resources/discovery/*.jsonl
                                                                          │
                                                          admin /lugares approval queue
                                                                          │
                                                          rebuild (build step) + PR ──> production
```

The agents refresh the repo's data. Turning that into a live site is the separate
build-and-deploy step — **building is not an agent operation.**

---

## Operational notes

- **Free tier holds.** The authoritative layers ship as static build artifacts
  (the app serves `.js` files), so bulk reference data costs nothing at runtime.
  D1 is reserved for owned/transactional data (sponsors, QR, telemetry).
- **Discovery volume is capped by dedup, not by an arbitrary limit** — each run
  only grows the jsonl by genuinely-new names, so re-running is safe and cheap.
- **Sessions expire.** Expect to re-run `--login` for instagram/facebook
  periodically; the attention path tells you when.
- **The dashboard is the source of truth for agent health** — status, diffs, and
  full logs all live there. Cron runs surface there too.
