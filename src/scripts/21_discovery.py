#!/usr/bin/env python3
"""Discovery agents: instagram / facebook / google.

Find Tehuacán businesses that exist on the platforms but NOT in our map data.
Candidates land in resources/discovery/<platform>.jsonl for review — they are
NEVER published directly; the admin approval queue stays the gate.

Systematic sweep, not one flat search
-------------------------------------
Repeating the same query misses most of the map. Instead:

  * SPACE — start at the geo center of Tehuacán and expand outward in
    concentric rings (centro → ~1.5km → 3km → 5km, eight compass points each).
    Google Maps searches are centered on each point so results are local to it.
  * CATEGORY — walk a taxonomy of categories and subcategories (restaurantes,
    cafés, bares, tiendas, belleza/salud, servicios, educación, gobierno,
    puntos de interés, arte…) one subcategory at a time. Never "grab all at
    once."

Each run does a BOUNDED BATCH of the plan and advances a persistent cursor
(resources/discovery/<platform>.cursor), so running the agent repeatedly walks
the whole space×category plan without repeating, finding new records each time.
The daily cron keeps it moving on its own.

Sessions — the human maintains auth, the agent does the work:
  python3 src/scripts/21_discovery.py <platform> --login [--profile NAME]
    opens a REAL Chrome (not automation-controlled, so Google accepts sign-in)
    on the profile in .agent-auth/<platform>/<profile>/. Sign in, close the
    window; cookies persist for headless runs.

  python3 src/scripts/21_discovery.py <platform> [--batch N] [--all] [--profile NAME]
    headless scrape of the next batch (default 24 plan items; --all ignores the
    cursor and sweeps everything — long). Hits a captcha/login wall? It does NOT
    bypass — screenshots it, notifies you to re-login, exits 3.
"""
import json
import math
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

CENTER = (18.4620, -97.3960)          # geo center of Tehuacán
DEFAULT_BATCH = 24

# category -> subcategories (Spanish; our data is Spanish). One subcategory is
# one search. Ordered roughly by density so early runs hit the fat part first.
TAXONOMY = {
    "restaurantes": ["restaurante", "taquería", "antojitos", "cocina económica", "mariscos",
                     "pizzería", "comida china", "barbacoa", "carnitas", "pozolería", "cemitas", "torterías"],
    "café y postres": ["cafetería", "panadería", "pastelería", "heladería", "dulcería", "juguería"],
    "bares y vida nocturna": ["bar", "cantina", "antro", "cervecería", "pulquería", "billar"],
    "tiendas": ["boutique de ropa", "zapatería", "joyería", "tienda de regalos", "papelería",
                "juguetería", "mueblería", "ferretería", "abarrotes", "mercado", "florería",
                "tienda de electrónica", "celulares", "vinos y licores"],
    "belleza y salud": ["estética", "peluquería", "barbería", "spa", "salón de uñas", "farmacia",
                        "consultorio médico", "dentista", "clínica", "óptica", "laboratorio clínico",
                        "nutriólogo", "psicólogo"],
    "servicios": ["taller mecánico", "lavandería", "cerrajería", "imprenta", "gimnasio", "veterinaria",
                  "refaccionaria", "banco", "gasolinera", "hotel", "inmobiliaria", "agencia de viajes"],
    "educación": ["escuela primaria", "secundaria", "preparatoria", "universidad", "kínder", "academia"],
    "gobierno y municipal": ["oficina de gobierno", "palacio municipal", "registro civil", "biblioteca pública"],
    "puntos de interés": ["iglesia", "parque", "plaza", "museo", "cine", "teatro", "centro deportivo"],
    "arte y cultura": ["galería de arte", "estudio de arte", "centro cultural"],
}
ALL_SUBCATS = [(cat, sub) for cat, subs in TAXONOMY.items() for sub in subs]

# base keyword queries (no geo) for the platforms whose search is keyword-only
IG_BASE = ["tehuacan", "tehuacán", "tehuacanpuebla"]

