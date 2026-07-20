#!/usr/bin/env python3
"""Periodic POI/places refresh — THE agent that keeps the map's point data alive.

Run weekly by .github/workflows/refresh-pois.yml (and by hand whenever):
  1. derives the service area from routes.js itself (bbox of every route + 3 km
     buffer) — mapping a new corridor automatically widens the net;
  2. pulls fresh OSM data via Overpass for BOTH layers:
       - public services (schools/health/gov)  -> poi/pois_osm.json
       - commercial destinations (supers, bancos, farmacias, mercados, cines,
         gasolineras, terminales)              -> poi/places_osm.json
  3. rebuilds app/pois.js (via 15_build_pois) and app/places.js.

Places are SEARCH data, not pins: the map never renders them unprompted
(commercial pins = sponsor pipeline, PRD-revenue.md). They surface only as
search suggestions. OSM coverage of chains in Tehuacán is thin today — this
agent means every OSM improvement lands here within a week, and the curated
places module (backoffice) can layer on top later.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib
build_pois = importlib.import_module("15_build_pois")

ROOT = Path(__file__).resolve().parent.parent
BUFFER_DEG = 0.03  # ~3 km
ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]
UA = "mitehuacan.mx data refresh (github.com/augmentedmike/mitehuacan.mx; augmentedmike@gmail.com)"

# places = EVERY named destination OSM knows in the service area, minus what's
# already in the public-services layer (pois.js) and minus street furniture.
PUBLIC_AMENITIES = ("school|kindergarten|college|university|townhall|courthouse|police|"
                    "post_office|hospital|clinic|library")
NOISE_AMENITIES = ("bench|waste_basket|waste_disposal|shelter|parking|parking_space|"
                   "parking_entrance|toilets|drinking_water|fountain|recycling|"
                   "vending_machine|telephone|atm|charging_station|bicycle_parking|"
                   "motorcycle_parking|loading_dock|hunting_stand|clock|post_box")
PLACE_KIND = {  # known tag values -> short Spanish chip; anything else shows its raw tag
    "supermarket": "súper", "convenience": "tienda", "department_store": "tienda",
    "mall": "plaza", "wholesale": "súper", "variety_store": "tienda",
    "doityourself": "ferretería", "hardware": "ferretería",
    "bank": "banco", "pharmacy": "farmacia", "marketplace": "mercado",
    "fuel": "gasolinera", "cinema": "cine", "bus_station": "terminal",
    "place_of_worship": "iglesia", "restaurant": "restaurante", "fast_food": "comida",
    "cafe": "café", "bar": "bar", "hotel": "hotel", "guest_house": "hotel",
    "attraction": "atracción", "museum": "museo", "park": "parque",
    "sports_centre": "deportivo", "stadium": "estadio", "pitch": "cancha",
    "swimming_pool": "alberca", "bakery": "panadería", "butcher": "carnicería",
    "clothes": "ropa", "shoes": "zapatería", "furniture": "muebles",
    "electronics": "electrónica", "mobile_phone": "celulares", "car_repair": "taller",
    "veterinary": "veterinaria", "dentist": "dentista", "doctors": "consultorio",
    # ropa / belleza
    "boutique": "ropa", "fabric": "telas", "tailor": "sastrería", "jewelry": "joyería",
    "bag": "bolsas", "cosmetics": "belleza", "beauty": "belleza", "hairdresser": "estética",
    "perfumery": "perfumería", "massage": "spa", "optician": "óptica",
    # comida / abarrotes
    "greengrocer": "frutería", "seafood": "mariscos", "deli": "abarrotes",
    "dairy": "lechería", "confectionery": "dulcería", "ice_cream": "nieves",
    "alcohol": "vinos y licores", "beverages": "bebidas", "water": "purificadora",
    "kiosk": "tienda", "general": "abarrotes", "food_court": "comida", "pub": "bar",
    # salud
    "chemist": "farmacia", "medical_supply": "equipo médico", "laboratory": "laboratorio",
    "physiotherapist": "fisioterapia", "alternative": "medicina alt.",
    "optometrist": "óptica", "midwife": "partera", "psychotherapist": "psicología",
    "childcare": "guardería", "social_facility": "asistencia social",
    # servicios / otros
    "stationery": "papelería", "books": "librería", "toys": "juguetería",
    "pet": "mascotas", "sports": "deportes", "gift": "regalos", "florist": "florería",
    "photo": "fotografía", "copyshop": "copias", "internet_cafe": "ciber",
    "laundry": "lavandería", "dry_cleaning": "tintorería", "travel_agency": "viajes",
    "funeral_directors": "funeraria", "car_parts": "refacciones", "tyres": "llantera",
    "motorcycle": "motos", "bicycle": "bicicletas", "paint": "pinturas",
    "driving_school": "autoescuela", "music_school": "música", "dance": "danza",
    "events_venue": "salón de eventos", "nightclub": "antro",
    "community_centre": "centro comunitario", "marketplace": "mercado",
}


def service_bbox():
    routes = build_pois.load_routes()
    lons, lats = [], []
    for f in routes["features"]:
        for part in f["geometry"]["coordinates"]:
            for lon, lat in part:
                lons.append(lon)
                lats.append(lat)
    return (min(lats) - BUFFER_DEG, min(lons) - BUFFER_DEG,
            max(lats) + BUFFER_DEG, max(lons) + BUFFER_DEG)


def overpass(query):
    data = ("data=" + urllib.parse.quote(query)).encode()
    last = None
    for url in ENDPOINTS:
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=120) as r:
                    return json.loads(r.read())
            except Exception as e:  # noqa: BLE001 — mirror fallback by design
                last = e
                time.sleep(5)
    raise RuntimeError(f"all overpass endpoints failed: {last}")


def fetch_public_services(bbox):
    s, w, n, e = bbox
    q = f"""[out:json][timeout:90];
