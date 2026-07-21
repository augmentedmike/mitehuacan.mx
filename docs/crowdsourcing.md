# Crowdsourcing + Gamification — Design

The vision: 99%+ mobile, no login/email, **identity tied to the device**. People
earn **points** for contributing — adding POIs, recording combi routes, referrals
— Pokémon-GO-style. This doc is the architecture and the honest constraints.

## The hard constraint you need to know first

**A web app cannot record GPS in the background.** When the phone locks or the
user switches to another app, iOS and Android **suspend the page** — `watchPosition`
stops delivering fixes and timers freeze. Only a *native* app can track in the
background. So:

- **Answer to "can they change screens and still record?" → No, not reliably.**
  The recorder must keep the **screen on** (wake lock) and stay in the
  **foreground**. If they switch apps or the screen sleeps, recording pauses and
  resumes only when they come back — leaving gaps.
- This is exactly why **your instinct to aggregate partial reports is correct.**
  No single rider will capture a whole route (their trip ends, phone sleeps, they
  give up). We collect many **partial route reports** and **stitch** them.

We mitigate, not eliminate: wake lock, big clear "keep this screen on, stay in the
app" instructions, and a live **"GPS stalled"** warning the moment fixes go quiet.

## 1. Device identity (the foundation — no login)

We already set a `qcv` visitor cookie per device. Promote it to a durable
**contributor id**:

- `contributors(device_id PK, created_at, display_name?, points, level, referred_by, last_seen)`
- Persist the id in `localStorage` + cookie (survives reloads; a cleared browser =
  new identity, acceptable trade-off for no-login).
- Everything a device does is attributed to its `device_id`. No email, no account.

## 2. Earning surfaces (each awards points)

| Contribution | Points | Status |
|---|---|---|
| Add a POI / business | e.g. +10 (approved: +20) | ✅ intake shipped — wire to points |
| Record a combi route segment | +points by length/new coverage | 🔲 build |
| Confirm/flag an existing place | +2 | 🔲 build |
| Referral (invite → new device contributes) | +25 | 🔲 build |

Points ledger: `point_events(device_id, kind, ref, points, ts)` → sum into
`contributors.points`. A **leaderboard** (top devices, this week / all-time) drives
the game loop. Optional **levels/badges**; rewards (sponsor perks, free stuff) TBD.

## 3. Combi route recording (crowdsourced, aggregated)

Public recorder (ports the admin `grabar.html` capture into the rider app):

1. Rider boards, taps **"Grabar esta ruta"**, types the **combi name** + a short
   **description** (e.g. "Centro → San Lorenzo").
2. Full-screen record UI: wake lock on, **"mantén la pantalla encendida y no
   cambies de app"**, live GPS-quality + a **stall warning** if fixes stop.
3. Rides; taps **stop** (or auto-stops on long GPS silence). The trace uploads as
   a **route report** tied to `device_id` + the combi name — points awarded.

**Aggregation (the key part):**
- `route_reports(id, device_id, combi_name_raw, description, geometry, ts, quality)`.
- Reports are **clustered by combi** (fuzzy name match + geometric overlap), then
  **merged** into a best-estimate line: overlapping segments reinforce each other,
  non-overlapping segments extend coverage, outliers drop.
- A route goes "publishable" once coverage + agreement cross a threshold; a human
  confirms, then it's promoted to the live map (same gate as today).
- This turns dozens of partial, imperfect phone traces into one good route — and
  it's *self-healing*: more reports = better geometry over time.

## 4. Why device-points + aggregation fit each other

The background-recording limit means contributions are inherently **partial and
noisy**. Points incentivize *volume* (many riders, many partial traces); aggregation
turns volume into *quality*. The game loop (points, leaderboard, referrals) is what
generates the volume. They're the same system.

## Build order (recommended)

1. **Device identity + points ledger + leaderboard** — the foundation everything
   hooks into. Wire the already-shipped POI intake to award points first.
2. **Combi route recorder + report aggregation** — the highest-value crowdsource
   (and what you keep asking for). Honest UX about screen-on/foreground.
3. **Referrals** — device-to-device invite links, points on first contribution.
4. **Rewards/levels** — once there's a contributor base to reward.

## Separate but related: getting our *agent-discovered* data into search

"Yom! not found" — Yoms! **is** in our discovery data (`instagram.db`, @yoms.mx),
but the discovery stores aren't wired into the live search index yet (that's the
"last mile"). Two paths, both worth doing: **(a)** the user-driven add-a-place
intake (shipped), and **(b)** publish the high-confidence unified discovery places
into the search layer / admin queue. (b) is what makes our 4.7k harvested places
searchable — a strong near-term build independent of gamification.
