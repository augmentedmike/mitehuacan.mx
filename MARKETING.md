# MiTehuacán — Local Sponsorship Marketing Plan

*v1 — 2026-07-20. Companion to PRD-backoffice.md. The plan below is grounded in
what is live in production today; anything the plan needs that does NOT exist
yet is listed in §9 (Product asks) with an honest build estimate, so sales
never promises vaporware.*

---

## 0. Executive summary

MiTehuacán is the first complete digital map of Tehuacán's combi system. Every
route is a daily habit for thousands of riders, and every business along a
route can be discovered at the exact moment someone is already traveling past
it.

The year-one objective is **not revenue — it is occupancy**: fill the map with
recognizable local businesses so the platform becomes self-evidently valuable
to riders (more useful map) and to future sponsors (busy marketplace). Revenue
follows scarcity; scarcity follows occupancy.

**The unfair advantages we already hold:**

- **The demo closes itself.** A salesperson stands in the shop, opens
  mitehuacan.mx, selects the route outside the door, and the owner watches
  their block appear. Then: "firma aquí" — contract by WhatsApp, click-to-sign,
  and **the pin is live on the public map within 5 minutes of signing** (the
  publication rule is wired to the contract status). No other local medium can
  close and deliver in the same visit.
- **A complete prospect database.** Our DENUE layer contains **28,727
  registered businesses in the service area with coordinates and categories** —
  we can generate a ranked door-knock list for any route in seconds.
- **Measurable from day one.** Sponsor impressions (`sponsor_view`), pin taps
  (`sponsor_tap`), QR scans, and DAU are already charted daily in the admin
  hub. Renewal conversations happen over *their* numbers, not promises.
- **The audience engine is printing this week.** QR stickers in combis
  deep-link scanners straight to that combi's route — riders onboard
  themselves during the ride.

---

## 1. What is sellable TODAY (no engineering required)

| Product (today) | What the sponsor gets | Where it shows |
|---|---|---|
| **Pin de patrocinio** (per location) | Logo/letter-badge pin on every route passing within 150 m of their storefront; tap opens their detail panel | Public map, route selection |
| **Founding placement** | Early sponsors lock founding pricing while active | Contractual |
| **Barter placard** (for tienditas) | Same pin, paid with wall space: they display our QR placard, we display their pin | Public map + their storefront |

Contract mechanics (live): X months × $X MXN per location × N locations,
WhatsApp delivery, electronic click-signature, SPEI transfer details on the
contract page, payments recorded against the total. Pins auto-publish on
signature; auto-unpublish on cancellation.

## 2. The flywheel

```
QR stickers in combis ──► riders scan ──► app habit (DAU)
        ▲                                    │
        │                                    ▼
sponsor placards in shops ◄── sponsors ◄── impressions worth paying for
```

Both loops are instrumented: scans per sticker, impressions and taps per
sponsor, DAU — all daily series in the hub.

---

## 3. Phase 0 — Ignition (weeks 1–2, this week's QR blitz)

Goal: an audience worth selling, plus visible pins before the first paid call.

1. **Sticker the fleet.** Batch TEH ×100–200, install across the highest-value
   routes first (see §4 route ranking). Every sticker auto-verifies on its
   first rider scan.
2. **Seed 10–15 barter placards** with beloved, recognizable businesses
   (mercados, tortillerías, the neighborhood references). Costs nothing,
   populates the map, and every placard is another QR acquiring riders. These
   are our "logos on the slide" for paid conversations.
3. **Baseline the numbers.** One week of DAU/scans becomes the first line of
   the sales script ("X personas abrieron el mapa esta semana").
4. Enter **schedules for the top 10 routes** in /rutas — a more useful app
   converts more scanners into daily users.

## 4. Phase 1 — Build the marketplace (months 1–4): first 100 sponsors

**Where to hunt (from our own DENUE data, service area counts):**
abarrotes 5,869 · restaurantes 3,101 · ropa 1,367 · estéticas 1,362 ·
consultorios 941 · papelerías 906 · fruterías 813 · talleres 716 ·
farmacias ~250 · plus banks, hotels, gyms, schools, veterinarias.

**Priority targets** = businesses that (a) depend on foot traffic, (b) sit
within 150 m of high-ridership routes, (c) have an owner on premises who can
decide today: farmacias, consultorios/dentistas, estéticas, restaurantes/
tacos/tortas, ferreterías, refaccionarias/llanteras, papelerías, ópticas,
veterinarias, gimnasios, hoteles, escuelas particulares.

**Route ranking:** sell route-by-route, not door-by-door at random. Start with
the routes that win on (riders × businesses): centro corridors first, then the
San Isidro / El Riego / San Lorenzo spokes, then foráneas (Ajalpan–Zinacatepec
corridor — different pitch: destination businesses, bus-terminal adjacency).

**Cadence target:** 2 field afternoons/week × 8–10 visits × ~25–35% close at
founding pricing ≈ 5–7 new sponsors/week → **100 sponsors in ~4 months.**

## 5. Sponsorship levels — plan vs. product

