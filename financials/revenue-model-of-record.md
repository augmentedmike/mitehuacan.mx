# Revenue Model of Record

**Status:** Canonical (decided 2026-07-24 by Michael). **This is the plan of record.**
It resolves the "four competing revenue models" problem
([`../business/research/13-consistency-audit.md`](../business/research/13-consistency-audit.md)
finding #1) by replacing all of them with one taxonomy, and it corrects the
no-salesperson over-rotation in `../business/research/09-organic-phase-reorder.md`
(finding #2).

**Two decisions define this model:**
1. **Six revenue lines, one referral primitive, sold prepaid with no transaction rake** (§1–4).
2. **A human salesperson closes the paid deals; collection is digital — SPEI / OXXO /
   bank — recorded against the contract. Growth stays organic and free.** (§2.1).

**Supersedes** as the revenue basis: `projections/z-master-combined.md`, the per-phase
`projections/a-…g-` files, `projections/organic-model-v2.md`, and the *subscription*
framing in `../PRD-revenue.md` (subscriptions are dead; see §2). Their numeric
projections must be rebuilt on this model before being cited as forward numbers.

**Re-validates / re-activates** (contra a strict reading of `09`): the sales motion in
[`../business/marketing-plan.md`](../business/marketing-plan.md), the ramp in
`../business/roles/03-revenue-forecast-12mo.md`, and the contract/collection ledger in
migration `0014_sponsors_contracts.sql` (the paid-close record; **now collected via the
digital rail**, not a cash route).

**Consistent with / unifies:** [`phase2-revenue-capture.md`](phase2-revenue-capture.md),
[`research/payments-cash-economy-2026.md`](research/payments-cash-economy-2026.md),
[`../business/research/11-storefront-freemium-monetization.md`](../business/research/11-storefront-freemium-monetization.md),
[`../business/research/12-seed-then-monetize-playbook.md`](../business/research/12-seed-then-monetize-playbook.md),
[`../PRD-phase3-fiestas.md`](../PRD-phase3-fiestas.md) §7b,
[`../docs/payments-rail-spec.md`](../docs/payments-rail-spec.md).

---

## 1. The decision — six lines, one primitive

Revenue comes from six product lines, all built on **one primitive (the referral)**
and sold **prepaid, with no transaction rake**:

1. **Sponsorships** — logo (or logo + map pin) on combi QR stickers, location
   stickers, and printed ad materials.
2. **Directory promotion** — paid position in the directory.
3. **Homepage** — placement on the homepage.
4. **Homepage + extra features** — homepage placement bundled with the premium
   business page (gallery, promotions, catalog — doc 11).
5. **Referral inclusion** — pay to be in the referral/recommendation pool for a category.
6. **Referral finder fees** — pay per qualified referral delivered.

> **Marketplace, sales, and Fiestas all monetize through the referral system**
> (lines 5–6). The referral is how the plan-a-thing graph becomes money.

## 2. Framing principles

- **We sell *visibility* and *referral-access* — never a cut of the transaction.**
  Cash disintermediates us: once two parties connect on WhatsApp they deal in cash and
  we never see the close. **No commission, ever.**
- **No subscriptions.** Everything is a **prepaid paquete / season / wallet** — one
  decision, one payment (marketing-plan §6: sell a *paquete de temporada*, not a
  monthly promise). This is the cash-economy constraint the payments research and the
  Puebla review established repeatedly. The `b–g` phase files' `$/mo` tiers must be
  rebuilt on this basis.
- **One collection rail.** SPEI / OXXO / bank transfer, recorded against the contract.

### 2.1 Go-to-market: sales-closed, digitally collected, organically grown

**The correction to `09`.** Growth and monetization are **two different engines** that
`09` wrongly merged into "no salesperson":

| Engine | How it works | Who/what drives it |
|---|---|---|
| **Growth (free)** | QR stickers, the fiesta **invitation loop**, free self-serve listings acquire users and supply at ~zero CAC | Organic — no salesperson needed to *acquire* (docs 10–12) |
| **Monetization (paid)** | A **human salesperson closes** the paid deals — the 3–5-visit relationship close the Puebla review says is unavoidable; self-serve paid adoption here is "near zero" | The salesperson (founder / operator / Monse-David), doing the **warm inside-sale** on already-free-listed, organically-warmed businesses |
| **Collection (digital)** | The customer pays by **SPEI / OXXO / bank on collection**, recorded against the contract in the `0014` ledger. **No cash-cobranza crew** — the money moves on the rail even though a human closed the deal | The digital rail; a self-serve pay-link + webhook is a **secondary** path for small/warm/repeat purchases |

Why this is stronger than either extreme: the human is the hand-holding self-serve
can't replace (fixing the review's "self-serve ≈ 0" doubt); the digital rail is what
removes the collections problem `09` feared. Organic growth still delivers warm leads
to the salesperson for free. **The salesperson converts; the loops acquire.**

- **One rail, two entry points.** Salesperson-closed (primary): contract by WhatsApp →
  SPEI/OXXO/bank details → payment recorded against the contract (the `0014` flow,
  digitally collected). Self-serve (secondary): OXXO/SPEI pay-link → signed webhook →
  auto-grant ([`../docs/payments-rail-spec.md`](../docs/payments-rail-spec.md)) for
  small/warm/repeat buys where a human close isn't worth the time.
- **Seedable.** Every line can still launch via the anchor-tenant motion (doc 12):
  seed 2–3 free credible partners → prove pull → the salesperson flips newcomers to
  paid → grandfather the anchors free forever.

## 3. The three layers (by intent)

| Layer | Lines | What's sold | Intent / surface | Pricing |
|---|---|---|---|---|
| **1 · Brand & physical placement** | Sponsorships (1) | Real-world visibility | Off-app: combi stickers, location stickers, ad materials (the perifoneo/flyer equivalent) | Prepaid **paquete** |
| **2 · On-app visibility** | Directory promotion (2) · Homepage (3) · Homepage + features (4) | Position on our surfaces | Browse → feature → premium storefront; scarcity + price rise up the ladder | Prepaid **season** |
| **3 · Referral / performance** | Referral inclusion (5) · Referral finder fees (6) | Access to **active** demand | Highest intent — a host/resident is *asking* for a provider now | Inclusion = flat prepaid; finder fee = prepaid **saldo wallet** |

Intent — and price — rises down the table: brand reach → on-app position → **active
referral** (bottom-of-funnel, priced highest).

## 4. The lines in detail

### 4.1 Sponsorships (Layer 1)
Logo / logo+map on physical surfaces businesses already understand (they buy perifoneo
and flyers one-shot). **Sold by the salesperson** as a prepaid paquete (the relationship
close; marketing-plan §7), **collected via SPEI/OXXO/bank**, recorded against the
contract. The free QR listing still seeds supply self-serve; the salesperson closes the
paid sponsorship as a warm upgrade. This is the original "route sponsorship" — a prepaid
placement paquete, **not** a monthly subscription.

### 4.2 Directory promotion · Homepage · Homepage + features (Layer 2)
The visibility ladder over `negocios`:
- **Directory promotion** = "Destacado" — appear first in category + zona (grant =
  `negocios.boosted_until`).
- **Homepage** = the scarcest inventory (the vision doc's "digital real estate"), sold
  last, into a busy marketplace.
- **Homepage + features** = homepage placement bundled with the premium page
  (`premium_until`; doc 11). Promotions double as the weekly-habit surface (`/api/ofertas`).
All prepaid seasons: auto-downgrade on expiry (features locked, not deleted), re-up as a
fresh close/pay — never a recurring charge. Sold by the salesperson (warm) or self-serve
pay-link (small/repeat).

### 4.3 Referral inclusion & finder fees (Layer 3 — the marketplace engine)
How Fiestas, home services, and every future "plan-a-thing" vertical monetizes. When a
resident states a need, we produce a referral to providers.
- **Referral inclusion (primary):** a provider pays a **flat prepaid** fee to be in the
  referral pool for its category/zona. Certain good, no trust trap. Salesperson-closable.
- **Referral finder fees (secondary):** pay **per qualified referral delivered**, funded
  from a prepaid **`saldo` wallet** ("recarga saldo" — 84% of MX lines are prepaid).
  **Charge on *delivery* of a qualified referral, never on close** (the close is off-
  platform cash, uncapturable). Add this only once referral volume is real.

**Trust rule (non-negotiable — PRD-phase3 §7b):** paying buys a provider *into the pool
/ into position*, **never the earned recommendation.** Reviews, `verified`, and
completed-job counts stay **unbuyable** and drive the "Recomendado" framing; paid slots
are labeled **"Destacado" (promoted)**. Free-tier providers still appear (paying buys
position, not existence). Selling the trust signal is fatal in a viral-loop product — a
burned host tells the WhatsApp group.

## 5. What this is (and isn't)

- **It is** an advertising + lead-gen business — brand placement + on-app visibility +
  referral access — sold by a **human salesperson doing warm inside-sales**, collected
  **digitally**, grown **organically**. Compounding, cash-native, ramen-profitable early.
- **It is not** a subscription SaaS, a transaction-rake marketplace, or a pure "tech is
  the salesperson" self-serve model. Growth is organic; *monetization is human-led*.

## 6. Three things to nail (open design points)

1. **Finder fees ride the prepaid `saldo` wallet and charge on delivery, not close.**
   Keep flat **inclusion** primary; finder fees secondary and later.
2. **Sales close + digital collection, not cash cobranza.** The salesperson closes and
   the customer pays on the SPEI/OXXO/bank rail against the contract — no one carries a
   cash bag. Reconcile the `0014` `payments` ledger with the self-serve `pagos` ledger
   (one source of truth for "who paid what").
3. **The trust rule governs inclusion** — sell position, never the earned signal.

## 7. What this resolves / re-opens (audit cross-ref)

- **#1 (four models):** resolved — this is the single plan of record; the four are
  demoted to scenario/history.
- **#2 (no-sales contradiction):** resolved by **decision, not deletion** — there *is* a
  salesperson; `09` is corrected, `marketing-plan` and `03-revenue-forecast` are
  re-validated (with digital collection).
- **#3 (subscriptions):** resolved — no line is a subscription; the `b–g` `$/mo` tiers
  are rebuilt on prepaid/referral pricing.
- **#4 (merchant-of-record / RFC / IVA):** **still open and now first-order** — this
  model books revenue through a PSP and (for SPEI/card) issues facturas + remits IVA, so
  the platform's own legal/tax entity must be resolved before any line goes paid.
- **#5 (price floor), #6 (conversion rate):** still open — per-line pricing and free→paid
  conversion remain **pilot measurements**.
- **Ledger reconciliation:** re-opened — `0014 payments` (sales-closed) vs `pagos`
  (self-serve) must be unified (§6.2).

## 8. One-line summary

> Six revenue lines on one **referral** primitive — sponsorship, directory promotion,
> homepage, homepage+features, referral inclusion, finder fees — sold **prepaid, no
> subscriptions, no rake**. **Growth is organic and free; a human salesperson closes the
> paid deals; collection is digital (SPEI/OXXO/bank) against the contract — no cash
> cobranza.** Sell visibility and referral-access; never the trust signal, never the cash
> close.
