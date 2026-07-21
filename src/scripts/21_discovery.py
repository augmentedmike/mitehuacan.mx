#!/usr/bin/env python3
"""Discovery agents: instagram / facebook / google.

Find Tehuacán businesses that exist on the platforms but NOT in our map data
(the Instagram-native long tail, new openings, chains OSM/DENUE lag on).
Candidates land in resources/discovery/<platform>.jsonl for review — they are
NEVER published directly; the admin approval queue stays the gate.

Session model — the human maintains auth, the agent does the work:
  python3 src/scripts/21_discovery.py <platform> --login
    opens a real (headed) browser on that platform's persistent profile in
    .agent-auth/<platform>/. YOU log in and solve any captcha yourself; the
    agent never sees or types credentials. Press Enter in the terminal when
    done — cookies persist in the profile for headless runs.

  python3 src/scripts/21_discovery.py <platform>
    headless scrape reusing the saved session. If it hits a captcha, login
    wall, or rate-limit it does NOT try to get past it: it screenshots the
    wall to .agent-runs/attention-<platform>.png, fires a desktop
    notification telling you to run --login, and exits 3 (flagged red in the
    agents dashboard).

Every candidate is deduped against denue/places/pois layers AND previously
discovered candidates before it is written, so the jsonl only ever grows
with genuinely new names.
"""
import json
import re
import subprocess
import sys
import time
import unicodedata
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


def norm(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def known_names():
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
    out_file = OUT / f"{PLATFORM}.jsonl"
    if out_file.exists():
        for line in out_file.read_text().splitlines():
            try:
                seen.add(norm(json.loads(line)["name"]))
            except (ValueError, KeyError):
                pass
    return seen


def notify(msg):
    subprocess.run(["osascript", "-e",
                    f'display notification "{msg}" with title "mitehuacán · agente {PLATFORM}" sound name "Basso"'],
                   capture_output=True)


def attention(page, reason):
    """Captcha/login wall: never bypass — hand it to the human and stop."""
    RUNS.mkdir(exist_ok=True)
    shot = RUNS / f"attention-{PLATFORM}.png"
    try:
        page.screenshot(path=str(shot))
    except Exception:  # noqa: BLE001
        pass
    print(f"ATTENTION REQUIRED: {reason}")
    print(f"  screenshot: {shot}")
    print(f"  fix it yourself with: python3 src/scripts/21_discovery.py {PLATFORM} --login")
    notify(f"needs you: {reason} — run {PLATFORM} --login")
    sys.exit(3)


def walled(page):
    url = page.url.lower()
    if any(w in url for w in ("consent.google", "/sorry/", "accounts/login", "/checkpoint", "login.php", "/challenge")):
        return "login/captcha wall at " + page.url[:80]
    try:
        body = page.inner_text("body", timeout=4000)[:4000].lower()
    except Exception:  # noqa: BLE001
        return None
    for marker in ("unusual traffic", "not a robot", "captcha", "confirma que eres", "inicia sesión para continuar"):
        if marker in body:
            return f"page shows '{marker}'"
    return None


def save(candidates):
    OUT.mkdir(parents=True, exist_ok=True)
    seen = known_names()
    fresh = []
    for c in candidates:
        k = norm(c["name"])
        if len(k) < 3 or k in seen:
            continue
        seen.add(k)
        fresh.append(c)
    with open(OUT / f"{PLATFORM}.jsonl", "a", encoding="utf-8") as fh:
        for c in fresh:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"\n{PLATFORM}: {len(candidates)} raw, {len(fresh)} NEW candidates -> resources/discovery/{PLATFORM}.jsonl")
    for c in fresh:
        print(f"  NEW: {c['name']}" + (f"  ({c.get('url', '')})" if c.get("url") else ""))


