# MiTehuacán — Local Sponsorship Marketing Plan

*v2 — 2026-07-20. Incorporates the adversarial review
(`business/research/07-adversarial-review-from-puebla.md`; per-phase
reconciliations in `financials/projections/challenges/`). Where v1 assumed
US-style sales mechanics, v2 plans for Tehuacán reality: multi-visit trust
building, cash collections, Facebook-as-the-internet, WhatsApp-as-the-platform,
and seasonal cash flow. Companion: PRD-backoffice.md. Anything the plan needs
that does not exist in the product is in §10 with an honest estimate.*

---

## 0. Executive summary

MiTehuacán is the first complete digital map of Tehuacán's combi system. Every
route is a daily habit for thousands of riders, and every business along a
route can be discovered at the exact moment someone is already traveling past
it.

The year-one objective is **not revenue — it is occupancy**: fill the map with
recognizable local businesses so the platform becomes self-evidently valuable
to riders and future sponsors. Revenue follows scarcity; scarcity follows
occupancy.

**What we actually hold (survived the adversarial review):**

- **The demo-to-live pipeline is real**: show the route in the shop, send the
  contract by WhatsApp, click-to-sign, **pin live within 5 minutes**. The
  review's verdict: "genuinely innovative for this market." It is the
  *accelerant* of a close — not a substitute for the 3–5 visits most closes
  will take.
- **DENUE prospect lists** — 28,727 located, categorized businesses; per-route
  door-knock sheets already generated (`tehuacan/prospects/*.csv`). "A
  legitimate operational advantage most local startups skip."
- **Measurable from day one** — impressions, taps, scans, DAU charted daily.
- **Phase 0 QR loop** — organic rider acquisition at zero ad spend. "The right
  starting point."
- **Barter placards** — "culturally smart"; visibility-for-wall-space is a
  trade Mexican micro-businesses understand.

