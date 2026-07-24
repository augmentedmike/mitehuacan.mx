# Network Effects & Organic Growth — Does the Path Hold?

*2026-07-24. A network-effects / organic-growth-hacking audit of the whole
roadmap. Written to answer one question: **is the current organic, no-sales,
QR-seeded path actually the right growth engine, or does it just feel right?**

Verdict up front: **the path holds — but it is under-formalized in one place that
matters, and that gap is the single highest-leverage thing left to build.**

This doc does not re-order the phases. It builds on
[`09-organic-phase-reorder.md`](09-organic-phase-reorder.md) (order stands),
[`07-adversarial-review-from-puebla.md`](07-adversarial-review-from-puebla.md)
(constraints stand), the live roadmap (`build/combis/roadmap/index.html`), and
[`PRD-phase2-fiesta-vendor-directory.md`](../../PRD-phase2-fiesta-vendor-directory.md).
It adds three things those docs lack: (1) a precise vocabulary for *why* the
model grows, (2) verdicts on three new product ideas raised in July 2026
(double-dating, the fiesta RSVP loop, the project/home-services directory), and
(3) identification of **the keystone** the roadmap names but does not yet spec —
now written up as [`PRD-phase3-fiestas.md`](../../PRD-phase3-fiestas.md).*

---

## 1. The one-sentence verdict

> You have a **distribution primitive** (the combi QR) and the beginnings of a
> **marketplace network effect** (the directory). You do **not yet have a viral
> loop.** Fiestas is the first thing on the roadmap that is one — and the
> *invitation* is the loop. Build the invitation as the flagship artifact, and
> the flywheel every existing doc describes finally has a motor.

Everything below is the argument for that sentence.

## 2. Three mechanisms — stop conflating them

The existing docs blur three different growth mechanisms under the word
"flywheel." They are not the same thing and they fail for different reasons.

| Mechanism | What it is | What we have | Truth |
|---|---|---|---|
| **Distribution primitive** | A zero-CAC *channel* to acquire one user at a time | Combi QR stickers | Real and proven. But a channel is a **faucet**, not a loop — it does not compound. Stop stickering and growth stops. |
| **Viral loop** | Using the product *recruits new users as a native act* | **None live** | This is the gap. Nothing in the live product makes a user pull in the next user. |
| **Marketplace / cross-side NFX** | More supply → more useful → more demand → more supply | Directory (`negocios`) + Fiestas (planned) | The prize. But directories *alone* are weak — no daily habit, easy to fork (the Yelp problem). NFX needs a loop to feed it. |
| **Data / trust NFX** | More usage → better data → more usage | Route accuracy, DENUE layer, reviews (future) | Real but slow and weak on its own. Nobody switches cities for a better bus map. Becomes strong only when it is **local trust** (§6). |
| **Rake** | Take a % of the transaction | **Impossible here** — cash economy, guaranteed disintermediation | Not a growth mechanism; a *monetization* one. And it is closed to us. Monetize visibility, never the transaction (§9). |

**The strategic error to avoid:** expecting the *directory* to be the growth
engine. It is the moat and the monetization surface. It cannot grow itself,
because listing a business is not a viral act. The engine must be **social /
invitational**, and it lives in Fiestas.

## 3. The reframe: MiTehuacán is a "plan-a-thing" graph

The roadmap already gropes toward this. Its horizon line reads: *"Cada evento de
vida — cumpleaños, mudanza, casa nueva, negocio nuevo — genera prospectos
calificados."* That is the whole company in one sentence — it just is not
formalized as the architecture.

Formalized: **every section is the same primitive repeated.**

> **Someone plans a *thing*, invites their *people*, and needs *providers* for it.**

- A **trip** = a thing, with a destination and a route.
- A **fiesta** = a thing, with guests (people) and vendors (providers).
- A **double date** = a small fiesta — 4 people, one venue.
- **Building a house** = a thing, with a needs-list (materials, labor, electrical,
  concrete) and providers.

Every section is `PLAN(thing) → INVITE(people) → MATCH(providers) → PAY(cash)`.
One identity (the WhatsApp number, already chosen), one schema, one set of loops,
one OXXO rail.

**Why this matters for growth:** build seven features and you cold-start seven
networks with one founder. Build **one plan-a-thing graph** and every section
feeds the same network — supply seeded for fiestas is supply for home services;
a host acquired by an invite is a future home-services customer; a review earned
at a party is trust capital for every category. The effects **compound across
sections instead of restarting per section.** This is the difference between a
bundle of apps and a platform.

## 4. Network-effect map of every section

