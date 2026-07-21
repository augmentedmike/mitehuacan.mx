#!/usr/bin/env python3
"""Location + contact resolver for no-coord discovered businesses.

Instagram/Facebook business accounts don't return coordinates in search, but
they DO publish an address, phone and hours in their bio/about. This reads that
bio, parses 📍address / phone / hours, and geocodes the address — Tehuacán
addresses are usually esquinas ("Reforma Nte esq 16 Ote"), which resolve
directly against our own streets layer (calles cruces). Google-Maps-by-name is
the fallback when the bio has no usable address.

  python3 src/scripts/discover/resolve.py [--batch N] [--all]

Writes lat/lon + address/phone/hours back onto the record, which then makes it
publishable to search.
"""
import json
import re
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import AUTH, DISC, ROOT, norm   # noqa: E402

BBOX = (18.10, 18.90, -97.70, -96.90)
CENTER = (18.462, -97.396)   # disambiguate repeated street names toward centro
PIN_RE = re.compile(r"📍\s*([^\n📍🕖🕗🕘👇🛵🚚☎📞]+)")
PHONE_RE = re.compile(r"\b(\d{3})[\s.\-]?(\d{3})[\s.\-]?(\d{4})\b")
HOURS_RE = re.compile(r"\d{1,2}[:.]\d{2}\s*[ap]\.?\s?m\.?(?:\s*[-a]+\s*\d{1,2}[:.]\d{2}\s*[ap]\.?\s?m\.?)?", re.I)
STOP = {"calle", "avenida", "av", "de", "la", "el", "del", "los", "las", "col", "colonia", "no", "num"}
ABBR = {"nte": "norte", "ote": "oriente", "pte": "poniente", "pnte": "poniente",
        "sur": "sur", "nor": "norte", "blvd": "boulevard", "blvrd": "boulevard", "priv": "privada"}


def _norm_sp(s):
    """lowercase + strip accents but KEEP word spacing (punctuation -> space)."""
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", s)).strip()


def expand(s):
    s = _norm_sp(s)
    for a, b in ABBR.items():
        s = re.sub(r"\b" + a + r"\b", b, s)
    return re.sub(r"\s+", " ", s).strip()


def load_cruces():
    t = (ROOT / "resources" / "map-data" / "calles.js").read_text(encoding="utf-8")
    data = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1])
    return [(expand(c["n"]), c["c"]) for c in data.get("cruces", [])]


def parse_bio(text):
    addr = phone = hours = None
    m = PIN_RE.search(text)
    if m:
        addr = HOURS_RE.sub("", m.group(1)).strip(" .·-\t")
        addr = re.sub(r"\s{2,}", " ", addr)[:120] or None
    p = PHONE_RE.search(text)
    if p:
        phone = f"{p.group(1)} {p.group(2)} {p.group(3)}"
    h = HOURS_RE.search(text)
    if h:
        hours = h.group(0).strip()
    return addr, phone, hours


def geocode(addr, cruces):
    """esquina addresses resolve against our streets layer's intersections."""
    if not addr:
        return None
    a = expand(addr)
    a = re.sub(r"#?\s*\d+\s*-?\s*[a-z]?\b", " ", a)      # drop the street number (#1600-A)
    parts = [p.strip() for p in re.split(r"\besq\w*\b|\bcon\b|\bentre\b|\by\b|&|/", a) if len(p.strip()) > 2]
    if len(parts) < 2:
        return None
    toks = set()
    for p in parts[:2]:
        toks.update(w for w in p.split() if w and w not in STOP and len(w) > 1)
    if len(toks) < 2:
        return None
    pats = [re.compile(r"\b" + re.escape(tk) + r"\b") for tk in toks]
    matches = [c for name, c in cruces
               if all(p.search(name) for p in pats)
               and BBOX[0] <= c[1] <= BBOX[1] and BBOX[2] <= c[0] <= BBOX[3]]
    if not matches:
        return None
    return min(matches, key=lambda c: (c[1] - CENTER[0]) ** 2 + (c[0] - CENTER[1]) ** 2)


