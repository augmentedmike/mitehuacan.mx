#!/usr/bin/env python3
"""Facebook Pages events — scrape configured official pages' upcoming events.

Same session + enrichment as fb_events, but instead of the global events search
it visits each page listed in fb_pages.json and reads that page's own events tab.
This catches municipal / Casa de Cultura / promoter pages that announce events
that never surface in Facebook's event search. Data: fbpages_events.db.

Fill fb_pages.json with the REAL page handles before running — the seeds there
are unverified placeholders.
"""
import json
from pathlib import Path

from fb_events import FacebookEventsAgent

HERE = Path(__file__).resolve().parent


class FacebookPagesEventsAgent(FacebookEventsAgent):
    NAME = "fbpages_events"

    def build_plan(self):
        cfg = json.loads((HERE / "fb_pages.json").read_text(encoding="utf-8"))
        return [{"page": p["handle"], "town": p.get("town", "Tehuacán"),
                 "label": f"page/{p['handle']}"}
                for p in cfg.get("pages", []) if p.get("handle")]

    def scrape_item(self, page, context, it):
        # a page's events live under /upcoming_events (fall back to /events)
        for path in ("upcoming_events", "events"):
            try:
                page.goto(f"https://www.facebook.com/{it['page']}/{path}", timeout=60000)
                page.wait_for_timeout(5000)
                break
            except Exception:  # noqa: BLE001
                continue
        if (w := self.walled(page)):
            self.attention(page, w)
        out = self._collect_grid(page, it["town"])   # inherited: parses the event cards
        return self._enrich(page, out)               # inherited: deep-scrapes each page
