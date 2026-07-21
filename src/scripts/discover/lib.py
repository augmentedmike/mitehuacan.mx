#!/usr/bin/env python3
"""Shared engine for the discovery agents (google / instagram / facebook).

Design (per Mike): procedural, and each agent owns its own setup, algorithm,
and data. This file is the shared MECHANISM; the per-agent modules
(google.py, instagram.py, facebook.py) supply the SETUP (center/rings/taxonomy)
and ALGORITHM (how to scrape one plan item, how to verify one record). Each
agent's DATA is its own SQLite file: resources/discovery/<agent>.db.

Lifecycle store — records are maintained, not just appended
-----------------------------------------------------------
Every record has a stable key and carries state:
  first_seen, last_seen, times_seen, status(candidate|approved|rejected|dead),
  status_reason, status_at, last_verified.

  * DISCOVER re-encountering a record BUMPS last_seen/times_seen (no duplicate
    row). A genuinely new record inserts as 'candidate'.
  * VERIFY re-checks existing records and marks the gone ones 'dead' (with a
    reason) — pruning by quarantine, never a hard delete, so it's reversible.
  * A record already decided (dead/rejected) stays decided; re-encountering it
    just bumps last_seen and it never re-surfaces to the export/queue.

Idempotency
-----------
The store is keyed, so running the SAME work twice converges to the SAME state:
upserts don't create duplicates, and re-marking a dead record dead is a no-op.
The only progress state is the plan cursor (meta table); running with --all (or
re-running a fixed slice) is fully data-idempotent.
"""
import json
import re
import sqlite3
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]      # discover/ -> scripts -> src -> repo
DISC = ROOT / "resources" / "discovery"
AUTH = ROOT / ".agent-auth"
RUNS = ROOT / ".agent-runs"
LAYERS = [ROOT / "resources" / "map-data" / f for f in ("denue.js", "places.js", "pois.js")]

CHROME_BINS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def norm(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def load_map_names():
    """norm(name) for everything already on our map — never re-add these."""
    seen = set()
    for f in LAYERS:
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8")
        try:
            data = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1])
        except ValueError:
            continue
        for key in ("pois", "places"):
            for e in data.get(key, []):
                seen.add(norm(e["n"]))
    return seen


