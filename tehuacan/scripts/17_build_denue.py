#!/usr/bin/env python3
"""DENUE → the places layer that actually covers the city.

INEGI's DENUE lists EVERY registered business establishment in Mexico with
name, SCIAN activity, and coordinates (Términos de Libre Uso MX — free reuse
with attribution). OSM has ~400 commercial places around Tehuacán; DENUE has
tens of thousands. This script filters the Puebla state CSV to the service
area (bbox of the route network + buffer, same rule as 16_refresh_pois) and
emits map/denue.js — loaded lazily by the app and searched like every other
tier.

Input:  poi/denue_puebla.csv (from denue_21_csv.zip, INEGI; refreshed ~2x/yr)
Output: map/denue.js  const DENUE = {places: [{n, c: [lon,lat], k}]}
"""
import csv
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
build_pois = importlib.import_module("15_build_pois")

ROOT = Path(__file__).resolve().parent.parent
BUFFER_DEG = 0.03

# SCIAN activity name → short chip. Substring match, first hit wins, order matters.
KIND = [
    ("abarrotes", "abarrotes"), ("supermercado", "súper"), ("autoservicio", "súper"),
    ("tortilla", "tortillería"), ("panader", "panadería"), ("carnicer", "carnicería"),
    ("carne de aves", "pollería"), ("frutas y verduras", "frutería"), ("pescados", "mariscos"),
    ("dulces", "dulcería"), ("paletas de hielo", "nieves"), ("nieve", "nieves"),
    ("agua purificada", "purificadora"), ("hielo", "purificadora"),
    ("restaurante", "restaurante"), ("preparación de tacos", "tacos"),
    ("antojitos", "antojitos"), ("comida para llevar", "comida"),
    ("cafeter", "café"), ("juguer", "juguería"), ("bares", "bar"), ("cerveza", "depósito"),
    ("farmacia", "farmacia"), ("consultorio", "consultorio"), ("dental", "dentista"),
    ("hospital", "hospital"), ("laboratorio", "laboratorio"), ("óptica", "óptica"),
    ("veterinari", "veterinaria"),
    ("ropa", "ropa"), ("calzado", "zapatería"), ("bisuter", "accesorios"),
    ("joyer", "joyería"), ("perfumer", "perfumería"), ("cosmétic", "belleza"),
    ("salones y clínicas de belleza", "estética"), ("peluquer", "estética"),
    ("telas", "telas"), ("mercer", "mercería"), ("bonetería", "mercería"),
    ("electrodomésticos", "electrónica"), ("computadoras", "computación"),
    ("teléfonos", "celulares"), ("electrónic", "electrónica"),
    ("muebles", "muebles"), ("colchones", "muebles"),
    ("ferreter", "ferretería"), ("tlapaler", "ferretería"), ("pinturas", "pinturas"),
    ("materiales para la construcción", "materiales"),
    ("papeler", "papelería"), ("libros", "librería"), ("regalos", "regalos"),
    ("juguetes", "juguetería"), ("deportivos", "deportes"), ("mascotas", "mascotas"),
    ("florer", "florería"), ("plantas", "vivero"),
    ("refacciones", "refacciones"), ("llantas", "llantera"),
    ("reparación mecánica", "taller"), ("hojalatería", "taller"),
    ("lavado y lubricado", "autolavado"), ("motocicletas", "motos"), ("bicicletas", "bicicletas"),
    ("gasolina", "gasolinera"), ("gas l.p", "gasera"),
    ("banca múltiple", "banco"), ("cajas de ahorro", "caja de ahorro"),
    ("casas de empeño", "casa de empeño"), ("cambio de divisas", "casa de cambio"),
    ("hoteles", "hotel"), ("moteles", "hotel"),
    ("lavander", "lavandería"), ("tintorer", "tintorería"),
    ("fotograf", "fotografía"), ("fotocopiado", "copias"),
    ("gimnasio", "gimnasio"), ("cine", "cine"), ("billares", "billar"),
    ("escuela", "escuela"), ("guarder", "guardería"),
    ("iglesia", "iglesia"), ("asociaciones religiosas", "iglesia"),
    ("funerar", "funeraria"), ("notar", "notaría"), ("abogados", "abogados"),
    ("contabilidad", "contadores"), ("bienes raíces", "inmobiliaria"),
    ("mensajer", "paquetería"), ("autobuses", "terminal"), ("taxis", "sitio de taxis"),
    ("sastrer", "sastrería"), ("costura", "costura"), ("zapatos, reparación", "reparación calzado"),
    ("vidrios", "vidriería"), ("herrer", "herrería"), ("carpinter", "carpintería"),
    ("imprenta", "imprenta"), ("rotulación", "rótulos"), ("publicidad", "publicidad"),
    ("cerrajer", "cerrajería"), ("mudanzas", "mudanzas"),
]
# activities that don't help a rider find a destination
SKIP = ("crianza", "cultivo", "explotación", "minería", "fabricación", "confección en serie",
        "elaboración de", "servicios de apoyo a los negocios", "captación, tratamiento",
        "generación", "transmisión", "autotransporte de carga", "edificación",
        "instalaciones eléctricas en construcciones", "trabajos de")


