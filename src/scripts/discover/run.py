#!/usr/bin/env python3
"""CLI for the discovery agents. The local runner (agents.py) calls this.

  python3 src/scripts/discover/run.py <agent> [MODE] [OPTS]

  agent   google | instagram | facebook
  MODE    (default) discover next batch into the store
          --verify  re-check existing records, mark the dead ones (pruning)
          --login   open a real Chrome to sign in
          --stats   print the store's lifecycle counts and exit
  OPTS    --batch N   items this run (default per agent)
          --all       discover: sweep the whole plan (ignore the cursor)
          --profile NAME   use a named account profile

Idempotent: discover upserts by stable key (no duplicates); verify re-marking a
dead record is a no-op; --all / re-running a fixed slice converges to the same
store state.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # import sibling modules

from gmaps import GoogleAgent          # noqa: E402
from instagram import InstagramAgent    # noqa: E402
from facebook import FacebookAgent      # noqa: E402
from fb_events import FacebookEventsAgent  # noqa: E402
from gov_events import GovEventsAgent      # noqa: E402

AGENTS = {"google": GoogleAgent, "instagram": InstagramAgent, "facebook": FacebookAgent,
          "fb_events": FacebookEventsAgent, "gov_events": GovEventsAgent}


def opt(name, default=None):
    if name in sys.argv:
        j = sys.argv.index(name)
        return sys.argv[j + 1] if j + 1 < len(sys.argv) else default
    return default


def main():
    names = [a for a in sys.argv[1:] if a in AGENTS]
    if not names:
        print("usage: run.py google|instagram|facebook [--verify|--login|--stats] "
              "[--batch N] [--all] [--profile NAME]")
        sys.exit(2)

    profile = re.sub(r"[^a-zA-Z0-9_-]", "", opt("--profile", "default") or "default") or "default"
    batch = None
    if opt("--batch"):
        try:
            batch = max(1, int(opt("--batch")))
        except ValueError:
            pass

    agent = AGENTS[names[0]](profile=profile, batch=batch)
    if "--stats" in sys.argv:
        print(f"{agent.NAME}: {agent.store.stats()}  cursor={agent.store.get_cursor()}")
        return
    if "--login" in sys.argv:
        agent.login()
    elif "--verify" in sys.argv:
        agent.verify()
    else:
        agent.discover(all_="--all" in sys.argv)


if __name__ == "__main__":
    main()
