#!/usr/bin/env python3
"""One-shot: import the old append-only resources/discovery/<agent>.jsonl into
the new per-agent SQLite lifecycle store, then rewrite the jsonl as the store's
export. Safe to re-run — keyed upserts mean no duplicates."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import DISC, Store, now_iso, norm  # noqa: E402
from gmaps import GoogleAgent  # noqa: E402


def key_for(agent, c):
    if agent == "instagram":
        return "ig:" + c["handle"] if c.get("handle") else f"igp:{norm(c['name'])}"
    if agent == "facebook":
        return "fb:" + norm(c["name"])
    # google: prefer the stable cid embedded in the url
    return GoogleAgent._key(c["name"], c.get("url", ""))


def main():
    for agent in ("google", "instagram", "facebook"):
        f = DISC / f"{agent}.jsonl"
        if not f.exists():
            continue
        store = Store(agent)
        now = now_iso()
        n = new = 0
        for line in f.read_text().splitlines():
            try:
                c = json.loads(line)
            except ValueError:
                continue
            n += 1
            rec = {"key": key_for(agent, c), "name": c["name"], "source": c.get("source", agent),
                   "category": c.get("cat") or c.get("category"), "subcat": c.get("sub") or c.get("subcat"),
                   "where": c.get("where"), "url": c.get("url"), "handle": c.get("handle"),
                   "lat": c.get("lat"), "lon": c.get("lon")}
            if store.upsert(rec, now):
                new += 1
        store.commit()
        q = store.export_queue()
        print(f"{agent}: imported {n} jsonl rows -> {new} new records; store {store.stats()}; queue rewritten to {q}")


if __name__ == "__main__":
    main()
