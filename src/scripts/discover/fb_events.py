#!/usr/bin/env python3
"""Facebook Events discovery — fiestas & events in the zone.

Reuses the same framework as the business agents (session, lifecycle store,
cursor, logging) but collects EVENTS: searches Facebook events for each
service-area town and records id/title/date/location. Data: fb_events.db.

An event is stored as a record: name=title, subcat=date, where=town,
category="evento", url=event page. VERIFY drops events whose page no longer
resolves (cancelled/removed); past events stay as history.
"""
import re

from lib import DiscoveryAgent
from gmaps import TOWNS


class FacebookEventsAgent(DiscoveryAgent):
    NAME = "fb_events"
    START_URL = "https://www.facebook.com/events/"
    LOGIN_URL = "https://www.facebook.com/login/"
    SESSION_COOKIE = "c_user"
    DEFAULT_BATCH = 8

    def build_plan(self):
        # one search per town — events are place-anchored
        return [{"q": t["name"], "town": t["name"], "label": f"events/{t['name']}"} for t in TOWNS]

    def scrape_item(self, page, context, it):
        url = "https://www.facebook.com/events/search/?q=" + it["q"].replace(" ", "%20")
        page.goto(url, timeout=60000)
        page.wait_for_timeout(6000)
        if (w := self.walled(page)):
            self.attention(page, w)
        for _ in range(4):
            page.mouse.wheel(0, 2200)
            page.wait_for_timeout(1500)
        out, seen = [], set()
        for a in page.query_selector_all('a[href*="/events/"]'):
            href = a.get_attribute("href") or ""
            m = re.search(r"/events/(\d{6,})", href)
            if not m or m.group(1) in seen:
                continue
            eid = m.group(1)
            # the card = nearest ancestor holding date + title + location lines
            card = a.evaluate_handle(
                "el => el.closest('div[role=\"article\"]') || el.closest('li') || el.parentElement.parentElement")
            try:
                txt = card.as_element().inner_text().strip()
            except Exception:  # noqa: BLE001
                txt = (a.inner_text() or "").strip()
            lines = [ln.strip() for ln in txt.split("\n") if ln.strip()]
            if not lines:
                continue
            # line 0 is usually the date; the title is the first longer non-date line
            date = lines[0]
            title = next((ln for ln in lines[1:] if len(ln) > 4 and not re.match(r"^\d+ (going|interested|personas)", ln, re.I)), lines[0])
            loc = next((ln for ln in lines if any(t["name"].split()[0].lower() in ln.lower() for t in TOWNS)), it["town"])
            seen.add(eid)
            out.append({"key": "fbev:" + eid, "name": title[:90], "source": "fb_events",
                        "category": "evento", "subcat": date[:40], "where": loc[:60],
                        "handle": None, "url": f"https://www.facebook.com/events/{eid}/",
                        "lat": None, "lon": None})
        return out

    def verify_record(self, page, rec):
        try:
            resp = page.goto(rec["url"], timeout=45000)
            page.wait_for_timeout(2500)
        except Exception:  # noqa: BLE001
            return True, ""
        if (w := self.walled(page)):
            self.attention(page, w)
        if resp and resp.status == 404:
            return False, "fb event: 404"
        try:
            body = page.inner_text("body", timeout=4000).lower()
        except Exception:  # noqa: BLE001
            return True, ""
        if "this content isn't available" in body or "este contenido no está disponible" in body:
            return False, "fb event: removed"
        return True, ""
