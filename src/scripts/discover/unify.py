#!/usr/bin/env python3
"""Cross-source entity resolution.

Merge the per-source stores (google/instagram/facebook + optional others) into
ONE canonical place per business, so "Yoms! on Instagram" and its Google Maps
listing become a single record. Confidence = how many independent sources agree.

  python3 src/scripts/discover/unify.py            # rebuild unified.db + export

Matching: normalized name, with a second pass that strips a leading generic
category word ("Restaurante Casa Vieja" ↔ "Casa Vieja") and, when both records
have coordinates, requires them to be within ~250 m so distinct businesses that
share a common name ("Farmacia GI") don't collapse into one.

Output: resources/discovery/unified.db (table `places`) + unified.jsonl for the
admin approval flow. Idempotent — rebuilt from the source stores each run.
"""
import json
import math
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import DISC, norm, now_iso   # noqa: E402

SOURCES = ["google", "instagram", "facebook"]
GENERIC = ("restaurante", "cafeteria", "taqueria", "taquería", "tienda", "farmacia", "estetica",
           "estética", "barberia", "barbería", "consultorio", "clinica", "clínica", "abarrotes",
           "papeleria", "papelería", "boutique", "hotel", "bar", "antojitos", "panaderia", "panadería")


def match_key(name):
    """normalized name with a leading generic word stripped, for cross-source join."""
    n = norm(name)
    for g in GENERIC:
        gn = norm(g)
        if n.startswith(gn) and len(n) > len(gn) + 2:
            return n[len(gn):]
    return n


def dist_m(a, b):
    if None in a or None in b:
        return 0.0
    (la1, lo1), (la2, lo2) = a, b
    return math.hypot((la1 - la2) * 111000, (lo1 - lo2) * 105000)


def load(source):
    p = DISC / f"{source}.db"
    if not p.exists():
        return []
    db = sqlite3.connect(p)
    db.row_factory = sqlite3.Row
    rows = [dict(r) for r in db.execute(
        "SELECT * FROM records WHERE status IN ('candidate','approved')")]
    db.close()
    return rows


def main():
    recs = []
    for s in SOURCES:
        recs += load(s)
    print(f"loaded {len(recs)} records from {len(SOURCES)} sources")

    # group by match key; split a group if two members have coords >250m apart
    groups = {}
    for r in recs:
        k = match_key(r["name"])
        if len(k) < 3:
            continue
        placed = False
        for g in groups.setdefault(k, []):
            gc = (g["lat"], g["lon"])
            rc = (r.get("lat"), r.get("lon"))
            if None in gc or None in rc or dist_m(gc, rc) < 250:
                g["members"].append(r)
                if g["lat"] is None and r.get("lat"):
                    g["lat"], g["lon"] = r["lat"], r["lon"]
                placed = True
                break
        if not placed:
            groups[k].append({"lat": r.get("lat"), "lon": r.get("lon"), "members": [r]})

    udb = sqlite3.connect(DISC / "unified.db")
    udb.execute("DROP TABLE IF EXISTS places")
    udb.execute("""CREATE TABLE places(
        key TEXT PRIMARY KEY, name TEXT, lat REAL, lon REAL, category TEXT,
        sources TEXT, confidence INTEGER,
        google TEXT, instagram TEXT, facebook TEXT, updated TEXT)""")

    now = now_iso()
    unified, conf = 0, {1: 0, 2: 0, 3: 0}
    for k, glist in groups.items():
        for i, g in enumerate(glist):
            ms = g["members"]
            srcs = sorted(set(m["source"] for m in ms))
            name = max((m["name"] for m in ms), key=len)
            lat = lon = None
            for m in ms:
                if m.get("lat") and m.get("lon"):
                    lat, lon = m["lat"], m["lon"]
                    break
            cats = sorted({m["category"] for m in ms if m.get("category")})
            gg = next((m["url"] for m in ms if m["source"] == "google"), None)
            ig = next((m.get("handle") or m.get("url") for m in ms if m["source"] == "instagram"), None)
            fb = next((m["url"] for m in ms if m["source"] == "facebook"), None)
            udb.execute("INSERT OR REPLACE INTO places VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (f"{k}:{i}", name[:80], lat, lon, ", ".join(cats),
                         ", ".join(srcs), len(srcs), gg, ig, fb, now))
            unified += 1
            conf[len(srcs)] = conf.get(len(srcs), 0) + 1
    udb.commit()

    # export the merged queue
    rows = udb.execute("SELECT name,lat,lon,category,sources,confidence,google,instagram,facebook "
                       "FROM places ORDER BY confidence DESC, name").fetchall()
    with open(DISC / "unified.jsonl", "w", encoding="utf-8") as fh:
        cols = ["name", "lat", "lon", "category", "sources", "confidence", "google", "instagram", "facebook"]
        for r in rows:
            fh.write(json.dumps({c: v for c, v in zip(cols, r) if v is not None}, ensure_ascii=False) + "\n")
    udb.close()

    print(f"unified {unified} canonical places -> resources/discovery/unified.db")
    print(f"  confidence: {conf.get(3,0)} on all 3 sources, {conf.get(2,0)} on 2, {conf.get(1,0)} single-source")


if __name__ == "__main__":
    main()