| Section | Live? | Frequency | NFX type | Loop? | Role in the machine |
|---|---|---|---|---|---|
| **Combis / transport** | Live | **Daily** | Weak data NFX | No (QR is a faucet) | **The habit.** Top of every funnel; civic trust anchor. Reason to open the app. |
| **Eventos** (city agenda) | Built | Weekly | None | No | Content + the *renderer* the invitation page reuses. Distribution surface. |
| **Directorio** (`negocios`) | Live | Weekly–monthly | Cross-side + trust | No | **The hard side.** Supply. The moat once dense + reviewed. Not a growth engine. |
| **Fiestas** (invitation) | Planned P3 | Monthly (year-round) | Social viral + cross-side | **YES** | **THE engine.** Invitations = acquisition. Feeds the directory with qualified demand. |
| **Grupos / dating** | Not built | — | Same-side social + pairing | Yes (high-variance) | A *mode* of the fiesta graph, not a vertical. See §8.2. |
| **Home services / projects** | Horizon | **Yearly** | Weak | No | High-ticket lead-gen + trust data. **Moat/LTV, not a loop.** See §8.3. |
| **Tianguis / Empleos / Rentas** | Stubs | Varies | Marketplace | No | Future rails. Do **not** cold-start until the invitation loop is proven (§10). |
| **Sponsors / Boost** | Live/planned | — | — | No | Monetization on top of the above. Not growth. |

Read the "Loop?" column top to bottom: **exactly one section is a viral loop.**
That is the whole point of this document.

## 5. The frequency ladder

Network effects need a *habit* to inject loops into. Order the sections by how
often a resident touches them; anchor attention on the frequent, run the loop on
the social, monetize on the valuable:

```
DAILY     Transport map          → the habit / reason to open the app
WEEKLY    Eventos, food, deals    → keeps the directory warm, earns browse time
MONTHLY   Fiestas / grupos        → THE viral loop (invitations = acquisition)
YEARLY    Home projects, house    → the high-ticket monetization + trust data
```

The temptation is to chase the *yearly* tier because the tickets are big (a house
build is worth 100× a taquiza lead). Resist it as a *growth* bet: nobody opens an
app daily to build a house, so it cannot grow the network. The daily habit earns
the audience, the monthly loop grows it, the yearly ticket monetizes it.

## 6. "One city, completely" is the real moat

This is the load-bearing insight for a single-city product. **The network effect
is local, which makes a national competitor's scale irrelevant.** Google Maps has
a billion users and still cannot tell you which taquiza in Tehuacán does 200-person
parties well, or when Ruta 23 actually runs.

The a16z local-marketplace playbook (OpenTable, early Uber, Nextdoor) is: **win
one geography's liquidity to ~100%, then it is unassailable, then replicate the
*playbook* — not the network — in the next town.**

For MiTehuacán the win condition is therefore **not "users"** — it is **coverage
of the hard side**: every real fiesta vendor, every combi route, every trusted
electrician in Tehuacán is *on the platform*. Because it is one mid-size city,
**full coverage is actually achievable**, and once done it is a local monopoly on
*trust* that cannot be forked — forking means re-door-knocking 28,727 businesses
and re-earning every review. The DENUE layer + QR self-onboard + review harvest is
exactly the machine that gets to full coverage at near-zero marginal cost.

**Implication for the plan:** the north-star is local density, not raw signups.
Depth in one colonia beats a thin layer across all of Tehuacán (see §8.1, §12).

## 7. The architecture in five "ones"

Everything collapses to this. Each section must map onto it or it does not belong:

- **One identity** — the WhatsApp number. Account, contact, edit-key, *and* the
  viral channel. (Already the design in the Phase 2 PRD — keep it everywhere.)
- **One habit** — the transport map. Daily, civic, trusted.
- **One loop** — the invitation. "Invite your people to a thing." Fiestas, grupos,
  events. The only compounding growth engine; invest here disproportionately.
- **One moat** — local density + verified reviews in a single city (§6).
- **One rail** — prepaid collection via SPEI/OXXO/bank. **Paid deals are salesperson-closed
  with digital collection** (against the contract); a self-serve webhook is the *secondary*
  channel. Growth (above) stays organic/free. See
  [`../../financials/revenue-model-of-record.md`](../../financials/revenue-model-of-record.md) §2.1.

## 8. Verdicts on the three July-2026 ideas

### 8.1 The fiesta RSVP loop → this is the engine. Go harder.

The idea: hosts create a fiesta "page," send RSVPs to everyone they want, get
shown providers for the party; every RSVP recipient becomes a future host.