| Level (from the vision) | Status | Note |
|---|---|---|
| **Route/location pin** | ✅ SELLABLE NOW | The core product; per-location pricing already in contracts |
| **Stop sponsor** | 🔨 NOT YET | Stops are only now being captured (PARADA events during recording rides). Sell later; don't promise dates |
| **Category sponsor** ("Farmacia recomendada") | 🔨 NOT YET (small build) | Exclusivity flag + featured ordering; ~1 session of work when we're ready to price it |
| **Premium** (search/home featured, banners) | 🔨 NOT YET | Deliberately last — scarcity products sell best into a busy marketplace |

Sales rule: **we only sell what publishes today.** Exclusivity can be sold
verbally as "founding position" (first pharmacy on the route gets founding
rate forever) without needing the feature yet.

## 6. Pricing (recommendation — Mike sets final numbers)

Anchors: a Facebook boost aimed vaguely at "Tehuacán" runs $1,000–3,000
MXN/month with zero purchase intent; a perifoneo car or flyers are one-shot.
Our pin is permanent, geo-perfect, and measured.

| | Founding (first 100) | Standard (after) |
|---|---|---|
| Pin, per location / month | **$250–400 MXN** | $500–800 MXN |
| Minimum term | 6 months | 3 months |
| Barter placard | wall space + placard stays up | (phased out as paid fills) |
| Founding lock | rate frozen while continuously active | — |

Payment: SPEI transfer (details on the contract) or cash recorded in admin.
Simple invoice-free receipts at first; facturación is a Phase-2 problem.

## 7. The sales visit (script en español — the working tool)

**Choreography (10 minutes):**
1. Walk in at a quiet hour. Ask for the owner. Phone out, app open.
2. Select the route that passes the door. Zoom to their block.
3. *"Todos los días, cientos de personas toman esta ruta. Cuando abren
   mitehuacan.mx para ver su combi, ven los negocios que están sobre la ruta."*
4. Show a seeded sponsor pin (Phase 0 barter pins earn their keep here). Tap
   it: logo, name, panel.
5. *"Su negocio está exactamente aquí. Por $X al mes, su logo aparece a cada
   persona que ve esta ruta — gente que ya pasa enfrente de su local."*
6. Urgency, honestly: *"Los primeros 100 negocios se quedan con la tarifa de
   fundador para siempre. Su competencia de la cuadra todavía no está aquí."*
7. Close: *"¿A qué WhatsApp le mando el contrato?"* — send from /patrocinios
   on the spot, watch them sign on their own phone, add their pin location
   while they watch. **The pin appears before you leave the shop.**

**Objections (respuestas cortas):**
- *"No uso internet / no tengo página"* → "No necesita nada. Nosotros lo
  ponemos en el mapa; usted solo atiende a los clientes que lleguen."
- *"¿Cuánta gente lo ve?"* → show the hub numbers on your phone; from month 2,
  show THEIR impressions/taps.
- *"Está caro"* → per-day math: "$300 al mes son $10 diarios — menos que un
  refresco, y sale a todos los que pasan en combi frente a su local."
- *"Déjame pensarlo"* → "Claro. Le dejo el contrato en su WhatsApp — la tarifa
  de fundador se respeta si firma esta semana."

## 8. Metrics & weekly review (already instrumented)

Weekly, from the admin hub: DAU · QR scans (per sticker, dead-sticker list) ·
sponsor impressions & taps (per sponsor) · new contracts signed · MXN
collected vs contracted · route coverage (% of top routes with ≥1 sponsor).

North-star for Phase 1: **occupied placements**, not MXN.
Kill criteria for tactics: a sticker with 0 scans in 30 days moves; a category
that never closes in 20 visits gets re-priced or re-pitched.

## 9. Product asks (engineering queue this plan generates)

Ordered by sales impact per unit of work:

1. **Prospect list generator** (admin): pick a route → ranked list of DENUE
   businesses within 150 m with category + name — the door-knock sheet.
   *(Small: the data and matching already exist.)*
2. **Per-sponsor stats page** — a shareable "your month" link (impressions,
   taps, vs route average) for renewals and WhatsApp follow-ups. *(Small.)*
3. **Promos on the pin panel** — optional "oferta" text field per location.
   *(Small.)*
4. **Category exclusivity flag** + "recomendado" ordering. *(Medium — gates
   selling Category Sponsor.)*
5. **Stop sponsors** — blocked on stop data accumulating from PARADA events.
   *(Later.)*
6. **Homepage featured module** — build when the marketplace is busy enough
   that scarcity is real. *(Later, deliberately.)*

## 10. Risks & honesty notes

- **Traffic claims must stay honest** — sell with real hub numbers, never
  invented ones. Early numbers are small; the founding rate exists precisely
  because sponsors are betting early.
- **Contract template needs a lawyer's pass** before the first paid signature.
- **App usefulness gates everything**: schedules for top routes and continued
  route coverage matter more to conversion than any sales tactic.
- **One-person sales bottleneck**: the kit (demo + WhatsApp close) is designed
  so Monse/David can run visits with their own tokens once trained.
