#!/usr/bin/env python3
"""Publish the rental listings into the app's Rentas feed.

Reads the harvested seed (resources/discovery/rentas_seed.jsonl) and emits
resources/map-data/rentas.js — the shape the /rentas/ page renders, in the same
spirit as events.js / discovery.js. Also (re)generates the per-type cover images
under resources/map-data/rentas-img/ so every listing shows exactly ONE photo,
served from OUR domain (Cloudflare Pages edge = our CDN) — never a hotlinked
portal image. Real per-listing photos come later from owner uploads / licensed
sources; until then each listing shows its property-type cover and links back to
the source listing (where the original photos live).

  python3 src/scripts/26_publish_rentas.py

Geo: every seed row is already gated to Tehuacán + service-area towns
(see business/discover-geo-scope.md). Deterministic: same seed => same output.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "resources" / "rentas" / "seed.jsonl"
OUT = ROOT / "resources" / "map-data" / "rentas.js"
IMGDIR = ROOT / "resources" / "map-data" / "rentas-img"

# property type -> (es label, en label, emoji, gradient a, gradient b)
KINDS = {
    "casa":         ("Casa", "House", "\U0001F3E1", "#fb923c", "#f97316"),
    "departamento": ("Departamento", "Apartment", "\U0001F3E2", "#38bdf8", "#0ea5e9"),
    "local":        ("Local comercial", "Retail space", "\U0001F3EA", "#a78bfa", "#8b5cf6"),
    "oficina":      ("Oficina", "Office", "\U0001F4BC", "#2dd4bf", "#14b8a6"),
    "edificio":     ("Edificio", "Building", "\U0001F3DB️", "#818cf8", "#6366f1"),
    "bodega":       ("Bodega", "Warehouse", "\U0001F4E6", "#94a3b8", "#64748b"),
    "nave":         ("Nave industrial", "Industrial", "\U0001F3ED", "#64748b", "#475569"),
    "terreno":      ("Terreno", "Land", "\U0001F3DE️", "#4ade80", "#22c55e"),
}
RESIDENTIAL = {"casa", "departamento"}


def cover_svg(kind, es, en, emoji, ca, cb):
    """A self-contained SVG cover — our own asset, one per property type."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" '
        f'viewBox="0 0 600 400" role="img" aria-label="{es}">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{ca}"/><stop offset="1" stop-color="{cb}"/>'
        f'</linearGradient></defs>'
        f'<rect width="600" height="400" fill="url(#g)"/>'
        f'<text x="300" y="196" font-size="150" text-anchor="middle" '
        f'dominant-baseline="central">{emoji}</text>'
        f'<text x="300" y="330" font-size="34" font-weight="700" text-anchor="middle" '
        f'fill="#ffffff" font-family="system-ui,-apple-system,sans-serif" '
        f'letter-spacing=".5">{es.upper()}</text>'
        f'<text x="580" y="380" font-size="16" text-anchor="end" fill="#ffffff" '
        f'opacity=".65" font-family="system-ui,sans-serif">mitehuacan.mx</text>'
        f'</svg>'
    )


def main():
    IMGDIR.mkdir(parents=True, exist_ok=True)
    for kind, (es, en, emoji, ca, cb) in KINDS.items():
        (IMGDIR / f"type-{kind}.svg").write_text(cover_svg(kind, es, en, emoji, ca, cb),
                                                 encoding="utf-8")

    rows = []
    for line in SEED.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))

    listings = []
    for r in rows:
        kind = r["kind"]
        es = KINDS.get(kind, KINDS["local"])[0]
        rec = {
            "t": f'{es} en {r["colonia"]}',
            "p": r["price"],
            "k": kind,
            "op": "renta",
            "m2": r.get("m2"),
            "col": r["colonia"],
            "town": "Tehuacán",
            "u": f'https://propiedades.com/inmuebles/{r["slug"]}',
            "src": "propiedades",
            "ph": f'/rentas-img/type-{kind}.svg',
            "x": 1,  # approximate location (colonia-level, no exact coords yet)
        }
        if kind in RESIDENTIAL:
            if r.get("beds") is not None:
                rec["br"] = r["beds"]
            if r.get("baths") is not None:
                rec["ba"] = r["baths"]
        # drop empty
        rec = {k: v for k, v in rec.items() if v is not None}
        listings.append(rec)

    # cheapest first is the useful default for renters
    listings.sort(key=lambda x: x["p"])
    payload = {"rentas": listings, "src": "propiedades.com", "town": "Tehuacán"}
    OUT.write_text("const RENTAS = " + json.dumps(payload, ensure_ascii=False) + ";\n",
                   encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(listings)} listings)")
    print(f"wrote {len(KINDS)} type covers -> {IMGDIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