**What v2 corrects (the review's core adjustments, now planning assumptions):**

| v1 assumed | v2 plans for |
|---|---|
| 10-minute walk-in close | 3–5 visits per close; first visit plants, later visits close |
| 25–35% close rate | **5–10% cold**, 20–25% warm (referral / repeat visit) |
| 100 sponsors in ~4 months | **100 in 9–12 months** (25 by month 3 incl. barter) |
| Monthly subscription framing | **One-shot "paquete de temporada"** (6 months prepaid) as the default offer |
| Payment = SPEI, frictionless | ~40% cash reality → **weekly cobranza route** + prepay discount |
| Web app drives adoption | **Facebook page IS the storefront**; the app is what it links to |
| Smooth revenue curve | **January and September dips modeled**; December strong |
| 80% renewal | Plan at **50–60%**; earn better |

---

## 1. What is sellable TODAY (no engineering required)

| Product | What the sponsor gets | Where it shows |
|---|---|---|
| **Pin de patrocinio** (per location) | Logo/letter-badge pin on every route passing within 150 m; tap opens their panel | Public map, route selection |
| **Paquete de temporada** | 6 months prepaid at founding rate, one payment | Contractual |
| **Barter placard** | Same pin, paid with wall space (our QR placard displayed) | Map + their storefront |

Contract mechanics (live): X months × $X MXN per location × N locations,
WhatsApp delivery, electronic click-signature, SPEI details on the contract
page, payments (transfer or cash) recorded against the total. Pins
auto-publish on signature; auto-unpublish on cancellation.

## 2. The flywheel

```
QR stickers in combis ──► riders scan ──► app habit (DAU)
        ▲                                    │
        │                                    ▼
sponsor placards in shops ◄── sponsors ◄── impressions worth paying for
        ▲                                    │
        └──── Facebook page content ◄────────┘  (routes, tips, new sponsors)
```

All loops instrumented: scans per sticker, impressions/taps per sponsor, DAU.

## 3. Phase 0 — Ignition (weeks 1–3)

Goal: an audience worth selling, visible pins, and a Facebook presence —
*before* the first paid ask.

1. **Sticker the fleet.** Batch TEH ×100–200 on the top corridors (§4).
2. **Seed 10–15 barter placards** with beloved businesses (mercados,
   tortillerías, neighborhood references). Zero cash, populates the map,
   every placard acquires riders, and these are the "logos on the slide"
   for paid visits.
3. **Launch the Facebook page** (review point: *Facebook is the internet
   here*). Minimum viable presence: page + 3 posts/week (route spotlights,
   "¿sabías que…" transit tips, new-sponsor welcomes), every post linking
   `mitehuacan.mx`. Join/post in the big Tehuacán community groups. Budget
   $0 in ads until organic proves the content.
4. **Baseline the numbers.** One week of DAU/scans = the first honest line of
   the sales script.
5. **Schedules for the top 10 routes** in /rutas — a more useful app converts
   more scanners into daily users.

## 4. Phase 1 — Build the marketplace (months 1–12): first 100 sponsors

**Territory chunking (review fix #7).** One seller cannot work 80 routes.
Roll out corridor-by-corridor; a corridor is "done" when its priority
prospects have had a first visit and its warm leads are in follow-up:

1. Centro core (routes 1/3/5/12/15/20 overlap zone) — highest density.
2. El Paseo / Bulevar corridor.
3. San Isidro & El Riego spokes.
4. San Lorenzo spokes.
5. Foráneas (Ajalpan–Zinacatepec corridor) — destination businesses, terminal
   adjacency, harvest-season sensitivity.

**The funnel, with adversarial math.** ~250 businesses per corridor shortlist
(from `tehuacan/prospects/`), of which priority categories ≈ 80–120.

- Visits: 2 field afternoons/week (heat-realistic), 6–8 visits/afternoon
  → **~55/month**, months 1–3 partially consumed by territory learning.
- First-visit closes (5–10%): ~3–5/month.
- Warm closes from visits 2–3 (20–25% of followed-up leads): ramping from
  month 2.
- **Targets: 0–2 paid in month 1 · 25 total by month 3 (incl. barter) ·
  50–60 by month 6 · 100 by month 9–12.**

**The warm-lead engine (because cold is 5–10%):**
- **Referral rule:** any signed sponsor who refers a business that signs gets
  a free month (founding sponsors: extends their locked rate). El compadre
  sells better than we do.
- Ask every barter placard for 2 introductions — barter partners are natural
  connectors.
- Combi drivers/checadores know every business on their route; small
  gratitude (airtime, comida) for introductions that sign.
- Sunday family decision reality: offer to come back "cuando esté su papá /
  el dueño" and book the time — a booked return visit is a warm lead, not a
  failure.

## 5. Sponsorship levels — plan vs. product

| Level | Status | Note |
|---|---|---|
| **Route/location pin** | ✅ SELLABLE NOW | Core product; per-location pricing in contracts |
| **Stop sponsor** | 🔨 NOT YET | Stops accumulating from PARADA events; sell later |
| **Category sponsor** | 🔨 NOT YET (small build) | Review warns: behavior shift + unproven-traffic objection make $1,500/mo exclusivity a hard sell early — price at $400-ish "featured" first |
| **Premium (home/search featured)** | 🔨 LAST | Scarcity products sell into a busy marketplace, not an empty one |

Sales rule unchanged: **we only sell what publishes today.** "Founding
position" is sold verbally (first pharmacy on the route keeps founding rate
forever) without needing the exclusivity feature yet.

## 6. Pricing & payment (adversarial-adjusted)

**Framing fix (review points 2 & 8): sell a paquete, not a subscription.**
Local businesses buy advertising one-shot (perifoneo, radio, flyers). So the
default offer is a **one-time payment for a season**, not a monthly promise:

| Offer | Price | Notes |
|---|---|---|
| **Paquete fundador — 6 meses** | **$1,500 MXN una vez** (= $250/mo) | The default ask. One decision, one payment, cash or SPEI |
| Founding monthly (if they insist) | $300–400/mo per location | Cobranza cost priced in |
| Standard (after first 100) | $500–800/mo per location | |
| Barter placard | wall space | Phased down as paid fills |
| Renewal | founding rate locked while continuously active | Plan on 50–60% renewing; schedule renewals to AVOID January and September |

**Planning average: $325/mo-equivalent** for the founding cohort (matches the
financial reconciliations — not the $500 standard rate).

**Competitive anchors (use the ones owners know):** perifoneo $500–1,000/day,
radio $300–800/spot, 5,000 flyers ≈ $1,000 — all one-shot and unmeasured. Our
paquete costs less than two days of perifoneo and works for six months, with
numbers they can see.

**Collections (review fix #8):**
- Prepaid paquete is the *point*: one collection event, not six.
- For monthly payers: a **weekly cobranza loop** folded into field afternoons
  (collect cash, record in admin on the spot, WhatsApp receipt).
- Every payment recorded against the contract in /patrocinios — the ledger is
  already built.

## 7. The sales visits (multi-visit reality, script en español)

**Visita 1 — plantar (10–15 min, no pretendas cerrar):**
Saludo largo, acepta el refresco. Pregunta por el negocio. Luego el demo:
selecciona la ruta que pasa por la puerta, muestra un pin sembrado, tap —
logo, panel. *"Su negocio está exactamente aquí. Los que van en la combi lo
verían todos los días."* Deja el precio del paquete y una tarjeta/volante con
el QR de la ruta. **Pide el WhatsApp del dueño.** Si el dueño no está:
*"¿Cuándo lo encuentro? Regreso el martes."* — y regresa el martes.

**Seguimiento (WhatsApp, día siguiente):** manda la liga de SU ruta en el
mapa + una línea: *"Así se vería su negocio. El paquete fundador de 6 meses
queda en $1,500 — se respeta esta semana."*

**Visita 2–3 — cerrar:** resuelve la objeción pendiente, y cierra con el
contrato por WhatsApp ahí mismo; su pin aparece antes de que salgas. La
regla de urgencia honesta: *"Los primeros 100 se quedan con tarifa de
fundador para siempre."*

**Objeciones:**
- *"No uso internet / no tengo página"* → "No necesita nada. Nosotros lo
  ponemos en el mapa; usted solo atiende a los que lleguen."
- *"La gente usa Facebook"* → "Sí — y ahí también estamos. Pero aquí sale
  justo cuando alguien ya viene pasando enfrente de su local, buscando su
  combi."
- *"¿Cuánta gente lo ve?"* → números reales del hub; desde el mes 2, SUS
  números.
- *"Está caro"* → "El paquete de 6 meses cuesta menos que dos días de
  perifoneo — y trabaja 6 meses, no una tarde."
- *"Lo tengo que consultar"* → "Claro. ¿Se lo mando por WhatsApp para que lo
  vean juntos? Paso el jueves." (Cada 'lo consulto' se convierte en visita
  agendada.)
- *"No quiero aparecer en nada"* (informalidad, review #5) → no insistir.
  "Sin problema." Nota en el prospecto y a la siguiente puerta. El mapa
  público no publica datos fiscales de nadie, pero el miedo se respeta, no
  se debate.

## 8. Distribution: Facebook + WhatsApp (new in v2)

- **Facebook page = the public storefront** (review #4). Content calendar:
  Mon route spotlight · Wed transit tip / schedule update · Fri sponsor
  welcome ("ya está en el mapa: Farmacia X, Ruta 23"). Every post links the
  route deep-link. Community groups > ads.
- **WhatsApp is the workflow** (review #9): contracts already deliver by
  WhatsApp; follow-ups by WhatsApp; receipts by WhatsApp. Product ask #1
  (§10) puts a WhatsApp button on every sponsor pin so the pin *sends the
  business customers the way they already talk to customers* — that converts
  the profile from "thing I manage for your benefit" into "thing that rings
  my phone."

## 9. Metrics & weekly review

From the hub, weekly: DAU · scans (per sticker, dead list) · sponsor
impressions & taps · **visits made / warm leads open / closes by visit
number** (funnel truth vs the 5–10% assumption) · MXN collected vs contracted
(collections health) · corridor coverage.

North-star Phase 1: **occupied placements.** Kill criteria: sticker 0 scans
in 30 days → move it; corridor <2 closes after full first pass → re-price or
re-pitch before more visits; cobranza >2 visits for one payment → convert to
prepaid or release.

Seasonality calendar: **push signings toward Oct–Nov and Feb–Mar; avoid
January and September renewals; December = collect prepays for the year.**

## 10. Product asks (updated queue)

1. ~~Prospect list generator~~ ✅ **shipped** (`tehuacan/scripts/18_prospects.py`
   → `tehuacan/prospects/*.csv`, per-route door-knock sheets).
2. **WhatsApp button on sponsor pin panel** — the review's highest-leverage
   point; makes the pin ring the owner's phone. *(Small.)*
3. **Per-sponsor stats page** — shareable "your month" link for renewals.
   *(Small.)*
4. **Promos on the pin panel** — optional "oferta" text. *(Small.)*
5. **Facebook OG deep-links per route** — sharing Ruta 23 shows "Ruta 23 —
   San Isidro" preview, so route spotlights unfurl properly. *(Small.)*
6. **Category featured/exclusivity flag.** *(Medium; gates Category Sponsor.)*
7. **Stop sponsors** — blocked on stop data. *(Later.)*
8. **Homepage featured module.** *(Deliberately last.)*

## 11. Risks & honesty notes

- The ten structural realities in the adversarial review are treated as
  planning constraints, not objections to argue with. Re-read it quarterly:
  `business/research/07-adversarial-review-from-puebla.md`.
- **Traffic claims stay honest** — real hub numbers only; founding pricing
  exists precisely because early numbers are small.
- **Contract template needs a lawyer's pass** before the first paid signature.
- **App usefulness gates everything** — schedules and coverage beat any sales
  tactic.
- **One-person bottleneck**: the kit is designed so Monse/David can run
  visits and cobranza with their own tokens; months 1–3 of any new seller are
  learning months (review #10) — plan output accordingly.
- Financial projections and their adversarial reconciliation live in
  `financials/projections/` (`z-master-combined.md` §Reconciliation).