class Store:
    """Per-agent SQLite lifecycle store."""

    def __init__(self, agent):
        DISC.mkdir(parents=True, exist_ok=True)
        self.agent = agent
        self.db = sqlite3.connect(DISC / f"{agent}.db")
        self.db.row_factory = sqlite3.Row
        self.db.execute("""CREATE TABLE IF NOT EXISTS records(
            key TEXT PRIMARY KEY, name TEXT, lat REAL, lon REAL,
            category TEXT, subcat TEXT, source TEXT, url TEXT, handle TEXT, where_ TEXT,
            first_seen TEXT, last_seen TEXT, times_seen INTEGER DEFAULT 1,
            status TEXT DEFAULT 'candidate', status_reason TEXT, status_at TEXT,
            last_verified TEXT)""")
        self.db.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_status ON records(status)")
        self.db.commit()

    # --- cursor (the only progress state) ---
    def get_cursor(self):
        r = self.db.execute("SELECT v FROM meta WHERE k='cursor'").fetchone()
        return int(r["v"]) if r else 0

    def set_cursor(self, i):
        self.db.execute("INSERT INTO meta(k,v) VALUES('cursor',?) "
                        "ON CONFLICT(k) DO UPDATE SET v=excluded.v", (str(i),))
        self.db.commit()

    # --- discovery upsert (idempotent) ---
    def upsert(self, rec, now):
        """Return True if this is a NEW record, False if it already existed.
        Existing rows only bump last_seen/times_seen + backfill coords/url —
        status is never changed here, so decided records stay decided."""
        key = rec["key"]
        row = self.db.execute("SELECT key FROM records WHERE key=?", (key,)).fetchone()
        if row:
            self.db.execute(
                "UPDATE records SET last_seen=?, times_seen=times_seen+1, "
                "lat=COALESCE(lat,?), lon=COALESCE(lon,?), url=COALESCE(url,?) WHERE key=?",
                (now, rec.get("lat"), rec.get("lon"), rec.get("url"), key))
            return False
        self.db.execute(
            "INSERT INTO records(key,name,lat,lon,category,subcat,source,url,handle,where_,"
            "first_seen,last_seen,times_seen,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,1,'candidate')",
            (key, rec["name"], rec.get("lat"), rec.get("lon"), rec.get("category"), rec.get("subcat"),
             rec.get("source"), rec.get("url"), rec.get("handle"), rec.get("where"), now, now))
        return True

    def mark(self, key, status, reason, now):
        self.db.execute("UPDATE records SET status=?, status_reason=?, status_at=?, last_verified=? WHERE key=?",
                        (status, reason, now, now, key))

    def touch_verified(self, key, now):
        self.db.execute("UPDATE records SET last_verified=? WHERE key=?", (now, key))

    def to_verify(self, limit):
        """Records due for re-verification: live ones, least-recently-verified first."""
        return self.db.execute(
            "SELECT * FROM records WHERE status IN ('candidate','approved') "
            "ORDER BY last_verified IS NOT NULL, last_verified ASC LIMIT ?", (limit,)).fetchall()

    def export_queue(self):
        """Write the live queue (candidate/approved) to <agent>.jsonl for the
        admin approval flow. Deterministic — same store => same file."""
        rows = self.db.execute(
            "SELECT * FROM records WHERE status IN ('candidate','approved') ORDER BY first_seen").fetchall()
        with open(DISC / f"{self.agent}.jsonl", "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps({k: r[k] for k in r.keys() if r[k] is not None}, ensure_ascii=False) + "\n")
        return len(rows)

    def stats(self):
        out = {s: 0 for s in ("candidate", "approved", "rejected", "dead")}
        for r in self.db.execute("SELECT status, COUNT(*) c FROM records GROUP BY status"):
            out[r["status"]] = r["c"]
        out["total"] = sum(out.values())
        return out

    def commit(self):
        self.db.commit()


class DiscoveryAgent:
    """Base agent. Subclasses set NAME, and implement build_plan / scrape_item /
    verify_record. Everything else (store, cursor, dedup, browser, logging) is
    shared here so agents only carry their setup + algorithm."""
    NAME = "base"
    START_URL = ""
    LOGIN_URL = ""
    DEFAULT_BATCH = 24
    NEEDS_CONTEXT = False        # instagram needs the browser context for API calls

    def __init__(self, profile="default", batch=None):
        self.profile = profile
        self.batch = batch or self.DEFAULT_BATCH
        self.store = Store(self.NAME)
        self.t0 = time.time()

    # ---- to implement per agent ----
    def build_plan(self):
        raise NotImplementedError

    def scrape_item(self, page, context, item):
        """Return list of record dicts. Each MUST include a stable 'key'."""
        raise NotImplementedError

    def verify_record(self, page, rec):
        """Return (alive: bool, reason: str) for an existing record."""
        raise NotImplementedError

    # ---- shared plumbing ----
    def log(self, msg):
        print(f"[{time.time() - self.t0:7.1f}s] {msg}", flush=True)

    def notify(self, msg):
        subprocess.run(["osascript", "-e",
                        f'display notification "{msg}" with title "mitehuacán · {self.NAME}" sound name "Basso"'],
                       capture_output=True)

    def profile_dir(self):
        d = AUTH / self.NAME / self.profile
        d.mkdir(parents=True, exist_ok=True)
        return d

    def attention(self, page, reason):
        RUNS.mkdir(exist_ok=True)
        try:
            page.screenshot(path=str(RUNS / f"attention-{self.NAME}.png"))
        except Exception:  # noqa: BLE001
            pass
        self.log(f"ATTENTION REQUIRED: {reason}")
        self.log(f"  re-login: python3 src/scripts/discover/run.py {self.NAME} --login" +
                 (f" --profile {self.profile}" if self.profile != "default" else ""))
        self.notify(f"needs you: {reason} — re-login {self.NAME}")
        sys.exit(3)

    def walled(self, page):
        url = page.url.lower()
        if any(w in url for w in ("consent.google", "/sorry/", "accounts/login", "/checkpoint", "login.php", "/challenge")):
            return "login/captcha wall at " + page.url[:80]
        try:
            body = page.inner_text("body", timeout=4000)[:4000].lower()
        except Exception:  # noqa: BLE001
            return None
        for m in ("unusual traffic", "not a robot", "captcha", "confirma que eres", "inicia sesión para continuar"):
            if m in body:
                return f"page shows '{m}'"
        return None

    _NOISE = re.compile(r"gen_204|/log204|/maps/vt|streetviewpixels|/textsearch|clients4|"
                        r"play\.google|doubleclick|adservice|/maps/preview/log")

    def wire_console(self, page):
        page.on("console", lambda m: m.type in ("error", "warning") and self.log(f"[console.{m.type}] {m.text[:170]}"))
        page.on("pageerror", lambda e: self.log(f"[pageerror] {str(e)[:170]}"))
        page.on("requestfailed", lambda r: (not self._NOISE.search(r.url)) and
                self.log(f"[requestfailed] {r.method} {r.url[:100]} — {r.failure}"))

    def _launch(self, pw):
        opts = dict(headless=True, viewport={"width": 1280, "height": 900},
                    locale="es-MX", timezone_id="America/Mexico_City",
                    ignore_default_args=["--enable-automation"],
                    args=["--disable-blink-features=AutomationControlled", "--no-default-browser-check", "--no-first-run"])
        try:
            ctx = pw.chromium.launch_persistent_context(str(self.profile_dir()), channel="chrome", **opts)
            self.log("launched real Chrome (channel=chrome)")
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            # profile locked = the login window for this agent is still open.
            # do NOT fall back to a session-less browser — that just yields a 401.
            if "ProcessSingleton" in msg or "SingletonLock" in msg or "already in use" in msg:
                self.log(f"profile in use — the {self.NAME} login window is still OPEN.")
                self.log(f"  CLOSE the {self.NAME} Chrome window (that saves the session), then re-run.")
                self.notify(f"close the {self.NAME} login window, then re-run")
                sys.exit(3)
            self.log(f"channel=chrome unavailable ({e!r}); using bundled chromium")
            ctx = pw.chromium.launch_persistent_context(str(self.profile_dir()), **opts)
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        return ctx

    # ---- login: real un-automated Chrome so Google accepts sign-in ----
    def login(self):
        chrome = next((b for b in CHROME_BINS if Path(b).exists()), None)
        if not chrome:
            self.log("no real Chrome/Chromium/Brave in /Applications — cannot do a clean login")
            sys.exit(4)
        self.log(f"launching real browser for login (NO automation): {chrome}")
        print(f"\nA normal Chrome window is opening for {self.NAME} (profile: {self.profile}).")
        print("Sign in there, then CLOSE the window — the session saves automatically.")
        subprocess.Popen([chrome, f"--user-data-dir={self.profile_dir()}",
                          "--no-first-run", "--no-default-browser-check", self.LOGIN_URL or self.START_URL]).wait()
        self.log("browser closed — session saved.")

    # ---- discover: sweep a bounded batch of the plan into the store ----
    def discover(self, all_=False):
        from playwright.sync_api import sync_playwright
        plan = self.build_plan()
        total = len(plan)
        if all_:
            items, start, end = plan, 0, total
            self.log(f"plan: sweeping ALL {total} items (--all)")
        else:
            start = self.store.get_cursor() % total
            end = start + self.batch
            items = (plan + plan)[start:end]
            self.log(f"plan: {total} items; this run covers {start}..{end} "
                     f"(batch {self.batch}); next cursor {end % total}")

        map_names = load_map_names()
        self.log(f"dedup: {len(map_names)} names already on the map; store has {self.store.stats()}")

        new = existed = onmap = 0
        with sync_playwright() as pw:
            ctx = self._launch(pw)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            self.wire_console(page)
            try:
                for i, it in enumerate(items, 1):
                    now = now_iso()
                    recs = self.scrape_item(page, ctx, it)
                    added = 0
                    for r in recs:
                        if norm(r["name"]) in map_names:      # already on our map
                            onmap += 1
                            continue
                        if self.store.upsert(r, now):
                            new += 1
                            added += 1
                        else:
                            existed += 1
                    self.store.commit()
                    self.log(f"[{self.NAME} {i}/{len(items)}] {it.get('label', '')} -> "
                             f"{len(recs)} results, {added} new to store")
            except SystemExit:
                raise
            except Exception:  # noqa: BLE001
                import traceback
                self.log("SCRAPE FAILED:\n" + traceback.format_exc())
                try:
                    page.screenshot(path=str(RUNS / f"error-{self.NAME}.png"))
                except Exception:  # noqa: BLE001
                    pass
                ctx.close()
                sys.exit(1)
            ctx.close()

        if not all_:
            self.store.set_cursor(end % total)
        q = self.store.export_queue()
        self.log(f"DISCOVER done in {time.time() - self.t0:.1f}s — {new} NEW, {existed} re-seen, "
                 f"{onmap} already-on-map; queue now {q}; store {self.store.stats()}")

    # ---- verify: re-check existing records, mark the dead ones (pruning) ----
    def verify(self):
        from playwright.sync_api import sync_playwright
        rows = self.store.to_verify(self.batch)
        if not rows:
            self.log("verify: nothing to check")
            return
        self.log(f"verify: re-checking {len(rows)} least-recently-verified records")
        dead = alive = 0
        with sync_playwright() as pw:
            ctx = self._launch(pw)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            self.wire_console(page)
            try:
                for i, r in enumerate(rows, 1):
                    now = now_iso()
                    ok, reason = self.verify_record(page, r)
                    if ok:
                        self.store.touch_verified(r["key"], now)
                        alive += 1
                    else:
                        self.store.mark(r["key"], "dead", reason, now)
                        dead += 1
                        self.log(f"  DEAD: {r['name']} — {reason}")
                    self.store.commit()
                    if i % 5 == 0:
                        self.log(f"verify {i}/{len(rows)}: {dead} dead, {alive} still live")
            finally:
                ctx.close()
        q = self.store.export_queue()
        self.log(f"VERIFY done in {time.time() - self.t0:.1f}s — {dead} marked dead, {alive} confirmed live; "
                 f"queue now {q}; store {self.store.stats()}")