T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


def build_points():
    """centro + concentric rings of 8 compass points expanding outward."""
    pts = [("centro", CENTER)]
    compass = {"N": (1, 0), "NE": (0.7, 0.7), "E": (0, 1), "SE": (-0.7, 0.7),
               "S": (-1, 0), "SW": (-0.7, -0.7), "W": (0, -1), "NW": (0.7, -0.7)}
    latc = math.cos(math.radians(CENTER[0]))
    for r_km, ring in [(1.5, "r1"), (3.0, "r2"), (5.0, "r3")]:
        d = r_km / 111.0
        for name, (dy, dx) in compass.items():
            pts.append((f"{ring}-{name}", (round(CENTER[0] + dy * d, 5),
                                           round(CENTER[1] + dx * d / latc, 5))))
    return pts


POINTS = build_points()


def build_plan(platform):
    """Ordered work list. Google is space×category (point-major: sweep every
    category at centro first, then ring by ring outward). IG/FB are keyword-only
    so they sweep the category taxonomy (plus base terms)."""
    if platform == "google":
        return [{"where": lbl, "pt": pt, "cat": cat, "sub": sub}
                for lbl, pt in POINTS for cat, sub in ALL_SUBCATS]
    if platform == "instagram":
        return [{"q": t, "cat": "base", "sub": t} for t in IG_BASE] + \
               [{"q": f"{sub} tehuacan", "cat": cat, "sub": sub} for cat, sub in ALL_SUBCATS]
    return [{"q": f"{sub} Tehuacán", "cat": cat, "sub": sub} for cat, sub in ALL_SUBCATS]  # facebook


def cursor_path():
    return OUT / f"{PLATFORM}.cursor"


def read_cursor():
    try:
        return int(cursor_path().read_text().strip())
    except (OSError, ValueError):
        return 0


def write_cursor(i):
    OUT.mkdir(parents=True, exist_ok=True)
    cursor_path().write_text(str(i))


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
        log(f"dedup: {prior} prior {PLATFORM} candidates")
    log(f"dedup: {len(seen)} known names total")
    return seen


def notify(msg):
    subprocess.run(["osascript", "-e",
                    f'display notification "{msg}" with title "mitehuacán · agent {PLATFORM}" sound name "Basso"'],
                   capture_output=True)


def attention(page, reason):
    RUNS.mkdir(exist_ok=True)
    shot = RUNS / f"attention-{PLATFORM}.png"
    try:
        page.screenshot(path=str(shot))
        log(f"attention screenshot -> {shot}")
    except Exception as e:  # noqa: BLE001
        log(f"attention screenshot FAILED: {e!r}")
    log(f"ATTENTION REQUIRED: {reason}")
    log(f"  current url: {page.url}")
    log(f"  re-login with: python3 src/scripts/21_discovery.py {PLATFORM} --login" +
        (f" --profile {PROFILE}" if PROFILE != "default" else ""))
    notify(f"needs you: {reason} — re-login {PLATFORM}")
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


# Google's own telemetry / tiles / thumbnails abort constantly and mean nothing
# to us — filter them so the log stays about OUR requests.
_NOISE = re.compile(r"gen_204|/log204|/maps/vt|streetviewpixels|/textsearch|clients4|"
                    r"play\.google|doubleclick|/gen204|adservice|/maps/preview/log")


def wire_console(page):
    page.on("console", lambda m: m.type in ("error", "warning") and log(f"[console.{m.type}] {m.text[:180]}"))
    page.on("pageerror", lambda e: log(f"[pageerror] {str(e)[:180]}"))
    page.on("requestfailed", lambda r: (not _NOISE.search(r.url)) and
            log(f"[requestfailed] {r.method} {r.url[:110]} — {r.failure}"))


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
        log(f"  NEW [{c.get('cat', '?')}/{c.get('sub', '?')}]: {c['name']}{loc}" +
            (f"  {c.get('url', '')}" if c.get("url") else ""))
    return len(fresh)


