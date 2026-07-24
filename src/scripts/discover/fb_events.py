#!/usr/bin/env python3
"""Facebook Events discovery — fiestas & events in the zone.

Reuses the same framework as the business agents (session, lifecycle store,
cursor, logging) but collects EVENTS: searches Facebook events for each
service-area town and records id/title/date/location. Data: fb_events.db.

An event is stored as a record: name=title, subcat=date, where=town,
category="evento", url=event page. After collecting a town's events from the
search grid, DISCOVER deep-scrapes each event page for the richer detail the
card doesn't carry — full address, description, exact time, host, cover image —
so the /eventos/ panel can show it. VERIFY drops events whose page no longer
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
    DETAIL_CAP = 15          # deep-scrape at most this many event pages per town/run

    def build_plan(self):
        # one search per town — events are place-anchored
        return [{"q": t["name"], "town": t["name"], "label": f"events/{t['name']}"} for t in TOWNS]

    def scrape_item(self, page, context, it):
        url = "https://www.facebook.com/events/search/?q=" + it["q"].replace(" ", "%20")
        page.goto(url, timeout=60000)
        page.wait_for_timeout(6000)
        if (w := self.walled(page)):
            self.attention(page, w)
        out = self._collect_grid(page, it["town"])
        return self._enrich(page, out)

    def _collect_grid(self, page, default_town):
        """Scroll the current events grid (search results OR a page's events tab)
        and pull one record per event card. Shared by the search agent and the
        pages agent — both land the same fbev:<id> key so they dedupe at publish."""
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
            loc = next((ln for ln in lines if any(t["name"].split()[0].lower() in ln.lower() for t in TOWNS)), default_town)
            seen.add(eid)
            out.append({"key": "fbev:" + eid, "name": title[:90], "source": self.NAME,
                        "category": "evento", "subcat": date[:40], "where": loc[:60],
                        "handle": None, "url": f"https://www.facebook.com/events/{eid}/",
                        "lat": None, "lon": None})
        return out

    def _enrich(self, page, out):
        """Deep-scrape each event page for detail the card doesn't carry."""
        for rec in out[:self.DETAIL_CAP]:
            rec.update(self._details(page, rec["url"]))
            page.wait_for_timeout(700)
        return out

    def _details(self, page, url):
        """Open one event page and pull address, description, exact time, host and
        cover image. Best-effort: Facebook's markup is obfuscated, so we lean on the
        stable og: meta tags plus light text heuristics. Returns only found fields."""
        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)
        except Exception:  # noqa: BLE001
            return {}
        if self.walled(page):
            return {}                      # logged out for this page — skip, don't kill the run
        d = {}
        # og:description is a reliable fallback blurb. (og:image is a lookaside
        # crawler URL that won't hotlink onto our page, so we don't use it.)
        try:
            v = page.get_attribute('meta[property="og:description"]', "content")
            if v:
                d["_ogdesc"] = v
        except Exception:  # noqa: BLE001
            pass
        try:
            body = page.inner_text("body", timeout=4000)
        except Exception:  # noqa: BLE001
            body = ""
        lines = [ln.strip() for ln in body.split("\n") if ln.strip()]
        for ln in lines:                    # host: "Event by X" / "Evento de X"
            m = re.match(r"(?:Event by|Evento de|Organizado por|Hosted by)\s+(.+)", ln, re.I)
            if m:
                d["host"] = m.group(1)[:80]
                break
        for ln in lines:                    # exact time: a line carrying HH:MM
            if re.search(r"\b\d{1,2}:\d{2}\b", ln) and len(ln) < 70:
                d["time_"] = ln
                break
        for ln in lines:                    # address: street/place-looking line
            if re.search(r"\b(calle|av\.?|avenida|carr\.?|carretera|blvd|boulevard|"
                         r"colonia|barrio|privada|prol\.?|#|no\.)\b", ln, re.I) and 6 < len(ln) < 140:
                d["addr"] = ln
                break
        paras = [ln for ln in lines if len(ln) > 60]     # description: longest paragraph
        if paras:
            d["descr"] = max(paras, key=len)[:600]
        elif d.get("_ogdesc"):
            d["descr"] = d["_ogdesc"][:600]
        d.pop("_ogdesc", None)
        return {k: v[:600] if isinstance(v, str) else v for k, v in d.items() if v}

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
