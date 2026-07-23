#!/usr/bin/env python3
"""Government / traditional-calendar events — fiestas patronales in the zone.

Unlike the social agents, this one needs no login and no browser: its source is
fiestas.json — patronal feasts DERIVED from the saint named in each town (a fact
of the liturgical calendar, not invented). Each enters the same lifecycle store
as 'candidate' with handle='approx' so the publisher/app flags it "por confirmar"
until a local date is verified. Data: gov_events.db.

DISCOVER re-materialises the seed (idempotent upserts) and prunes any record
whose key left the seed. VERIFY just re-syncs — fiestas don't 404.
"""
import json
import re
from pathlib import Path

from lib import DiscoveryAgent, now_iso
from events_common import TOWN_CENTER, DEFAULT_CENTER

HERE = Path(__file__).resolve().parent
_MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
           "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


class GovEventsAgent(DiscoveryAgent):
    NAME = "gov_events"
    SESSION_COOKIE = ""          # no login — public/derived data
    DEFAULT_BATCH = 100

    def _seed(self):
        return json.loads((HERE / "fiestas.json").read_text(encoding="utf-8")).get("fiestas", [])

    def build_plan(self):
        return self._seed()

    # seed-driven: no page needed, so we own the discover loop
    def discover(self, all_=False):
        seed = self._seed()
        now = now_iso()
        keys, new, existed = set(), 0, 0
        for f in seed:
            town = f["town"]
            lon, lat = TOWN_CENTER.get(town, DEFAULT_CENTER)
            key = "gov:" + _slug(f"{town}-{f['name']}")
            keys.add(key)
            rec = {"key": key, "name": f["name"][:90], "source": self.NAME,
                   "category": "evento", "subcat": f"{f['day']} de {_MONTHS[f['month'] - 1]}",
                   "where": town, "handle": "approx" if f.get("approx") else None,
                   "url": f.get("url"), "lat": lat, "lon": lon}
            if self.store.upsert(rec, now):
                new += 1
            else:
                existed += 1
        # prune fiestas dropped from the seed
        pruned = 0
        for r in self.store.db.execute(
                "SELECT key FROM records WHERE status IN ('candidate','approved')").fetchall():
            if r["key"] not in keys:
                self.store.mark(r["key"], "dead", "removed from fiestas.json seed", now)
                pruned += 1
        self.store.commit()
        q = self.store.export_queue()
        self.log(f"gov_events: {len(seed)} fiestas in seed — {new} new, {existed} re-seen, "
                 f"{pruned} pruned; queue now {q}; store {self.store.stats()}")

    def verify(self):
        # fiestas are permanent; re-sync the seed instead of hitting the network
        self.log("gov_events verify: re-syncing seed (fiestas don't expire)")
        self.discover()

    # never called (discover/verify overridden) but keep the contract explicit
    def scrape_item(self, page, context, item):
        return []

    def verify_record(self, page, rec):
        return True, ""
