#!/usr/bin/env python3
"""Instagram discovery agent — its own setup, algorithm, and data.

SETUP: base Tehuacán terms + the category taxonomy as keyword queries (IG search
is keyword-only, no geo).
ALGORITHM: the web topsearch API with the signed-in session's cookies; keep
users/places whose name references Tehuacán. VERIFY re-checks the profile URL
for a live handle. DATA: resources/discovery/instagram.db
"""
from lib import DiscoveryAgent, norm
from gmaps import SUBCATS

IG_BASE = ["tehuacan", "tehuacán", "tehuacanpuebla"]


class InstagramAgent(DiscoveryAgent):
    NAME = "instagram"
    START_URL = "https://www.instagram.com/"
    LOGIN_URL = "https://www.instagram.com/accounts/login/"
    NEEDS_CONTEXT = True

    def build_plan(self):
        base = [{"q": t, "cat": "base", "sub": t, "label": f"base/{t}"} for t in IG_BASE]
        return base + [{"q": f"{sub} tehuacan", "cat": cat, "sub": sub, "label": f"{cat}/{sub}"}
                       for cat, sub in SUBCATS]

    def scrape_item(self, page, context, it):
        r = context.request.get(
            "https://www.instagram.com/api/v1/web/search/topsearch/?context=blended&query=" + it["q"],
            headers={"x-ig-app-id": "936619743392459", "x-requested-with": "XMLHttpRequest",
                     "referer": "https://www.instagram.com/"})
        if r.status in (401, 403, 429):
            self.attention(page, f"instagram API {r.status} (session expired / rate-limited)")
        try:
            data = r.json()
        except Exception:  # noqa: BLE001
            self.attention(page, "instagram API returned non-JSON (login wall)")
        out = []
        for u in data.get("users", []):
            usr = u.get("user", {})
            handle, full = usr.get("username", ""), usr.get("full_name", "")
            if handle and "tehuacan" in norm(handle) + norm(full):
                out.append({"key": "ig:" + handle, "name": (full or handle)[:80], "source": "instagram",
                            "category": it["cat"], "subcat": it["sub"], "handle": handle,
                            "url": f"https://instagram.com/{handle}", "lat": None, "lon": None})
        for pl in data.get("places", []):
            loc = pl.get("place", {}).get("location", {})
            nm = loc.get("name", "")
            if nm and ("tehuacan" in norm(nm) or "tehuacan" in norm(pl.get("place", {}).get("subtitle", ""))):
                out.append({"key": f"igp:{norm(nm)}", "name": nm[:80], "source": "instagram",
                            "category": it["cat"], "subcat": it["sub"], "handle": None, "url": None,
                            "lat": loc.get("lat"), "lon": loc.get("lng")})
        return out

    def verify_record(self, page, rec):
        handle = rec["handle"]
        if not handle:
            return True, ""
        try:
            resp = page.goto(f"https://www.instagram.com/{handle}/", timeout=45000)
            page.wait_for_timeout(2500)
        except Exception:  # noqa: BLE001
            return True, ""
        if (w := self.walled(page)):
            self.attention(page, w)
        if resp and resp.status == 404:
            return False, "instagram: handle 404"
        try:
            body = page.inner_text("body", timeout=4000).lower()
        except Exception:  # noqa: BLE001
            return True, ""
        if "sorry, this page isn't available" in body or "la página no está disponible" in body:
            return False, "instagram: profile gone"
        return True, ""