def kind_for(act):
    a = act.lower()
    for needle, k in KIND:
        if needle in a:
            return k
    # generic fallbacks: anything retail/service is still a destination someone
    # will search for — only true non-destinations (SKIP) get dropped
    if a.startswith("comercio al por menor"):
        return "tienda"
    if a.startswith("comercio al por mayor"):
        return "mayoreo"
    if "reparación" in a or "mantenimiento" in a:
        return "taller"
    if a.startswith("servicios") or "servicio" in a or a.startswith("otros"):
        return "servicio"
    if a.startswith("consultorios") or "médic" in a or "salud" in a:
        return "salud"
    return None


def main():
    src = ROOT / "poi" / "denue_puebla.csv"
    routes = build_pois.load_routes()
    lons, lats = [], []
    for f in routes["features"]:
        for part in f["geometry"]["coordinates"]:
            for lon, lat in part:
                lons.append(lon)
                lats.append(lat)
    s, w = min(lats) - BUFFER_DEG, min(lons) - BUFFER_DEG
    n, e = max(lats) + BUFFER_DEG, max(lons) + BUFFER_DEG

    # OSM places already shipped: skip DENUE rows that duplicate them nearby
    osm = []
    pj = ROOT / "map" / "places.js"
    if pj.exists():
        txt = pj.read_text(encoding="utf-8")
        osm = json.loads(txt[txt.index("{"):txt.rstrip().rstrip(";").rindex("}") + 1])["places"]
    osm_keys = {(p["n"].lower()[:18], round(p["c"][0], 3), round(p["c"][1], 3)) for p in osm}

    kept, skipped_act, seen = [], 0, set()
    with open(src, encoding="latin-1", newline="") as fh:
        r = csv.DictReader(fh)
        for row in r:
            try:
                lat, lon = float(row["latitud"]), float(row["longitud"])
            except (ValueError, KeyError):
                continue
            if not (s <= lat <= n and w <= lon <= e):
                continue
            act = row.get("nombre_act", "")
            la = act.lower()
            if any(x in la for x in SKIP):
                skipped_act += 1
                continue
            k = kind_for(act)
            if k is None:
                skipped_act += 1
                continue
            name = " ".join(row.get("nom_estab", "").split()).title()[:60]
            if len(name) < 3:
                continue
            key = (name.lower(), round(lon, 4), round(lat, 4))
            if key in seen:
                continue
            seen.add(key)
            if (name.lower()[:18], round(lon, 3), round(lat, 3)) in osm_keys:
                continue
            kept.append({"n": name, "c": [round(lon, 6), round(lat, 6)], "k": k})

    kept.sort(key=lambda p: p["n"].lower())
    out = ROOT / "map" / "denue.js"
    out.write_text(
        "// generated by scripts/17_build_denue.py from INEGI DENUE (Términos de\n"
        "// Libre Uso MX — fuente: INEGI, DENUE). SEARCH data only, never pins.\n"
        "const DENUE = " + json.dumps({"places": kept}, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")
    kb = out.stat().st_size // 1024
    print(f"denue: {len(kept)} places in service area ({kb} KB), {skipped_act} filtered as non-destination")


if __name__ == "__main__":
    main()
