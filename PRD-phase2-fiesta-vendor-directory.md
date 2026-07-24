# PRD — Phase 2: Fiesta Vendor Directory (QR-seeded, self-serve)

**Status:** Draft v1
**Owner:** Michael
**Date:** 2026-07-21
**Depends on:** Phase 1 (transport map, live) · combi-QR acquisition loop
**Feeds:** Phase 3 (Fiestas consumer feature) · Phase 4 (self-serve boosts = first revenue)
**Grounded in:** `business/research/09-organic-phase-reorder.md` (ordering) ·
`financials/research/payments-cash-economy-2026.md` (payments, fact-checked) ·
`financials/projections/organic-model-v2.md` (revenue)

---

## 1. Problem

We have a live transport map with organic daily users (combi QR stickers) and a
28,727-row DENUE business layer, but **no populated, self-maintained business
directory and no way for a business to put itself on the platform.** The existing
`places` table is *field-captured by our own people* (`/lugares` admin, "usar mi
ubicación"), which does not scale and does not create business ownership.

At the same time, the one product we believe will be big — **Fiestas** — is dead on
arrival without vendor supply in the categories a party needs (catering, cake, DJ,
photo, decor, rentals, venue). And our operating reality forbids the obvious fix:
**there is no sales team and no cash-collection staff.** Every earlier plan assumed a
salesperson closing sponsors; that person does not exist.

**So Phase 2 must do one thing:** let fiesta-service businesses **add and maintain
themselves** on the platform, for free, with **zero sales touch** — seeding the supply
side of the Fiestas marketplace and the data moat for everything after it.

## 2. Strategic context (why this, why now, why in this order)

- **Supply before demand before money.** Transport (live) → **Fiesta Vendor Directory
  (this PRD)** → Fiestas (Phase 3) → self-serve boosts (Phase 4, first revenue). The
  directory is the substrate; Fiestas is the demand that makes it valuable; money comes
  last and only after free leads are visibly flowing.
- **The QR handout reuses a proven mechanic.** Riders already self-onboard by scanning
  a combi sticker. We extend the *same* mechanic to businesses: a printable QR they scan
  to list themselves. No salesperson in the loop — the QR *is* the distribution.
- **Warm beats cold.** Once a vendor is listed and sees leads, later monetization is an
  inside-sale, not the 3–5-visit cold close our Puebla review says is unavoidable
  otherwise. This PRD's job is to manufacture that warm state at zero cost.

## 3. Goals

1. **Self-serve listing.** A fiesta-service business scans a printed QR and creates a
   usable profile from a phone in **under 5 minutes**, no app install, no account, no
   RFC, no salesperson.
2. **Fiesta-ready categories.** The directory captures the specific vendor categories
   and attributes a fiesta host will filter on (see §9), not a generic listing.
3. **Vendor ownership.** The listing business can edit its own profile (hours, photos,
   WhatsApp, price-from) via a returnable link — so the data stays fresh without us.
4. **Feed Fiestas.** Expose a clean, filterable vendor query the Phase 3 Fiestas feature
   consumes to match a host's needs to vendors.
5. **Instrument the funnel** end-to-end (QR scan → listing started → listing published →
   lead sent → boost purchased) so the Phase 4 conversion rate is *measured*, not
   assumed.
6. **Lay the payment rail** (self-serve pay-link + webhook auto-publish) so Phase 4
   boosts require no new go-to-market work — see §8.

### Non-goals (Phase 2)

- The consumer Fiestas planning UI itself (Phase 3 — this PRD only supplies it;
  now speced in `PRD-phase3-fiestas.md`, which is the viral loop this supply feeds).
- Charging anyone. The directory is **free**; the boost (Phase 4) is designed here but
  not the launch focus.
- Reviews/ratings (later — trust layer is its own phase).
- Replacing the field-captured `places` search entries (they coexist; see §7).
- Migrating the legacy manual `contracts`/`payments` sponsorship flow (it is superseded,
  not migrated — see §8.4).

## 4. Users

| Persona | Description | Primary needs |
|---|---|---|
| **Fiesta vendor** (e.g. a taquiza cook, DJ, repostera, mobiliario rental) | Micro-business, often informal, cash, WhatsApp-first, no website | List for free in 5 min from a phone; get leads on WhatsApp; edit later; never feel "seen" by SAT |
| **Fiesta host** (Phase 3 consumer) | Resident planning a party | Find trusted vendors by category, budget, area; contact via WhatsApp |
| **Coordinator** (Michael) | Runs the platform | Print QR batches; moderate listings; watch the funnel; toggle a listing |
| **Field helper** (optional) | Hands out QR flyers | Credit via existing `field_tokens` when they assist a signup |

## 5. The three surfaces

1. **QR self-onboard** — printable QR (per-batch or per-category) → landing → "list your
   business" form → published listing + a private edit link sent to the vendor's
   WhatsApp.
2. **Vendor directory** — the stored, filterable set of fiesta-ready vendor profiles.
3. **Fiestas feed (read API)** — the query Phase 3 uses to match host needs → vendors.

## 6. Self-serve onboarding flow (the core of this PRD)

```
Vendor scans printed QR  (e.g. mitehuacan.mx/alta?b=<batch>&c=<category?>)
        │
        ▼
Landing: "Aparece gratis para las familias que organizan fiestas en Tehuacán"
        │  (value-first, zero jargon, cash/informal-safe wording — NO 'factura', NO 'RFC')
        ▼
Form (phone-first, <5 min, no login):
   • Nombre del negocio
   • Categoría (chips: catering/taquiza, pastel, DJ, foto/video, decoración,
     mobiliario y carpas, salón, meseros, flores, mariachi…)
   • WhatsApp  ◄── the identity + contact + edit key, all in one
   • Zona / colonia served (free text or map pin — reuse places lat/lon capture)
   • Optional: 1–3 photos, precio desde, horario
        │
        ▼
Publish immediately  →  send edit link to their WhatsApp (returnable, tokenized)
   "Listo. Ya apareces. Para editar o agregar fotos: <link>"
```

Design rules (all trace to the payments/informal research):
- **WhatsApp number is the account.** No passwords, no email required. It is contact,
  identity, and the key to the edit link. Matches how these businesses already operate.
- **Never ask for RFC, factura, or bank details to list.** Listing is free and
  traceability-free; that fear is *the* documented reason CoDi failed. Money details
  only appear at the optional Phase-4 boost step.
- **Publish-first, moderate-after.** Zero friction to appear; coordinator can soft-toggle
  (`active=0`) spam. Don't gate publication on review.
- **Editable forever via the WhatsApp link.** Keeps data fresh with no staff.

## 7. Data model (extend, don't fork)

Reuse the existing `places` capture pattern and `field_tokens` crediting. Add a
vendor-profile layer rather than overloading `places` (which stays the *search* index).

Proposed (illustrative — engineering owns final schema; **this PRD does not change code**):

```
vendors
  id, name, category, whatsapp (unique-ish key), zona/colonia,
  lat, lon,                     -- reuse the /lugares 'usar mi ubicación' capture
  price_from_mxn (nullable),
  edit_token (for the returnable WhatsApp edit link),
  source ('self' | 'field' | 'denue-claimed'),
  self_onboarded_at,
  active (soft delete), boosted_until (nullable, set by Phase-4 webhook),
  created_at, updated_at
vendor_photos ( vendor_id, url, sort )
vendor_categories  -- if a vendor spans >1 fiesta category (M:N)
qr_batches ( batch_id, category?, printed_at, notes )   -- ties scans → funnel
leads ( id, vendor_id, host_ref, created_at, channel )  -- for the funnel + Phase 3
```

- **Coexists with `places`:** `places` remains the OSM-gap *search* layer; `vendors` is
  the *owned, fiesta-ready* profile layer. A vendor may also surface in search.
- **DENUE claim path (bonus):** because we hold the 28,727-row DENUE layer, a vendor's
  QR landing can pre-fill from DENUE (`source='denue-claimed'`) — they *claim* an
  existing pin instead of typing from scratch. Fastest possible onboarding.

## 8. Payment & monetization design (built here, activated in Phase 4)

Grounded entirely in `financials/research/payments-cash-economy-2026.md`.

### 8.1 The product
One-shot **prepaid boost** — "Aparece primero para tu categoría por 30 días" —
**priced ≥300 MXN** (below that the fixed per-transaction fee eats >6%). No
subscription. No invoice. No collection. Pay-to-publish.

### 8.2 The flow (this is the salesperson, in software)
```
Listed vendor (already getting free leads) taps "Aparecer primero" in WhatsApp/app
        ▼
We send a Mercado Pago (or Conekta) Link de Pago for a fixed amount
        ▼
Vendor pays by  ► card / SPEI   OR   ► OXXO cash (reference, pay at any OXXO)   ◄ REQUIRED rail
        ▼
PSP fires webhook (order.paid / charge.paid)  →  our endpoint sets vendors.boosted_until
        ▼
Boost publishes automatically. No human confirmed the sale.
```

### 8.3 Hard requirements from the research
- **OXXO cash rail is mandatory**, not optional — ~45% of adults are unbanked; cash is
  >80% of transactions. A card-only flow excludes half the market.
- **Vendor never registers as a merchant.** The consumer/vendor *pays*; the PSP
  abstracts us as the merchant. This sidesteps the SAT-visibility fear that killed CoDi.
- **Webhook-driven auto-publish** — the flow must complete with zero staff. One receiver
  endpoint (Cloudflare Worker) verifies the signed webhook and flips `boosted_until`.
- **Budget ~4–6.5% + IVA** all-in (higher on OXXO cash and small tickets) into unit
  economics.
- **No recurring billing, ever.** Re-boost is a fresh voluntary purchase.

### 8.4 Relationship to the legacy sponsorship module
The existing `sponsors`/`contracts`/`payments` tables (migration 0014) implement
**click-to-sign contracts with hand-recorded SPEI/cash payments** — i.e. a manual
collections operation. Under the no-sales model that is superseded: the boost above
replaces it for the fiesta vertical. Legacy tables stay for any already-signed barter
pins; new monetization runs on the pay-link + webhook path. **Do not extend the manual
payments flow.**

## 9. Fiesta categories to seed (supply the demand Phase 3 will create)

Catering / taquiza · Pastel & repostería · DJ / música / sonido · Mariachi / música en
vivo · Foto & video · Decoración & globos · Mobiliario, carpas y sillas · Salón de
eventos / jardín · Meseros / staff · Flores · Renta de brincolines/inflables · Piñatas
& dulces · Seguridad · Menaje/loza · Pastelería salada/botanas.

Seed order = the categories a host *always* needs first (catering, pastel, DJ, decor,
mobiliario, salón), so a host's first Fiesta has non-empty results.

## 10. Metrics (the funnel — instrument from day one)

| Stage | Metric | Why |
|---|---|---|
| Reach | QR scans per batch/category | Which flyers/areas work |
| Activation | Listing started → **published** (%) | Onboarding friction |
| Supply | Published vendors per fiesta category | Fiesta readiness |
| Freshness | % listings edited after publish | Self-maintenance working? |
| Demand | Leads sent to vendors (free) | The value that warms conversion |
| **Money (Phase 4)** | **Boost purchases ÷ listed vendors / month** | **THE number the model hinges on** |
| Payments | Boost pay-link → paid (%), OXXO vs card split | Rail health |

## 11. Pilot plan — validate the one unproven number before scaling

The revenue model rests on a free→paid boost-conversion rate that is **SaaS-derived and
unvalidated in this market**. Phase 2 exists partly to measure it for real.

1. Onboard **20–40 fiesta vendors** via QR in the highest-density Tehuacán corridors.
2. Route real (or seeded) fiesta leads to them for free; let them feel the value.
3. Turn on the boost pay-link for that cohort; **measure actual monthly conversion,
   OXXO-vs-card split, and willingness-to-pay** at 300 / 400 / 500 MXN.
4. That measured rate rewrites `organic-model-v2.md` §4. Until it exists, treat all
   revenue totals as illustrative.

## 12. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Vendors won't self-onboard without a human | QR value-prop is "get fiesta leads," not "list your business"; DENUE claim path removes typing; pilot measures real activation |
| Chicken-and-egg (no hosts yet → no leads → vendors churn) | Seed categories first; Phase 3 launches close behind; use transport user base as first hosts |
| Conversion far below 2% | It's a *pilot question*; near-zero cost to run means low downside; model's conservative case already assumes 2% |
| Cash/unbanked can't pay for boost | OXXO rail mandatory (§8.3) |
| SAT-visibility fear blocks signups | No RFC/factura/bank details to list; PSP abstracts merchant identity |
| Spam / fake listings | Publish-first + soft-toggle moderation; WhatsApp-verify on edit |
| Seasonality (Jan/Sep cash dips) | Time boost promos to strong-cash/fiesta months |

## 13. Milestones within Phase 2

| # | Deliverable | Gates |
|---|---|---|
| 2.0 | Confirm DENUE fiesta-vendor pool; finalize categories | Supply sizing |
| 2.1 | QR self-onboard landing + form + WhatsApp edit link | Self-serve listing live |
| 2.2 | Vendor directory + filterable read API for Fiestas | Unblocks Phase 3 |
| 2.3 | Funnel instrumentation (scan→list→lead) | Measurement live |
| 2.4 | Payment rail: pay-link + webhook auto-publish (OXXO+card) | Unblocks Phase 4 |
| 2.5 | Boost pilot with 20–40 vendors → **real conversion number** | Rewrites financials |

## 14. Open questions

1. Real willingness-to-pay / conversion for a boost among Tehuacán fiesta vendors — the
   pilot exists to answer this.
2. Does a vendor need any account at all to *receive* boost value, or only to pay?
   (Nivel 2 Bis, June 2026, may let them receive digital payments with no RFC — verify
   the live onboarding UX before relying on it.)
3. Mercado Pago vs Conekta as the pay-link provider (fees vs. the $5.4 Conekta cash
   minimum vs. MP's OXXO 3.79%+$4) — decide at build with re-verified 2026 pricing.
4. Should the DENUE-claim path launch in 2.1 or wait until 2.2?
5. How much of Fiestas (Phase 3) must exist before the directory has enough demand to
   keep vendors engaged — i.e. the minimum host-side MVP.

---

## 15. One-line summary

> Hand fiesta-service businesses a QR that lists them free in 5 minutes from a phone —
> no salesperson, no RFC, no account — seed the categories a party needs, feed it to a
> free Fiestas feature, and later sell warm, already-listed vendors a one-shot OXXO/card
> boost that auto-publishes via webhook. **This PRD builds the supply and the payment
> rail; Phase 3 builds the demand; Phase 4 flips on the money.**
