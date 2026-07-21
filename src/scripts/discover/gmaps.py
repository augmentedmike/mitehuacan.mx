#!/usr/bin/env python3
"""Google Maps discovery agent — its own setup, algorithm, and data.

SETUP: geo center of Tehuacán + concentric rings, and a category/subcategory
taxonomy. The plan is space×category (point-major: every category at centro
first, then ring by ring outward).
ALGORITHM: center a Maps search on each point, paginate the results feed fully,
extract name + coords + place id. VERIFY re-opens a place and reads whether
Google marks it permanently/temporarily closed.
DATA: resources/discovery/google.db
"""
import math
import re

from lib import DiscoveryAgent, norm, SUBCATS   # SUBCATS from the shared taxonomy.json

CENTER = (18.4620, -97.3960)


def _points():
    pts = [("centro", CENTER)]
    compass = {"N": (1, 0), "NE": (0.7, 0.7), "E": (0, 1), "SE": (-0.7, 0.7),
               "S": (-1, 0), "SW": (-0.7, -0.7), "W": (0, -1), "NW": (0.7, -0.7)}
    latc = math.cos(math.radians(CENTER[0]))
    for r_km, ring in [(1.5, "r1"), (3.0, "r2"), (5.0, "r3")]:
        d = r_km / 111.0
        for name, (dy, dx) in compass.items():
            pts.append((f"{ring}-{name}", (round(CENTER[0] + dy * d, 5), round(CENTER[1] + dx * d / latc, 5))))
    return pts


POINTS = _points()


class GoogleAgent(DiscoveryAgent):
    NAME = "google"
    START_URL = "https://www.google.com/maps"
    LOGIN_URL = "https://accounts.google.com/"
    SESSION_COOKIE = "SID"

    def build_plan(self):
        # CATEGORY-major (points inner): each run sweeps a category across the
        # WHOLE city (all rings), not all categories at one point. At a fixed
        # map center Google returns the same nearby places for any category, so
        # point-major overlaps heavily; spreading geography per run maximizes
        # new records.
        return [{"where": lbl, "pt": pt, "cat": cat, "sub": sub,
                 "label": f"{cat}/{sub} · {lbl}"}
                for cat, sub in SUBCATS for lbl, pt in POINTS]

    def _paginate(self, page):
        feed = page.query_selector('div[role="feed"]')
        if not feed:
            return
        prev = 0
        for _ in range(12):
            page.evaluate("el => el.scrollTo(0, el.scrollHeight)", feed)
            page.wait_for_timeout(1100)
            n = len(page.query_selector_all('div[role="feed"] a[href*="/maps/place/"]'))
            if n == prev:
                break
            prev = n

    @staticmethod
    def _key(name, href):
        m = re.search(r"!1s(0x[0-9a-f]+:0x[0-9a-f]+)", href)     # google's stable cid
        if m:
            return "g:" + m.group(1)
        c = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", href)
        return f"n:{norm(name)}:" + (f"{float(c.group(1)):.4f},{float(c.group(2)):.4f}" if c else "?")

    def scrape_item(self, page, context, it):
        lat, lng = it["pt"]
        # z16 (~1.5km view) so each ring point returns its OWN neighborhood — at
        # z14 every point saw the whole city and results overlapped completely.
        url = f"https://www.google.com/maps/search/{it['sub'].replace(' ', '+')}/@{lat},{lng},16z"
        page.goto(url, timeout=60000)
        page.wait_for_timeout(3200)
        if (w := self.walled(page)):
            self.attention(page, w)
        self._paginate(page)
        out = []
        for a in page.query_selector_all('div[role="feed"] a[aria-label][href*="/maps/place/"]'):
            name = (a.get_attribute("aria-label") or "").strip()
            href = a.get_attribute("href") or ""
            if not name:
                continue
            c = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", href)
            out.append({"key": self._key(name, href), "name": name[:80], "source": "google",
                        "cat": it["cat"], "sub": it["sub"], "category": it["cat"], "subcat": it["sub"],
                        "where": it["where"], "url": href.split("?")[0][:200],
                        "lat": float(c.group(1)) if c else None, "lon": float(c.group(2)) if c else None})
        return out

    def verify_record(self, page, rec):
        url = rec["url"]
        if not url:
            return True, ""                       # nothing to check against; leave live
        try:
            page.goto(url, timeout=45000)
            page.wait_for_timeout(2500)
        except Exception as e:  # noqa: BLE001
            return True, ""                       # transient nav issue — don't kill on it
        if (w := self.walled(page)):
            self.attention(page, w)
        try:
            body = page.inner_text("body", timeout=4000).lower()
        except Exception:  # noqa: BLE001
            return True, ""
        if "permanentemente cerrado" in body or "permanently closed" in body:
            return False, "google: permanently closed"
        # place page that no longer resolves to a business
        if "no se encontró" in body or ("google maps" == page.title().strip().lower() and "/place/" not in page.url):
            return False, "google: place no longer found"
        return True, ""
