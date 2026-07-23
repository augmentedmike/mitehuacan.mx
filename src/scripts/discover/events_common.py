#!/usr/bin/env python3
"""Shared normalization for the EVENT agents (fb_events, gov_events, …).

The event agents collect raw records into their own <agent>.db (same lifecycle
store as the business agents). What makes an event calendar-usable is three
normalizations, kept here so every source is treated identically:

  * parse_date_es  — a Spanish/relative date string -> an ISO date (with year
    inferred to the next upcoming occurrence when the source omits it, as
    Facebook does). Recurring/annual dates (fiestas) roll to their next date.
  * geocode_event  — venue/town text -> [lon, lat], falling back to the town
    centre (from towns.json) when the venue isn't a resolvable intersection.
  * categorize     — title -> one of a small set of Spanish calendar buckets.

No fabrication: this file only reshapes strings the agents actually collected.
"""
import json
import re
import unicodedata
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOWNS = json.loads((HERE / "towns.json").read_text(encoding="utf-8"))
TOWN_CENTER = {t["name"]: (t["lon"], t["lat"]) for t in TOWNS}
_TEHUACAN = next((t for t in TOWNS if "tehuac" in t["name"].lower()), TOWNS[0])
DEFAULT_CENTER = (_TEHUACAN["lon"], _TEHUACAN["lat"])

MONTHS = {m[:3]: i for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
     "agosto", "septiembre", "octubre", "noviembre", "diciembre"], start=1)}

_CATS = [
    ("religioso", ("fiesta patronal", "patronal", "san ", "santa ", "santo ", "virgen",
                   "señor", "procesion", "misa", "parroquia", "guadalup", "peregrinac")),
    ("feria",     ("feria", "expo", "kermes", "kermés", "tianguis", "muestra")),
    ("cultural",  ("cultura", "concierto", "musica", "música", "danza", "teatro",
                   "exposicion", "festival", "arte", "cine", "libro")),
    ("deportivo", ("carrera", "torneo", "futbol", "fútbol", "maraton", "maratón",
                   "deportiv", "ciclism", "box", "lucha")),
    ("civico",    ("desfile", "aniversario", "independencia", "grito", "civic",
                   "cívic", "informe", "revolucion", "revolución")),
]


def _strip(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def parse_date_es(text, ref=None):
    """'Sáb, 2 de may.' / '24 de junio de 2026' / '15 sep' -> datetime.date.

    Year rules: an explicit 20xx wins. Otherwise pick the occurrence of (month,
    day) nearest going forward from ref-45d — Facebook shows upcoming events with
    no year, and annual fiestas want their next date. Returns None if unparseable.
    """
    ref = ref or date.today()
    t = _strip(text)
    m = re.search(r"(\d{1,2})\s+(?:de\s+)?([a-z]{3,})", t)
    if not m:
        return None
    day = int(m.group(1))
    mon = MONTHS.get(m.group(2)[:3])
    if not mon or not (1 <= day <= 31):
        return None
    y = re.search(r"\b(20\d{2})\b", t)
    if y:
        try:
            return date(int(y.group(1)), mon, day)
        except ValueError:
            return None
    best = None
    for yr in (ref.year - 1, ref.year, ref.year + 1):
        try:
            d = date(yr, mon, day)
        except ValueError:
            continue
        if d >= ref - timedelta(days=45) and (best is None or d < best):
            best = d
    return best


def parse_time_es(text):
    """'a las 12:00' / '19:30 h' -> 'HH:MM' or ''. Ignores am/pm noise safely."""
    m = re.search(r"(\d{1,2}):(\d{2})", text)
    if not m:
        return ""
    h, mn = int(m.group(1)), int(m.group(2))
    low = _strip(text)
    if "p. m." in low or "pm" in low.replace(" ", ""):
        if h < 12:
            h += 12
    return f"{h:02d}:{mn:02d}"


def categorize(title):
    t = _strip(title)
    for cat, keys in _CATS:
        if any(k in t for k in keys):
            return cat
    return "otro"


def town_of(text, fallback="Tehuacán"):
    """Which service-area town does this venue/where text name?"""
    t = _strip(text or "")
    for name in TOWN_CENTER:
        if _strip(name.split()[-1]) in t or _strip(name) in t:
            return name
    return fallback


def geocode_event(venue, town, cruces=None):
    """[lon, lat] for an event. Try a street-intersection match (if cruces given
    and the venue reads like one), else the town centre, else Tehuacán centre."""
    if cruces and venue and (" esq" in _strip(venue) or " y " in _strip(venue)):
        hit = _match_cruce(venue, cruces)
        if hit:
            return [round(hit[0], 6), round(hit[1], 6)]
    c = TOWN_CENTER.get(town) or TOWN_CENTER.get(town_of(venue or town)) or DEFAULT_CENTER
    return [round(c[0], 6), round(c[1], 6)]


def load_cruces():
    """OSM intersections from calles.js (same source resolve.py uses)."""
    f = HERE.parents[2] / "resources" / "map-data" / "calles.js"
    if not f.exists():
        return []
    t = f.read_text(encoding="utf-8")
    try:
        data = json.loads(t[t.index("{"):t.rstrip().rstrip(";").rindex("}") + 1])
    except ValueError:
        return []
    return [(_strip(c["n"]), c["c"]) for c in data.get("cruces", [])]


def _match_cruce(venue, cruces):
    toks = [w for w in re.split(r"[^a-z0-9]+", _strip(venue)) if len(w) > 3]
    best, score = None, 0
    for name, c in cruces:
        s = sum(1 for w in toks if w in name)
        if s > score:
            best, score = c, s
    return best if score >= 2 else None
