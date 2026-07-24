#!/usr/bin/env python3
"""Backfill event HOST from Facebook's PUBLIC og: metadata — no login needed.

Facebook serves og:description to anonymous fetches for public events, templated:
    "Evento en <place> de <host> el <weekday>, <month> <day> <year>"
so we can pull the HOST and write it into every *_events.db store.
25_publish_events.py then emits it and the /eventos/ panel shows "👤 <host>".

(og:image is a lookaside crawler URL that returns HTML and won't hotlink onto our
page, so we don't use it — cover images would need downloading + rehosting. The
full About text, street address and exact time are only visible to a signed-in
session, so those come from the deep scrape in fb_events.py.)

    python3 src/scripts/26_enrich_events_og.py
"""
import html
import re
import sqlite3
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISC = ROOT / "resources" / "discovery"
UA = "Mozilla/5.0 (compatible; MiTehuacanBot/1.0; +https://mitehuacan.mx)"

OG = re.compile(r'<meta property="og:(title|description)" content="([^"]*)"')
# host sits between the LAST " de " and " el <weekday>"; greedy .* grabs the last one
HOST = re.compile(
    r"^Evento en .* de (.+?) el (?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\b",
    re.I)


def fetch_og(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        page = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")
    except Exception:  # noqa: BLE001
        return {}
    return {k: html.unescape(v).strip() for k, v in OG.findall(page)}


def main():
    stores = sorted(DISC.glob("*_events.db"))
    if not stores:
        raise SystemExit(f"no *_events.db stores in {DISC}")
    grand = 0
    for db_path in stores:
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        for col in ("addr", "descr", "time_", "host", "image"):   # match lib.py schema
            try:
                db.execute(f"ALTER TABLE records ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass
        rows = db.execute(
            "SELECT key, url FROM records "
            "WHERE url LIKE '%facebook.com/events/%' AND status IN ('candidate','approved') "
            "AND host IS NULL").fetchall()
        upd = 0
        for r in rows:
            og = fetch_og(r["url"])
            if not og:
                continue
            m = HOST.search(og.get("description", ""))
            host = m.group(1).strip()[:80] if m else None
            if host:
                db.execute("UPDATE records SET host=COALESCE(host,?) WHERE key=?", (host, r["key"]))
                upd += 1
            time.sleep(0.4)                      # be gentle
        db.commit()
        db.close()
        grand += upd
        print(f"{db_path.name}: enriched {upd}/{len(rows)} FB events with host")
    print(f"done — {grand} events got a host. "
          f"Now run: python3 src/scripts/25_publish_events.py")


if __name__ == "__main__":
    main()