**Verdict: correct, and the most important thing on the roadmap.** Why it is
genuinely viral *in this market specifically*:

1. **Fan-out is huge.** A quinceañera invites ~150 people; a bautizo ~60; posadas,
   whole colonias. Invite counts are 10–50× a typical SaaS referral.
2. **Cycle time is short and never stops.** XV year-round, bodas, bautizos,
   graduaciones (Jun/Jul), posadas (Dec), Día de Muertos, patron-saint fiestas per
   barrio. The Mexican social calendar is a built-in growth cadence — you do not
   wait for virality, you **ambush the calendar** (§9).

The k-factor is real: `invites_per_host × guest→host_conversion`. With
invites_per_host in the tens, even a low guest→host rate compounds if cycle time <
retention — and fiesta cycle time is weeks, not months.

**The build discipline it demands:** the *invitation is the product.* The RSVP
page is the ad; the needs-list is the demand signal; the party is a live
acquisition event. Full spec in [`PRD-phase3-fiestas.md`](../../PRD-phase3-fiestas.md).

### 8.2 Double-dating → highest-variance idea. Ship as "grupos," not a dating app.

The safety/fun mechanic is a real insight with a hidden network-effects virtue:

> **Double dating solves the hard side of every dating product.** Dating markets
> die because women (the constrained side) do not feel safe or valued. Requiring
> each person to bring a friend means women arrive **in pairs, with social cover**,
> and every unit of 4 recruits ≥2 new users. The hard side self-supplies.

But the counter-forces are strong in a small conservative city, and they are
structural, not cosmetic:

- **Success = churn.** Dating's leaky bucket: it works, people couple, they leave.
  Structurally the worst retention curve of any category here.
- **Thin liquidity.** Needs many singles online *simultaneously* in one town.
  Brutal cold-start at city scale.
- **Stigma + "everyone knows everyone."** In a conservative city this is a privacy
  risk and — worse — a **brand swerve** away from the civic, family-trusted utility
  that makes MiTehuacán safe to put a QR on. A swipe app can poison the well the
  whole platform drinks from.
- **Safety liability.** You become responsible for strangers meeting.

**Verdict: do not spin up a dating vertical. Ship "grupos" — group outings — as an
*event type* inside the fiesta graph.** A double date is a 4-person fiesta at a
café. Culturally, group social events are the *only* acceptable on-ramp to dating
in a conservative town anyway. You capture the viral pairing mechanic, reuse the
entire stack (identity, invite, RSVP, venue-as-provider), and never bet the brand.
If grupos shows organic pull, *then* graduate it. Keep the double-date-as-safety
insight; discard the standalone-app framing. Treated as a low-cost experiment
appendix in the Phase 3 PRD (§9 there).

### 8.3 The project / home-services directory → moat and LTV, not a loop.

The idea: connect people to verified providers for what they want (build a house →
materials, labor, electrical, plumbing, concrete).

**Verdict: necessary and valuable — but understand what it is.**

- **Low frequency** (you build a house once a decade) → **no virality, no habit.**
  Do not expect network effects here.
- **Disintermediation is guaranteed.** Cash economy: once host and plumber connect
  on WhatsApp, they transact in cash and you never see it. **You cannot take a
  rake.** The Phase 2 PRD already chose visibility/boost monetization instead —
  protect that; any instinct to chase a % of the deal will fail.
- **Its real value:** high-intent, high-ticket **lead-gen** (monetize with boosts)
  + it generates **verified-project trust data** (this electrician did 30 jobs,
  photos, 4.7★) that Google and Facebook structurally cannot hold.

Treat it as the **LTV and moat layer** ridden on top of the habit (transport) and
the loop (fiestas). It is where the money is largest and the growth is smallest.

## 9. The cash / local growth-hacking playbook

Grounded in the constraints the Puebla review made non-negotiable — WhatsApp is
the OS, Facebook is the internet, cash is the currency, the compadre is the sales
force:

1. **Every loop terminates in WhatsApp.** Do not fight the WhatsApp group — inject
   *structure* into it. A host's group chat cannot show 10 caterers with prices and
   photos; the fiesta page can, then hands the lead *back* to WhatsApp. Be the
   index; WhatsApp is the runtime.
2. **Compadrazgo referral, everywhere.** The marketing plan already found the line:
   *"El compadre sells better than we do."* That is the entire acquisition strategy
   in five words. Vendor refers a vendor → free boost. Host refers a host →
   priority. Trust moves through family/compadre edges; make referral first-class.
3. **Reviews harvested at the party, not requested by email.** Guests were *there*
   and ate the food. One-tap post-fiesta WhatsApp prompt. This is how you bootstrap
   trust data in a low-trust cash market — from lived, attended events.
