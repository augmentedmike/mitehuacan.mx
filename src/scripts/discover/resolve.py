#!/usr/bin/env python3
"""Location resolver: backfill coordinates for discovered businesses that have a
name but no location (Instagram/Facebook accounts don't carry coords).

For each no-coord record it searches Google Maps by name and, if a confident
match sits inside the service area, writes the coordinates back onto the record —
which then makes it publishable to search. Businesses with no Google Maps listing
at all (e.g. Instagram-only like Yoms!) stay unresolved and need an owner pin.

  python3 src/scripts/discover/resolve.py [--batch N] [--all]

Bounded batches with a per-store cursor, same as the discovery agents.
"""
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import AUTH, DISC, norm   # noqa: E402
import sqlite3   # noqa: E402

STORES = ["instagram", "facebook"]
BBOX = (18.10, 18.90, -97.70, -96.90)   # service-area lat/lon bounds
GENERIC = ("restaurante", "cafeteria", "taqueria", "tienda", "farmacia", "estetica",
           "barberia", "boutique", "antojitos", "panaderia", "bar")


def strip_generic(n):
    for g in GENERIC:
        gn = norm(g)
        if n.startswith(gn) and len(n) > len(gn) + 2:
            return n[len(gn):]
    return n


def core(n):
    # strip the generic category word AND the ever-present place words, so the
    # distinctive brand is what's compared (not "tehuacan", in ~every name)
    n = strip_generic(norm(n))
    for w in ("tehuacan", "tehuacana", "puebla", "sucursal", "oficial"):
        n = n.replace(w, "")
    return n


def match(a, b):
    ca, cb = core(a), core(b)
    if len(ca) < 4 or len(cb) < 4:          # nothing distinctive left → not a match
        return False
    return ca == cb or ca.startswith(cb) or cb.startswith(ca) \
        or (len(cb) >= 5 and cb in ca) or (len(ca) >= 5 and ca in cb)


def resolve_one(page, name):
    url = "https://www.google.com/maps/search/" + (name + " Tehuacán").replace(" ", "+")
    try:
        page.goto(url, timeout=45000)
        page.wait_for_timeout(3200)
    except Exception:  # noqa: BLE001
        return None
    for a in page.query_selector_all('div[role="feed"] a[aria-label][href*="/maps/place/"]')[:5]:
        rname = a.get_attribute("aria-label") or ""
        href = a.get_attribute("href") or ""
        m = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", href)
        if not m:
            continue
        lat, lon = float(m.group(1)), float(m.group(2))
        if BBOX[0] <= lat <= BBOX[1] and BBOX[2] <= lon <= BBOX[3] and match(name, rname):
            return round(lat, 6), round(lon, 6), rname
    # single-result page: coords land in the URL
    m2 = re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", page.url)
    if m2:
        lat, lon = float(m2.group(1)), float(m2.group(2))
        if BBOX[0] <= lat <= BBOX[1] and BBOX[2] <= lon <= BBOX[3] and "/place/" in page.url:
            return round(lat, 6), round(lon, 6), "(single result)"
    return None


def main():
    from playwright.sync_api import sync_playwright
    args = sys.argv[1:]
    batch = 30
    if "--batch" in args:
        batch = int(args[args.index("--batch") + 1])
    all_ = "--all" in args

    # gather no-coord candidates across stores
    todo = []
    for s in STORES:
        p = DISC / f"{s}.db"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        for key, name in db.execute(
                "SELECT key, name FROM records WHERE lat IS NULL AND status IN ('candidate','approved') ORDER BY first_seen"):
            todo.append((s, key, name))
        db.close()
    print(f"{len(todo)} no-coord records across {STORES}")
    if not all_:
        cur_f = DISC / "resolve.cursor"
        start = int(cur_f.read_text()) % max(1, len(todo)) if cur_f.exists() else 0
        todo = (todo + todo)[start:start + batch]
        cur_f.write_text(str((start + batch) % max(1, len(todo) or 1)))
        print(f"this run: {len(todo)} records")

    prof = AUTH / "google" / "default"
    opts = dict(headless=True, viewport={"width": 1280, "height": 900}, locale="es-MX",
                ignore_default_args=["--enable-automation", "--use-mock-keychain"],
                args=["--disable-blink-features=AutomationControlled", "--no-first-run"])
    resolved = unresolved = 0
    with sync_playwright() as pw:
        try:
            ctx = pw.chromium.launch_persistent_context(str(prof), channel="chrome", **opts)
        except Exception:  # noqa: BLE001
            ctx = pw.chromium.launch_persistent_context(str(prof), **opts)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        conns = {s: sqlite3.connect(DISC / f"{s}.db") for s in STORES}
        for i, (s, key, name) in enumerate(todo, 1):
            hit = resolve_one(page, name)
            if hit:
                lat, lon, rname = hit
                conns[s].execute("UPDATE records SET lat=?, lon=? WHERE key=?", (lat, lon, key))
                conns[s].commit()
                resolved += 1
                print(f"  [{i}/{len(todo)}] RESOLVED {name!r} -> {lat},{lon}  (google: {rname[:40]!r})")
            else:
                unresolved += 1
            time.sleep(1.5)
        for c in conns.values():
            c.close()
        ctx.close()
    print(f"\nresolved {resolved}, unresolved {unresolved} (no Google Maps match — need an owner pin)")


if __name__ == "__main__":
    main()
