#!/usr/bin/env python3
"""Discovery agents: instagram / facebook / google.

Find Tehuacán businesses that exist on the platforms but NOT in our map data
(the Instagram-native long tail, new openings, chains OSM/DENUE lag on).
Candidates land in resources/discovery/<platform>.jsonl for review — they are
NEVER published directly; the admin approval queue stays the gate.

Session model — the human maintains auth, the agent does the work:
  python3 src/scripts/21_discovery.py <platform> --login [--profile NAME]
    opens a real (headed) browser on that platform's persistent profile in
    .agent-auth/<platform>/<profile>/. YOU log in and solve any captcha
    yourself; the agent never sees or types credentials. Press Enter in the
    terminal when done — cookies persist in the profile for headless runs.

  python3 src/scripts/21_discovery.py <platform> [--profile NAME]
    headless scrape reusing the saved session. If it hits a captcha, login
    wall, or rate-limit it does NOT try to get past it: it screenshots the
    wall to .agent-runs/attention-<platform>.png, fires a desktop
    notification telling you to run --login, and exits 3 (flagged red in the
    agents dashboard).

Each platform has its own isolated browser profile (separate cookies/login),
so your facebook / instagram / google accounts never mix. --profile lets you
keep more than one account per platform (e.g. two google logins).

EVERYTHING is logged: every query, every URL navigated, HTTP statuses, result
counts, page titles, browser console errors, per-step timing, and full
tracebacks. The log is meant to be enough to debug a run without re-running it.
"""
import json
import re
import subprocess
import sys
import time
import traceback
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTH = ROOT / ".agent-auth"
OUT = ROOT / "resources" / "discovery"
RUNS = ROOT / ".agent-runs"
LAYERS = [ROOT / "resources" / "map-data" / f for f in ("denue.js", "places.js", "pois.js")]

GOOGLE_QUERIES = [
    "restaurantes en Tehuacán", "cafeterías en Tehuacán", "boutiques en Tehuacán",
    "estéticas en Tehuacán", "gimnasios en Tehuacán", "veterinarias en Tehuacán",
    "papelerías en Tehuacán", "florerías en Tehuacán", "panaderías en Tehuacán",
    "tiendas en Tehuacán", "consultorios en Tehuacán", "negocios nuevos en Tehuacán",
]
IG_QUERIES = ["tehuacan", "tehuacán", "tehuacan mx", "tehuacan puebla"]
FB_QUERIES = ["Tehuacán", "restaurante Tehuacán", "tienda Tehuacán", "boutique Tehuacán"]

T0 = time.time()


def log(msg):
    """Timestamped line to stdout — the runner captures it into the run log."""
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


def norm(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def known_names():
    seen = set()
    for f in LAYERS:
        if not f.exists():
            log(f"dedup: layer {f.name} missing, skipped")
            continue
        t = f.read_text(encoding="utf-8")
        try:
            data = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1])
        except ValueError:
            log(f"dedup: layer {f.name} unparseable, skipped")
            continue
        n0 = len(seen)
        for key in ("pois", "places"):
            for e in data.get(key, []):
                seen.add(norm(e["n"]))
        log(f"dedup: {f.name} contributed {len(seen) - n0} names")
    out_file = OUT / f"{PLATFORM}.jsonl"
    if out_file.exists():
        prior = 0
        for line in out_file.read_text().splitlines():
            try:
                seen.add(norm(json.loads(line)["name"]))
                prior += 1
            except (ValueError, KeyError):
                pass
        log(f"dedup: {prior} prior candidates in {out_file.name}")
    log(f"dedup: {len(seen)} known names total")
    return seen


def notify(msg):
    subprocess.run(["osascript", "-e",
                    f'display notification "{msg}" with title "mitehuacán · agent {PLATFORM}" sound name "Basso"'],
                   capture_output=True)


def attention(page, reason):
    """Captcha/login wall: never bypass — hand it to the human and stop."""
    RUNS.mkdir(exist_ok=True)
    shot = RUNS / f"attention-{PLATFORM}.png"
    try:
        page.screenshot(path=str(shot))
        log(f"attention screenshot -> {shot}")
    except Exception as e:  # noqa: BLE001
        log(f"attention screenshot FAILED: {e!r}")
    log(f"ATTENTION REQUIRED: {reason}")
    log(f"  current url: {page.url}")
    log(f"  fix it yourself with: python3 src/scripts/21_discovery.py {PLATFORM} --login" +
        (f" --profile {PROFILE}" if PROFILE != "default" else ""))
    notify(f"needs you: {reason} — run {PLATFORM} --login")
    sys.exit(3)


def walled(page):
    url = page.url.lower()
    if any(w in url for w in ("consent.google", "/sorry/", "accounts/login", "/checkpoint", "login.php", "/challenge")):
        return "login/captcha wall at " + page.url[:80]
    try:
        body = page.inner_text("body", timeout=4000)[:4000].lower()
    except Exception as e:  # noqa: BLE001
        log(f"walled: could not read body ({e!r})")
        return None
    for marker in ("unusual traffic", "not a robot", "captcha", "confirma que eres", "inicia sesión para continuar"):
        if marker in body:
            return f"page shows '{marker}'"
    return None