4. **Facebook community groups as the amplifier.** FB = the internet here. Route
   spotlights, "¿quién organizó esta fiesta?", new-vendor welcomes. $0 ads until
   organic content proves itself.
5. **Ambush the fiesta calendar.** Seasonal campaigns, not a steady drip: posadas
   in Dec, XV season, graduaciones Jun/Jul. Pre-seed the relevant vendor categories
   ~6 weeks ahead of each peak. Note the cash-dip months (Jan, Sep) the financials
   already flag — do not launch paid asks into them.
6. **The QR points at the loop, not just the map.** Combi QR seeds the habit;
   vendor QR seeds supply; **party QR** seeds hosts + reviews. Same primitive,
   three surfaces.

## 10. Where it breaks — the adversarial pass

Honest failure modes, in the house style:

| Risk | Why it bites | Mitigation |
|---|---|---|
| **The supply→demand gap** | Vendors self-onboard (QR), get no leads yet (Fiestas not live / thin), churn before the loop closes. The make-or-break window. | Launch Fiestas *close behind* the directory; **hand-generate the first leads** (concierge, §12). Do not let seeded vendors sit lead-less for a month. |
| **Disintermediation / no rake** | Cash + WhatsApp = the transaction leaves the platform the instant of match. | Never build a rake. Sell the *attention before* the match (boost/featured/priority-lead). Already the Phase 2 design. |
| **Dating brand + leaky-bucket + liability** | A swipe app poisons civic trust; success = churn; safety exposure. | Fold into "grupos" event-type; do not spin a vertical (§8.2). |
| **Thin habit** | A bus map is daily but *shallow* (10 seconds, gone). Attention may not transfer to the loops. | Earn browse time on the weekly tier (Eventos, deals) so there is a surface for the loop to live on. |
| **Cold-starting stubs early** | Tianguis/Empleos/Rentas are three future empty marketplaces; shipping them now = four cold-starts, one founder. | **Do not build them until the invitation loop is proven.** Sequence is the mitigation. |
| **Founder is the only operator** | Every concierge/seed motion is one person's time. | Win one colonia, not the city; the plan-a-thing graph reuses one build across sections so effort compounds. |

## 11. Kill criteria — the numbers that decide the path

The path is *validated by instrumentation, not by this document.* Watch:

- **k-factor of the invitation** = `invites_sent_per_host × (new hosts created ÷
  invitees)`. Target trend toward ≥1 within a fiesta cycle. If it stalls well below
  1 after the page is genuinely good, the viral thesis is wrong — reconsider.
- **Guest→host conversion** within one cycle (the compounding term).
- **Vendor lead→contact rate** (does the needs-list produce contact vendors value?).
- **Review capture rate** post-fiesta (is the trust moat actually accreting?).
- **Time-to-first-lead for a newly seeded vendor** (the supply→demand gap, §10).
- **Density per fiesta category in the pilot colonia** (are results non-empty?).

If the invitation k-factor and the guest→host rate move, the whole model is real
and self-funding. If they do not, no amount of directory seeding saves it — which
is precisely why the invitation is the keystone and the first thing to measure.

## 12. What this changes vs the existing docs

- **Phase order (`09`):** unchanged. Supply → demand → money still holds.
- **Adversarial constraints (`07`):** unchanged; reinforced.
- **Added:** the vocabulary (§2), the plan-a-thing graph as the *explicit*
  architecture (§3), the network-effect map (§4), the "one city completely" moat
  framing (§6), and verdicts on the three ideas (§8).
- **Identified the keystone:** the Phase 2 PRD deferred the consumer Fiestas tool
  as a non-goal. It is the loop. It now has its own spec —
  [`PRD-phase3-fiestas.md`](../../PRD-phase3-fiestas.md) — and it is the next thing
  to build well.
- **Do-things-that-don't-scale bootstrap:** concierge the first ~20 real fiestas by
  hand, in one colonia/corridor, routing leads to seeded vendors so they feel value
  before any paid ask. Prove the loop in one atomic network before spreading.

## 13. One-line summary

> The organic no-sales path is right. It just lacks its motor. You have a faucet
> (QR) and a moat-in-waiting (the directory) but no viral loop — and the loop is
> the invitation. Build the fiesta invitation as the flagship artifact, win one
> colonia's fiesta market completely, harvest reviews at the party, fold dating in
> as "grupos," keep home-services as high-ticket lead-gen, and let the plan-a-thing
> graph make every later section reuse the same loop. **Supply before demand before
> money — and the invitation is what turns demand on.**