def scrape_google(page):
    out = []
    for q in GOOGLE_QUERIES:
        page.goto("https://www.google.com/maps/search/" + q.replace(" ", "+"), timeout=60000)
        page.wait_for_timeout(4000)
        if (w := walled(page)):
            attention(page, w)
        for _ in range(4):                       # pull more of the result feed
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(1200)
        for a in page.query_selector_all('div[role="feed"] a[aria-label][href*="/maps/place/"]'):
            name = (a.get_attribute("aria-label") or "").strip()
            href = a.get_attribute("href") or ""
            m = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", href)
            if name:
                out.append({"name": name[:80], "source": "google", "query": q,
                            "lat": float(m.group(1)) if m else None,
                            "lon": float(m.group(2)) if m else None,
                            "url": href.split("?")[0][:200]})
        print(f"[google] {q!r}: {len(out)} cumulative")
        time.sleep(3)
    return out


def scrape_instagram(context, page):
    page.goto("https://www.instagram.com/", timeout=60000)
    page.wait_for_timeout(4000)
    if (w := walled(page)):
        attention(page, w)
    out = []
    for q in IG_QUERIES:
        r = context.request.get(
            "https://www.instagram.com/api/v1/web/search/topsearch/?context=blended&query=" + q,
            headers={"x-ig-app-id": "936619743392459",
                     "x-requested-with": "XMLHttpRequest",
                     "referer": "https://www.instagram.com/"})
        if r.status in (401, 403, 429):
            attention(page, f"instagram API {r.status} (session expired or rate-limited)")
        try:
            data = r.json()
        except Exception:  # noqa: BLE001
            attention(page, "instagram API returned non-JSON (probably a login wall)")
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
        print(f"[instagram] {q!r}: {len(out)} cumulative")
        time.sleep(4)
    return out


def scrape_facebook(page):
    out = []
    junk = re.compile(r"^(me gusta|like|follow|seguir|compartir|share|ver|see|facebook|iniciar|log in)\b", re.I)
    for q in FB_QUERIES:
        page.goto("https://www.facebook.com/search/places/?q=" + q.replace(" ", "%20"), timeout=60000)
        page.wait_for_timeout(5000)
        if (w := walled(page)):
            attention(page, w)
        for _ in range(3):
            page.mouse.wheel(0, 2500)
            page.wait_for_timeout(1500)
        for a in page.query_selector_all('div[role="main"] a[role="link"]'):
            name = (a.inner_text() or "").strip().split("\n")[0]
            href = a.get_attribute("href") or ""
            if len(name) > 3 and not junk.match(name) and ("/pages/" in href or re.search(r"facebook\.com/[^/?]+/?(\?|$)", href)):
                out.append({"name": name[:80], "source": "facebook", "query": q, "url": href.split("?")[0][:200]})
        print(f"[facebook] {q!r}: {len(out)} cumulative")
        time.sleep(4)
    return out


def main():
    from playwright.sync_api import sync_playwright

    login = "--login" in sys.argv
    profile = AUTH / PLATFORM
    profile.mkdir(parents=True, exist_ok=True)
    start_url = {"google": "https://www.google.com/maps",
                 "instagram": "https://www.instagram.com/",
                 "facebook": "https://www.facebook.com/"}[PLATFORM]

    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            str(profile), headless=not login, viewport={"width": 1280, "height": 900},
            locale="es-MX", timezone_id="America/Mexico_City")
        page = context.pages[0] if context.pages else context.new_page()

        if login:
            page.goto(start_url)
            print(f"\nBrowser open on {PLATFORM}. Log in / solve any captcha YOURSELF.")
            print("The session persists in .agent-auth/ — press Enter here when done.")
            input()
            context.close()
            print("session saved.")
            return

        candidates = {"google": lambda: scrape_google(page),
                      "instagram": lambda: scrape_instagram(context, page),
                      "facebook": lambda: scrape_facebook(page)}[PLATFORM]()
        context.close()
    save(candidates)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("instagram", "facebook", "google"):
        print("usage: 21_discovery.py instagram|facebook|google [--login]")
        sys.exit(2)
    PLATFORM = sys.argv[1]
    main()
