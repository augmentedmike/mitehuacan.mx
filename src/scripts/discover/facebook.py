#!/usr/bin/env python3
"""Facebook discovery agent — its own setup, algorithm, and data.

SETUP: category taxonomy as "<subcat> Tehuacán" place-search queries.
ALGORITHM: Facebook places search with the signed-in session; keep page/profile
links, drop UI chrome. VERIFY re-opens the page URL and checks it still resolves.
DATA: resources/discovery/facebook.db
"""
import re

from lib import DiscoveryAgent, norm, SUBCATS   # shared taxonomy.json

# a real business page link: a vanity URL or profile.php?id=
_BIZ = re.compile(r"facebook\.com/(profile\.php\?id=\d+|[A-Za-z0-9.]{3,})/?(\?|$)")
# facebook chrome / nav / non-business links to ignore
_CHROME = re.compile(r"/(notifications|login|login_alerts|marketplace|groups|search|watch|gaming|events|"
                     r"reel|stories|messages|friends|help|policies|privacy|settings|bookmarks|ads|business)/"
                     r"|modal=|__rsid|l\.php|/photo|/videos", re.I)
_JUNK = re.compile(r"^(me gusta|like|follow|seguir|compartir|share|ver|see all|pages|reels|unread|"
                   r"facebook|iniciar|log in|más|more)\b", re.I)


class FacebookAgent(DiscoveryAgent):
    NAME = "facebook"
    START_URL = "https://www.facebook.com/"
    LOGIN_URL = "https://www.facebook.com/login/"
    SESSION_COOKIE = "c_user"

    def build_plan(self):
        # /search/pages/ returns business Pages specifically (cleaner than places)
        return [{"q": f"{sub} Tehuacán", "cat": cat, "sub": sub, "label": f"{cat}/{sub}"}
                for cat, sub in SUBCATS]

    @staticmethod
    def _key(href):
        m = re.search(r"facebook\.com/(?:profile\.php\?id=(\d+)|([A-Za-z0-9.]+))", href)
        return "fb:" + (m.group(1) or m.group(2)) if m else None

    def scrape_item(self, page, context, it):
        url = "https://www.facebook.com/search/pages/?q=" + it["q"].replace(" ", "%20")
        page.goto(url, timeout=60000)
        page.wait_for_timeout(6000)                 # let the GraphQL results render
        if (w := self.walled(page)):
            self.attention(page, w)
        for _ in range(4):
            page.mouse.wheel(0, 2200)
            page.wait_for_timeout(1500)
        out, seen = [], set()
        for a in page.query_selector_all('div[role="main"] a[href*="facebook.com/"]'):
            href = a.get_attribute("href") or ""
            if not href.startswith("http") or _CHROME.search(href) or not _BIZ.search(href):
                continue
            name = (a.inner_text() or "").strip().split("\n")[0]
            if len(name) < 3 or _JUNK.match(name):
                continue
            key = self._key(href)
            if not key or key in seen:
                continue
            seen.add(key)
            out.append({"key": key, "name": name[:80], "source": "facebook",
                        "category": it["cat"], "subcat": it["sub"], "handle": None,
                        "url": href.split("?")[0][:200] if "profile.php" not in href else href[:200],
                        "lat": None, "lon": None})
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
