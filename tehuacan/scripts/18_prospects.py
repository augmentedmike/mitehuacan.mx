#!/usr/bin/env python3
"""Sales prospecting lists from DENUE × route geometry.

For each route: every registered business within WALK_M of the line, ranked by
category sales-priority (foot-traffic businesses first — the Phase-1 targets in
docs/marketing-plan.md). Output: one CSV per route + a summary ranking routes
by prospect density (where to send the sellers first).

Usage:  python3 tehuacan/scripts/18_prospects.py [route-id ...]
Output: tehuacan/prospects/<route>.csv + tehuacan/prospects/_summary.csv
"""
import csv
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
build_pois = importlib.import_module("15_build_pois")

ROOT = Path(__file__).resolve().parent.parent
WALK_M = 150  # sponsor pin rule: the storefront must be right on the route

# category -> sales priority (1 = knock first). Phase-1 foot-traffic targets.
PRIORITY = {
    "farmacia": 1, "restaurante": 1, "café": 1, "panadería": 1, "súper": 1,
    "abarrotes": 2, "ferretería": 1, "taller": 1, "llantera": 1, "refacciones": 1,
    "estética": 1, "dentista": 1, "consultorio": 1, "veterinaria": 1,
    "gimnasio": 1, "escuela": 2, "inmobiliaria": 1, "hotel": 1,
    "electrónica": 1, "muebles": 1, "celulares": 1, "banco": 2,
    "óptica": 1, "zapatería": 2, "ropa": 2, "papelería": 2, "tortillería": 3,
}
DEFAULT_PRIORITY = 3


def load(js_path, const_name):
    txt = (ROOT / js_path).read_text(encoding="utf-8")
    return json.loads(txt[txt.index("{"):txt.rstrip().rstrip(";").rindex("}") + 1])


def main():
    routes = build_pois.load_routes()
    to_m = build_pois.meter_space(18.462)
    places = load("map/denue.js", "DENUE")["places"] + load("map/places.js", "PLACES")["places"]

    want = set(sys.argv[1:])
    outdir = ROOT / "prospects"
    outdir.mkdir(exist_ok=True)
    summary = []

    for f in routes["features"]:
        rid = f["properties"]["id"]
        if want and rid not in want:
            continue
        parts = [[to_m(lon, lat) for lon, lat in part] for part in f["geometry"]["coordinates"]]
        rows = []
        for p in places:
            px, py = to_m(*p["c"])
            d = min((build_pois.dist_point_polyline(px, py, pp) for pp in parts if len(pp) > 1),
                    default=1e9)
            if d <= WALK_M:
                rows.append({
                    "prioridad": PRIORITY.get(p["k"], DEFAULT_PRIORITY),
                    "negocio": p["n"], "categoria": p["k"],
                    "dist_m": round(d), "lat": p["c"][1], "lon": p["c"][0],
                    "maps": f"https://mitehuacan.mx/?ruta={rid}",
                })
        rows.sort(key=lambda r: (r["prioridad"], r["categoria"], r["dist_m"]))
        if rows:
            with open(outdir / f"{rid}.csv", "w", newline="", encoding="utf-8-sig") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
        p1 = sum(1 for r in rows if r["prioridad"] == 1)
        summary.append({"ruta": rid, "nombre": f["properties"]["name"],
                        "prospectos": len(rows), "prioridad_1": p1})

    summary.sort(key=lambda s: -s["prioridad_1"])
    with open(outdir / "_summary.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=["ruta", "nombre", "prospectos", "prioridad_1"])
        w.writeheader()
        w.writerows(summary)
    top = summary[:8]
    total = sum(s["prospectos"] for s in summary)
    print(f"prospects: {total} route-adjacencies across {len(summary)} routes -> tehuacan/prospects/")
    for s in top:
        print(f"  {s['nombre']:<30} {s['prospectos']:>5} prospectos ({s['prioridad_1']} prioridad 1)")


if __name__ == "__main__":
    main()