def wire_console(page):
    """Surface browser console errors + failed requests into the run log."""
    page.on("console", lambda m: m.type in ("error", "warning")
            and log(f"[console.{m.type}] {m.text[:200]}"))
    page.on("pageerror", lambda e: log(f"[pageerror] {str(e)[:200]}"))
    page.on("requestfailed", lambda r: log(f"[requestfailed] {r.method} {r.url[:120]} — {r.failure}"))


def save(candidates):
    OUT.mkdir(parents=True, exist_ok=True)
    seen = known_names()
    fresh, dropped = [], 0
    for c in candidates:
        k = norm(c["name"])
        if len(k) < 3 or k in seen:
            dropped += 1
            continue
        seen.add(k)
        fresh.append(c)
    with open(OUT / f"{PLATFORM}.jsonl", "a", encoding="utf-8") as fh:
        for c in fresh:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    log(f"RESULT: {len(candidates)} raw scraped, {dropped} already-known/too-short, "
        f"{len(fresh)} NEW -> resources/discovery/{PLATFORM}.jsonl")
    for c in fresh:
        loc = f" @{c['lat']:.4f},{c['lon']:.4f}" if c.get("lat") and c.get("lon") else " (no location)"
        log(f"  NEW: {c['name']}{loc}" + (f"  {c.get('url', '')}" if c.get("url") else ""))


def scrape_google(page):
    wire_console(page)
    out = []
    for i, q in enumerate(GOOGLE_QUERIES, 1):
        url = "https://www.google.com/maps/search/" + q.replace(" ", "+")
        log(f"[google {i}/{len(GOOGLE_QUERIES)}] query={q!r} -> {url}")
        page.goto(url, timeout=60000)
        page.wait_for_timeout(4000)
        log(f"[google] landed: title={page.title()!r} url={page.url[:90]}")
        if (w := walled(page)):
            attention(page, w)
        for s in range(4):                       # pull more of the result feed
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(1200)
        anchors = page.query_selector_all('div[role="feed"] a[aria-label][href*="/maps/place/"]')
        before = len(out)
        for a in anchors:
            name = (a.get_attribute("aria-label") or "").strip()
            href = a.get_attribute("href") or ""
            m = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", href)
            if name:
                out.append({"name": name[:80], "source": "google", "query": q,
                            "lat": float(m.group(1)) if m else None,
                            "lon": float(m.group(2)) if m else None,
                            "url": href.split("?")[0][:200]})
        log(f"[google] {q!r}: {len(anchors)} anchors, +{len(out) - before} rows (cumulative {len(out)})")
        time.sleep(3)
    return out


def scrape_instagram(context, page):
    wire_console(page)
    log("[instagram] warming session at instagram.com")
    page.goto("https://www.instagram.com/", timeout=60000)
    page.wait_for_timeout(4000)
    log(f"[instagram] landed: title={page.title()!r} url={page.url[:90]}")
    if (w := walled(page)):
        attention(page, w)
    out = []
    for i, q in enumerate(IG_QUERIES, 1):
        api = "https://www.instagram.com/api/v1/web/search/topsearch/?context=blended&query=" + q
        log(f"[instagram {i}/{len(IG_QUERIES)}] query={q!r} -> topsearch API")
        r = context.request.get(api, headers={"x-ig-app-id": "936619743392459",
                                              "x-requested-with": "XMLHttpRequest",
                                              "referer": "https://www.instagram.com/"})
        log(f"[instagram] API status={r.status}")
        if r.status in (401, 403, 429):
            attention(page, f"instagram API {r.status} (session expired or rate-limited)")
        try:
            data = r.json()
        except Exception:  # noqa: BLE001
            attention(page, "instagram API returned non-JSON (probably a login wall)")
        before = len(out)
        for u in data.get("users", []):
            usr = u.get("user", {})
            handle, full = usr.get("username", ""), usr.get("full_name", "")
            if "tehuacan" in norm(handle) + norm(full):
                out.append({"name": (full or handle)[:80], "source": "instagram", "query": q,
                            "handle": handle, "url": f"https://instagram.com/{handle}"})
        for pl in data.get("places", []):
            p2 = pl.get("place", {}).get("location", {})
            if "tehuacan" in norm(p2.get("name", "")) or "tehuacan" in norm(pl.get("place", {}).get("subtitle", "")):
                out.append({"name": p2.get("name", "")[:80], "source": "instagram", "query": q,
                            "lat": p2.get("lat"), "lon": p2.get("lng")})
        log(f"[instagram] {q!r}: {len(data.get('users', []))} users, {len(data.get('places', []))} places, "
            f"+{len(out) - before} kept (cumulative {len(out)})")
        time.sleep(4)
    return out