def batch_slice(plan):
    """Return (items, start, end, wrapped) for this run per the cursor + batch."""
    total = len(plan)
    if "--all" in sys.argv:
        log(f"plan: sweeping ALL {total} items (--all)")
        return plan, 0, total, False
    start = read_cursor() % total
    end = start + BATCH
    items = (plan + plan)[start:end]          # wrap around the end
    wrapped = end > total
    write_cursor(end % total)
    log(f"plan: {total} items total; this run covers {start}..{end} "
        f"(batch {BATCH}{', wrapped' if wrapped else ''}); next cursor {end % total}")
    return items, start, end, wrapped


def scrape_google(page):
    wire_console(page)
    plan = build_plan("google")
    items, *_ = batch_slice(plan)
    out = []
    for i, it in enumerate(items, 1):
        lat, lng = it["pt"]
        url = f"https://www.google.com/maps/search/{it['sub'].replace(' ', '+')}/@{lat},{lng},14z"
        log(f"[google {i}/{len(items)}] {it['where']} · {it['cat']}/{it['sub']} -> @{lat},{lng}")
        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(3500)
        except Exception as e:  # noqa: BLE001
            log(f"[google] nav error: {e!r} — skipping item")
            continue
        if (w := walled(page)):
            attention(page, w)
        # the results feed is its own scroll container — page-level scroll won't
        # paginate it. scroll INSIDE the feed until no new results load.
        feed = page.query_selector('div[role="feed"]')
        if feed:
            prev = 0
            for _ in range(12):
                page.evaluate("el => el.scrollTo(0, el.scrollHeight)", feed)
                page.wait_for_timeout(1100)
                n = len(page.query_selector_all('div[role="feed"] a[href*="/maps/place/"]'))
                if n == prev:                 # nothing new loaded → end of list
                    break
                prev = n
        anchors = page.query_selector_all('div[role="feed"] a[aria-label][href*="/maps/place/"]')
        before = len(out)
        for a in anchors:
            name = (a.get_attribute("aria-label") or "").strip()
            href = a.get_attribute("href") or ""
            m = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", href)
            if name:
                out.append({"name": name[:80], "source": "google", "cat": it["cat"], "sub": it["sub"],
                            "where": it["where"],
                            "lat": float(m.group(1)) if m else None,
                            "lon": float(m.group(2)) if m else None,
                            "url": href.split("?")[0][:200]})
        log(f"[google]   {len(anchors)} results, +{len(out) - before} rows (cumulative {len(out)})")
        time.sleep(2)
    return out


def scrape_instagram(context, page):
    wire_console(page)
    log("[instagram] warming session")
    page.goto("https://www.instagram.com/", timeout=60000)
    page.wait_for_timeout(3500)
    if (w := walled(page)):
        attention(page, w)
    plan = build_plan("instagram")
    items, *_ = batch_slice(plan)
    out = []
    for i, it in enumerate(items, 1):
        q = it["q"]
        log(f"[instagram {i}/{len(items)}] {it['cat']}/{it['sub']} -> query={q!r}")
        r = context.request.get(
            "https://www.instagram.com/api/v1/web/search/topsearch/?context=blended&query=" + q,
            headers={"x-ig-app-id": "936619743392459", "x-requested-with": "XMLHttpRequest",
                     "referer": "https://www.instagram.com/"})
        log(f"[instagram]   API status={r.status}")
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
                out.append({"name": (full or handle)[:80], "source": "instagram", "cat": it["cat"],
                            "sub": it["sub"], "handle": handle, "url": f"https://instagram.com/{handle}"})
        for pl in data.get("places", []):
            p2 = pl.get("place", {}).get("location", {})
            if "tehuacan" in norm(p2.get("name", "")) or "tehuacan" in norm(pl.get("place", {}).get("subtitle", "")):
                out.append({"name": p2.get("name", "")[:80], "source": "instagram", "cat": it["cat"],
                            "sub": it["sub"], "lat": p2.get("lat"), "lon": p2.get("lng")})
        log(f"[instagram]   {len(data.get('users', []))} users, {len(data.get('places', []))} places, "
            f"+{len(out) - before} kept (cumulative {len(out)})")
        time.sleep(3)
    return out


