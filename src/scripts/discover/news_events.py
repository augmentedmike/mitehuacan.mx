#!/usr/bin/env python3
"""Google News discovery — local event coverage via the News RSS search feed.

No login and no browser rendering: it hits news.google.com's RSS *search* endpoint
per service-area town (clean XML, no consent wall), keeps articles whose headline
names an event, and lets the publisher parse a date out of the headline. Dates
pulled from news are soft, so every record is handle='approx' -> the app flags it
"por confirmar". Articles with no parseable date simply never publish. Data:
news_events.db.
"""
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

from lib import DiscoveryAgent
from gmaps import TOWNS

EVENT_TERMS = ("feria", "fiesta", "festival", "concierto", "evento", "expo",
               "carnaval", "verbena", "jaripeo", "torneo", "desfile", "kermes",
               "romería", "peregrinación", "mercado", "exposición")

# crime/obituary/politics headlines often collide with an event term ("... en el
# mercado", "feria de empleo cancelada"); drop the obvious non-events.
NEG_TERMS = ("falleci", "muere", "murió", "asesin", "homicid", "detien", "detenid",
             "robo", "asalt", "balac", "accidente", "choque", "cancel", "suspend",
             "narco", "violencia", "cadáver", "cuerpo", "desaparec")


class GoogleNewsEventsAgent(DiscoveryAgent):
    NAME = "news_events"
    SESSION_COOKIE = ""          # public RSS — no login
    DEFAULT_BATCH = 20
    CAP = 25                     # articles kept per town/run

    def build_plan(self):
        terms = " OR ".join(EVENT_TERMS)
        return [{"q": f'"{t["name"]}" ({terms})', "town": t["name"], "label": f"news/{t['name']}"}
                for t in TOWNS]

    def scrape_item(self, page, context, it):
        url = ("https://news.google.com/rss/search?q=" + quote(it["q"]) +
               "&hl=es-419&gl=MX&ceid=MX:es")
        try:
            r = context.request.get(url, timeout=45000)
        except Exception:  # noqa: BLE001
            return []
        if r.status != 200:
            return []
        try:
            root = ET.fromstring(r.text())
        except Exception:  # noqa: BLE001
            return []
        out = []
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            if not title or not link:
                continue
            low = title.lower()
            if not any(term in low for term in EVENT_TERMS):
                continue
            if any(neg in low for neg in NEG_TERMS):
                continue
            key = "news:" + re.sub(r"\W+", "", link)[-40:]
            out.append({"key": key, "name": title[:90], "source": self.NAME,
                        "category": "evento",
                        "subcat": title[:120],   # publisher parses a Spanish date out of it
                        "where": it["town"], "handle": "approx",
                        "url": link, "lat": None, "lon": None})
            if len(out) >= self.CAP:
                break
        return out

    def verify_record(self, page, rec):
        # Google News links are stable redirect URLs; past articles drop at publish.
        return True, ""