(
  nwr["amenity"~"^(school|kindergarten|college|university|townhall|courthouse|police|post_office|hospital|clinic|library)$"]({s},{w},{n},{e});
  nwr["office"="government"]({s},{w},{n},{e});
  nwr["healthcare"~"^(hospital|clinic|centre)$"]({s},{w},{n},{e});
);
out center 6000;"""
    return overpass(q)


def fetch_places(bbox):
    s, w, n, e = bbox
    q = f"""[out:json][timeout:120];
(
  nwr["name"]["shop"]({s},{w},{n},{e});
  nwr["name"]["amenity"]["amenity"!~"^({PUBLIC_AMENITIES}|{NOISE_AMENITIES})$"]({s},{w},{n},{e});
  nwr["name"]["tourism"]({s},{w},{n},{e});
  nwr["name"]["leisure"]({s},{w},{n},{e});
  nwr["name"]["office"]["office"!="government"]({s},{w},{n},{e});
  nwr["name"]["craft"]({s},{w},{n},{e});
  nwr["name"]["healthcare"]["healthcare"!~"^(hospital|clinic|centre)$"]({s},{w},{n},{e});
);
out center 12000;"""
    return overpass(q)


def build_places(raw):
    seen, places = set(), []
    for el in raw.get("elements", []):
        tags = el.get("tags", {})
        name = (tags.get("name") or "").strip()
        if not name:
            continue
        kind = (tags.get("shop") or tags.get("amenity") or tags.get("healthcare") or
                tags.get("tourism") or tags.get("leisure") or tags.get("office") or
                tags.get("craft") or "")
        if not kind:
            continue
        # unknown categories keep their raw tag as the chip — everything named stays findable
        k = PLACE_KIND.get(kind, kind.replace("_", " ")[:18])
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        if lon is None:
            continue
        key = (round(lon, 4), round(lat, 4), name.lower())
        if key in seen:
            continue
        seen.add(key)
        places.append({"n": name[:60], "c": [round(lon, 6), round(lat, 6)], "k": k})
    places.sort(key=lambda p: p["n"].lower())
    (ROOT / "app" / "places.js").write_text(
        "// generated by scripts/16_refresh_pois.py — do not edit. SEARCH data only:\n"
        "// the map never renders these as pins (commercial pins = sponsor pipeline).\n"
        "const PLACES = " + json.dumps({"places": places}, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")
    return len(places)


def main():
    bbox = service_bbox()
    print(f"service area (from routes + {BUFFER_DEG}°): "
          f"lat {bbox[0]:.3f}..{bbox[2]:.3f}, lon {bbox[1]:.3f}..{bbox[3]:.3f}")

    pub = fetch_public_services(bbox)
    (ROOT / "poi" / "pois_osm.json").write_text(
        json.dumps(pub, ensure_ascii=False), encoding="utf-8")
    print(f"public services: {len(pub.get('elements', []))} raw elements")
    build_pois.main()

    com = fetch_places(bbox)
    (ROOT / "poi" / "places_osm.json").write_text(
        json.dumps(com, ensure_ascii=False), encoding="utf-8")
    n = build_places(com)
    print(f"places: {n} commercial destinations -> app/places.js")


if __name__ == "__main__":
    main()
