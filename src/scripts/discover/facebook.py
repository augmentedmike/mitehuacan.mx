#!/usr/bin/env python3
"""Facebook discovery agent — its own setup, algorithm, and data.

SETUP: category taxonomy as "<subcat> Tehuacán" place-search queries.
ALGORITHM: Facebook places search with the signed-in session; keep page/profile
links, drop UI chrome. VERIFY re-opens the page URL and checks it still resolves.
DATA: resources/discovery/facebook.db
"""
import re

from lib import DiscoveryAgent, norm
from gmaps import SUBCATS

_JUNK = re.compile(r"^(me gusta|like|follow|seguir|compartir|share|ver|see|facebook|iniciar|log in)\b", re.I)


class FacebookAgent(DiscoveryAgent):
    NAME = "facebook"
    START_URL = "https://www.facebook.com/"
    LOGIN_URL = "https://www.facebook.com/login/"

    def build_plan(self):
        return [{"q": f"{sub} Tehuacán", "cat": cat, "sub": sub, "label": f"{cat}/{sub}"}
                for cat, sub in SUBCATS]

    def scrape_item(self, page, context, it):
        url = "https://www.facebook.com/search/places/?q=" + it["q"].replace(" ", "%20")
        page.goto(url, timeout=60000)
        page.wait_for_timeout(4500)
        if (w := self.walled(page)):
            self.attention(page, w)
        for _ in range(3):
            page.mouse.wheel(0, 2500)
            page.wait_for_timeout(1400)
        out = []
        for a in page.query_selector_all('div[role="main"] a[role="link"]'):
            name = (a.inner_text() or "").strip().split("\n")[0]
            href = a.get_attribute("href") or ""
            if len(name) > 3 and not _JUNK.match(name) and \
               ("/pages/" in href or re.search(r"facebook\.com/[^/?]+/?(\?|$)", href)):
                clean = href.split("?")[0]
                out.append({"key": "fb:" + (re.sub(r"https?://[^/]+/", "", clean).strip("/") or norm(name)),
                            "name": name[:80], "source": "facebook", "category": it["cat"], "subcat": it["sub"],
                            "handle": None, "url": clean[:200], "lat": None, "lon": None})
        return out

    def verify_record(self, page, rec):
        url = rec["url"]
        if not url:
            return True, ""
        try:
            resp = page.goto(url, timeout=45000)
            page.wait_for_timeout(2500)
        except Exception:  # noqa: BLE001
            return True, ""
        if (w := self.walled(page)):
            self.attention(page, w)
        if resp and resp.status == 404:
            return False, "facebook: page 404"
        try:
            body = page.inner_text("body", timeout=4000).lower()
        except Exception:  # noqa: BLE001
            return True, ""
        if "este contenido no está disponible" in body or "content isn't available" in body or \
           "esta página no está disponible" in body:
            return False, "facebook: page gone"
        return True, ""
