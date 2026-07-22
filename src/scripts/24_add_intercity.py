#!/usr/bin/env python3
"""Add the three intercity bus lines that run from Tehuacán centro south/southeast
(Interoceánico, Tecoxteo, Sierra Negra) as `foránea` routes.

No recorded ride exists, so geometry is built by routing along the real roads
(OSRM) through the served towns — realistic, but marked as road-routed (not a GPS
trace) and flagged for review. Each line keeps its downtown terminal + the towns
it serves so it's searchable. Sources: online listings (see docs).
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTES = ROOT / "resources" / "map-data" / "routes.js"
CSV = ROOT / "resources" / "data" / "master_route_index.csv"
OSRM = "https://router.project-osrm.org/route/v1/driving/"

# [lon, lat]
T_INDEP = [-97.383, 18.4625]      # Av. Independencia Ote (Interoceánico #323, Tecoxteo #511)
T_TECOX = [-97.380, 18.4625]
T_JOSEFA = [-97.381, 18.4575]     # Josefa Ortiz de Domínguez (Sierra Negra #521)
ALTEPEXI = [-97.29861, 18.3675]
AJALPAN = [-97.25944, 18.37833]
ZINACATEPEC = [-97.245, 18.33472]
CALIPAN = [-97.16389, 18.29583]
COXCATLAN = [-97.14639, 18.26444]
TILAPA = [-97.10207, 18.16321]
COYOMEAPAN = [-96.99278, 18.28472]
TLACOTEPEC = [-96.82196, 18.37682]

LINES = [
    {"id": "interoceanico", "name": "Interoceánico — Ajalpan · Altepexi · Coxcatlán",
     "alias": "Interoceánicos", "color": "#e8590c",
     "terminal": "Av. Independencia 323, Centro, Tehuacán", "phone": "238 383 8192", "hours": "",
     "colonias": ["Altepexi", "Ajalpan", "San Sebastián Zinacatepec", "Coxcatlán"],
     "pts": [T_INDEP, ALTEPEXI, AJALPAN, ZINACATEPEC, COXCATLAN]},
    {"id": "tecoxteo", "name": "Tecoxteo — Tehuacán · Coxcatlán · Teotitlán",
     "alias": "Tehcoxteo", "color": "#1971c2",
     "terminal": "Av. Independencia Ote., Centro, Tehuacán", "phone": "", "hours": "",
     "colonias": ["San Diego", "San Pablo", "Santa Cruz", "Altepexi", "Ajalpan",
                  "San Sebastián Zinacatepec", "Calipan", "Coxcatlán", "Pueblo Nuevo",
                  "San Rafael", "San José Tilapa"],
     "pts": [T_TECOX, ALTEPEXI, AJALPAN, ZINACATEPEC, CALIPAN, COXCATLAN, TILAPA]},
    {"id": "sierra-negra", "name": "Sierra Negra — Ajalpan · Coyomeapan · Tlacotepec",
     "alias": "Autobuses Sierra Negra", "color": "#2f9e44",
     "terminal": "Josefa Ortiz de Domínguez 521, Tehuacán", "phone": "238 383 5000",
     "hours": "Lun–Vie 9–20 · Sáb 9–20:30 · Dom 9–18:30",
     "colonias": ["Ajalpan", "Santa María Coyomeapan", "San Sebastián Tlacotepec",
                  "San Miguel Eloxochitlán"],
     "pts": [T_JOSEFA, AJALPAN, COYOMEAPAN, TLACOTEPEC]},
]


def osrm(pts):
    coords = ";".join(f"{lon},{lat}" for lon, lat in pts)
    url = OSRM + coords + "?overview=full&geometries=geojson"
    req = urllib.request.Request(url, headers={"User-Agent": "mitehuacan.mx"})
    for _ in range(2):
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=40).read())
            if d.get("routes"):
                return d["routes"][0]["geometry"]["coordinates"]
        except Exception as e:  # noqa: BLE001
            print("  osrm retry:", e)
            time.sleep(3)
    print("  osrm FAILED — falling back to straight polyline through the towns")
    return pts


def main():
    t = ROUTES.read_text(encoding="utf-8")
    prefix = t[:t.index("{")]
    data = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1])
    existing = {f["properties"]["id"] for f in data["features"]}

    added = 0
    for L in LINES:
        if L["id"] in existing:
            print(f"  {L['id']} already present, skipping")
            continue
        geom = osrm(L["pts"])
        km = 0.0
        for a, b in zip(geom, geom[1:]):
            km += ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 * 111
        feat = {
            "type": "Feature",
            "properties": {
                "id": L["id"], "name": L["name"], "alias": L["alias"],
                "colonias": L["colonias"], "places": L["colonias"], "kind": "foránea",
                "sources": ["online listings"], "color": L["color"],
                "geom_source": "osrm-roads", "has_geom": True, "review": True,
                "terminal": L["terminal"], "phone": L["phone"], "hours": L["hours"],
            },
            "geometry": {"type": "MultiLineString", "coordinates": [[[round(x, 6), round(y, 6)] for x, y in geom]]},
        }
        data["features"].append(feat)
        added += 1
        print(f"  + {L['id']}: {len(geom)} pts, ~{km:.0f} km, {len(L['colonias'])} towns")

    ROUTES.write_text(prefix + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n",
                      encoding="utf-8")
    # master index rows (name,alias,kind,source,has_geom,geojson,...) — keep it simple
    with open(CSV, "a", encoding="utf-8") as fh:
        for L in LINES:
            if L["id"] in existing:
                continue
            fh.write(f'\n{L["id"]},{L["name"]},foránea,online listings,yes,,no,yes,no,yes,'
                     f'"intercity bus; geometry road-routed (OSRM), not a recorded ride; terminal: {L["terminal"]}",'
                     f'{L["alias"]},online listing,"{", ".join("Colonia "+c for c in L["colonias"])}"')
    print(f"\nadded {added} intercity routes -> resources/map-data/routes.js")


if __name__ == "__main__":
    main()