def _launch(pw, profile):
    opts = dict(headless=True, viewport={"width": 1280, "height": 900}, locale="es-MX",
                ignore_default_args=["--enable-automation", "--use-mock-keychain"],
                args=["--disable-blink-features=AutomationControlled", "--no-first-run"])
    try:
        return pw.chromium.launch_persistent_context(str(profile), channel="chrome", **opts)
    except Exception:  # noqa: BLE001
        return pw.chromium.launch_persistent_context(str(profile), **opts)


def ig_bio(page, handle):
    try:
        page.goto(f"https://www.instagram.com/{handle}/", timeout=45000)
        page.wait_for_timeout(3000)
        h = page.query_selector("header")
        return h.inner_text() if h else ""
    except Exception:  # noqa: BLE001
        return ""


def fb_bio(page, url):
    try:
        page.goto(url, timeout=45000)
        page.wait_for_timeout(4000)
        main = page.query_selector('div[role="main"]')
        return main.inner_text()[:2500] if main else ""
    except Exception:  # noqa: BLE001
        return ""


def main():
    from playwright.sync_api import sync_playwright
    args = sys.argv[1:]
    batch = int(args[args.index("--batch") + 1]) if "--batch" in args else 30
    all_ = "--all" in args
    cruces = load_cruces()

    todo = {"instagram": [], "facebook": []}
    for s in ("instagram", "facebook"):
        p = DISC / f"{s}.db"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        rows = db.execute("SELECT key, name, handle, url FROM records "
                          "WHERE lat IS NULL AND status IN ('candidate','approved') ORDER BY first_seen").fetchall()
        todo[s] = rows
        db.close()
    total = sum(len(v) for v in todo.values())
    print(f"{total} no-coord records (instagram {len(todo['instagram'])}, facebook {len(todo['facebook'])})")

    if not all_:
        cur_f = DISC / "resolve.cursor"
        flat = [("instagram", r) for r in todo["instagram"]] + [("facebook", r) for r in todo["facebook"]]
        start = (int(cur_f.read_text()) % len(flat)) if cur_f.exists() and flat else 0
        chunk = (flat + flat)[start:start + batch]
        cur_f.write_text(str((start + batch) % max(1, len(flat))))
        todo = {"instagram": [r for s, r in chunk if s == "instagram"],
                "facebook": [r for s, r in chunk if s == "facebook"]}
        print(f"this run: {len(chunk)} records (from cursor {start})")

    resolved = 0
    with sync_playwright() as pw:
        for source, bio_fn, url_from in (("instagram", ig_bio, lambda r: r[2]),
                                         ("facebook", fb_bio, lambda r: r[3])):
            rows = todo[source]
            if not rows:
                continue
            ctx = _launch(pw, AUTH / source / "default")
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            db = sqlite3.connect(DISC / f"{source}.db")
            for key, name, handle, url in rows:
                text = bio_fn(page, url_from((key, name, handle, url)))
                addr, phone, hours = parse_bio(text)
                c = geocode(addr, cruces)
                if c or addr or phone or hours:
                    db.execute(
                        "UPDATE records SET lat=COALESCE(?,lat), lon=COALESCE(?,lon), "
                        "address=COALESCE(?,address), phone=COALESCE(?,phone), hours=COALESCE(?,hours) WHERE key=?",
                        (c[1] if c else None, c[0] if c else None, addr, phone, hours, key))
                    db.commit()
                    if c:
                        resolved += 1
                        print(f"  RESOLVED {name!r} -> {c[1]},{c[0]}  addr={addr!r} tel={phone}")
                    else:
                        print(f"  got contact for {name!r} (addr={addr!r} tel={phone}) but no geocode")
                time.sleep(1.5)
            db.close()
            ctx.close()
    print(f"\nresolved coordinates for {resolved} businesses from their bio")


if __name__ == "__main__":
    main()