def scrape_facebook(page):
    wire_console(page)
    plan = build_plan("facebook")
    items, *_ = batch_slice(plan)
    out = []
    junk = re.compile(r"^(me gusta|like|follow|seguir|compartir|share|ver|see|facebook|iniciar|log in)\b", re.I)
    for i, it in enumerate(items, 1):
        q = it["q"]
        url = "https://www.facebook.com/search/places/?q=" + q.replace(" ", "%20")
        log(f"[facebook {i}/{len(items)}] {it['cat']}/{it['sub']} -> query={q!r}")
        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(4500)
        except Exception as e:  # noqa: BLE001
            log(f"[facebook] nav error: {e!r} — skipping item")
            continue
        if (w := walled(page)):
            attention(page, w)
        for _ in range(3):
            page.mouse.wheel(0, 2500)
            page.wait_for_timeout(1400)
        anchors = page.query_selector_all('div[role="main"] a[role="link"]')
        before = len(out)
        for a in anchors:
            name = (a.inner_text() or "").strip().split("\n")[0]
            href = a.get_attribute("href") or ""
            if len(name) > 3 and not junk.match(name) and ("/pages/" in href or re.search(r"facebook\.com/[^/?]+/?(\?|$)", href)):
                out.append({"name": name[:80], "source": "facebook", "cat": it["cat"], "sub": it["sub"],
                            "url": href.split("?")[0][:200]})
        log(f"[facebook]   {len(anchors)} links, +{len(out) - before} rows (cumulative {len(out)})")
        time.sleep(3)
    return out


CHROME_BINS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]


def do_login(profile, start_url):
    """Manual sign-in in a REAL, un-automated Chrome. Google blocks sign-in in
    any browser Playwright drives (it detects the remote-debugging port), so we
    launch the actual Chrome binary against the profile dir with NO automation
    port. Playwright later reuses the cookies for headless scraping."""
    chrome = next((b for b in CHROME_BINS if Path(b).exists()), None)
    if not chrome:
        log("no real Chrome/Chromium/Brave in /Applications — cannot do a clean login")
        sys.exit(4)
    log(f"launching real browser for login (NO automation): {chrome}")
    print(f"\nA normal Chrome window is opening for {PLATFORM} (profile: {PROFILE}).")
    print("Sign in there, then CLOSE the window — the session saves automatically.")
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
        f"batch={BATCH} utc={datetime.now(timezone.utc).isoformat()}")
    log(f"profile dir: {profile}")

    if login:
        do_login(profile, start_url)
        return

    launch = dict(
        headless=True, viewport={"width": 1280, "height": 900},
        locale="es-MX", timezone_id="America/Mexico_City",
        ignore_default_args=["--enable-automation"],
        args=["--disable-blink-features=AutomationControlled", "--no-default-browser-check", "--no-first-run"])

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
    n = save(candidates)
    log(f"done in {time.time() - T0:.1f}s — {n} new records this batch")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    plats = [a for a in args if a in ("instagram", "facebook", "google")]
    if not plats:
        print("usage: 21_discovery.py instagram|facebook|google [--login] [--batch N] [--all] [--profile NAME]")
        sys.exit(2)
    PLATFORM = plats[0]
    PROFILE = "default"
    BATCH = DEFAULT_BATCH
    if "--profile" in sys.argv:
        j = sys.argv.index("--profile")
        if j + 1 < len(sys.argv):
            PROFILE = re.sub(r"[^a-zA-Z0-9_-]", "", sys.argv[j + 1]) or "default"
    if "--batch" in sys.argv:
        j = sys.argv.index("--batch")
        if j + 1 < len(sys.argv):
            try:
                BATCH = max(1, int(sys.argv[j + 1]))
            except ValueError:
                pass
    main()