def scrape_facebook(page):
    wire_console(page)
    out = []
    junk = re.compile(r"^(me gusta|like|follow|seguir|compartir|share|ver|see|facebook|iniciar|log in)\b", re.I)
    for i, q in enumerate(FB_QUERIES, 1):
        url = "https://www.facebook.com/search/places/?q=" + q.replace(" ", "%20")
        log(f"[facebook {i}/{len(FB_QUERIES)}] query={q!r} -> {url}")
        page.goto(url, timeout=60000)
        page.wait_for_timeout(5000)
        log(f"[facebook] landed: title={page.title()!r} url={page.url[:90]}")
        if (w := walled(page)):
            attention(page, w)
        for s in range(3):
            page.mouse.wheel(0, 2500)
            page.wait_for_timeout(1500)
        anchors = page.query_selector_all('div[role="main"] a[role="link"]')
        before = len(out)
        for a in anchors:
            name = (a.inner_text() or "").strip().split("\n")[0]
            href = a.get_attribute("href") or ""
            if len(name) > 3 and not junk.match(name) and ("/pages/" in href or re.search(r"facebook\.com/[^/?]+/?(\?|$)", href)):
                out.append({"name": name[:80], "source": "facebook", "query": q, "url": href.split("?")[0][:200]})
        log(f"[facebook] {q!r}: {len(anchors)} links, +{len(out) - before} rows (cumulative {len(out)})")
        time.sleep(4)
    return out


CHROME_BINS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]


def do_login(profile, start_url):
    """Manual sign-in in a REAL, un-automated Chrome.

    Google blocks sign-in in any browser Playwright drives (it detects the
    remote-debugging port). So for login we launch the actual Chrome binary
    against the same profile dir with NO automation port — an ordinary browser
    Google accepts. Playwright later reuses the cookies for headless scraping.
    """
    chrome = next((b for b in CHROME_BINS if Path(b).exists()), None)
    if not chrome:
        log("no real Chrome/Chromium/Brave found in /Applications — cannot do a clean login")
        print("Install Google Chrome, then retry the login.")
        sys.exit(4)
    log(f"launching real browser for login (NO automation): {chrome}")
    print(f"\nA normal Chrome window is opening for {PLATFORM} (profile: {PROFILE}).")
    print("Sign in there, then CLOSE the window — the session saves automatically.")
    # NOT a Playwright browser: no --remote-debugging-port, so Google sees a
    # normal browser. Blocking wait() = the process ends when you close it.
    proc = subprocess.Popen([chrome, f"--user-data-dir={profile}",
                             "--no-first-run", "--no-default-browser-check", start_url])
    proc.wait()
    log("browser closed — session saved.")


def main():
    from playwright.sync_api import sync_playwright

    login = "--login" in sys.argv
    profile = AUTH / PLATFORM / PROFILE
    profile.mkdir(parents=True, exist_ok=True)
    start_url = {"google": "https://accounts.google.com/",
                 "instagram": "https://www.instagram.com/accounts/login/",
                 "facebook": "https://www.facebook.com/login/"}[PLATFORM]

    log(f"start: platform={PLATFORM} profile={PROFILE} mode={'LOGIN' if login else 'scrape'} "
        f"utc={datetime.now(timezone.utc).isoformat()}")
    log(f"profile dir: {profile}")

    if login:
        do_login(profile, start_url)
        return

    # scrape flow — reuse the profile's saved cookies, headless
    launch = dict(
        headless=True, viewport={"width": 1280, "height": 900},
        locale="es-MX", timezone_id="America/Mexico_City",
        ignore_default_args=["--enable-automation"],
        args=["--disable-blink-features=AutomationControlled",
              "--no-default-browser-check", "--no-first-run"])

    with sync_playwright() as pw:
        try:
            context = pw.chromium.launch_persistent_context(str(profile), channel="chrome", **launch)
            log("launched real Chrome (channel=chrome) for scrape")
        except Exception as e:  # noqa: BLE001
            log(f"channel=chrome unavailable ({e!r}); using bundled chromium")
            context = pw.chromium.launch_persistent_context(str(profile), **launch)
        context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        page = context.pages[0] if context.pages else context.new_page()

        try:
            candidates = {"google": lambda: scrape_google(page),
                          "instagram": lambda: scrape_instagram(context, page),
                          "facebook": lambda: scrape_facebook(page)}[PLATFORM]()
        except SystemExit:
            raise
        except Exception:  # noqa: BLE001
            log("SCRAPE FAILED with exception:")
            log(traceback.format_exc())
            try:
                page.screenshot(path=str(RUNS / f"error-{PLATFORM}.png"))
                log(f"error screenshot -> {RUNS / f'error-{PLATFORM}.png'}")
            except Exception:  # noqa: BLE001
                pass
            context.close()
            sys.exit(1)
        context.close()
    save(candidates)
    log(f"done in {time.time() - T0:.1f}s")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--") or a == "--login"]
    if not args or args[0] not in ("instagram", "facebook", "google"):
        print("usage: 21_discovery.py instagram|facebook|google [--login] [--profile NAME]")
        sys.exit(2)
    PLATFORM = args[0]
    PROFILE = "default"
    if "--profile" in sys.argv:
        j = sys.argv.index("--profile")
        if j + 1 < len(sys.argv):
            PROFILE = re.sub(r"[^a-zA-Z0-9_-]", "", sys.argv[j + 1]) or "default"
    main()
