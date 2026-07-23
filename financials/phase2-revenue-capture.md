# Phase 2 — How We Capture Revenue

*2026-07-21. The concrete revenue-capture design for the Fiesta Vendor Directory:
what we charge for, how the money is collected with no sales team in a cash economy,
what to price it at, and what it plausibly earns. Grounded in two fact-checked deep
researches — `financials/research/payments-cash-economy-2026.md` (rails/fees) and the
capture-mechanism research summarized in §7 below (Bodas.com.mx, IFT prepaid data,
event unit economics). Revenue math lives in `financials/projections/organic-model-v2.md`.*

> **The answer in one line:** free listing → the vendor pays a **one-shot "Destacado"
> boost** to appear first in their fiesta category, collected via a **WhatsApp pay-link
> (OXXO cash / card / SPEI) that auto-publishes on a webhook** — no salesperson, no
> invoice, no collection. Pay-per-lead (funded by a prepaid **saldo** wallet) is the
> secondary layer added once host demand is real.

---

## 1. What we charge for (and what we deliberately don't)

| Capture mechanism | Role | Why | Evidence |
|---|---|---|---|
| **Destacado (visibility-boost)** — pay to appear first in your category/zona for 30 days | **PRIMARY** | Charges for a **certain** good (placement). No trust problem. This is exactly how the largest MX event-vendor marketplace monetizes. | Bodas.com.mx premium-positioning contract, 51k+ MX vendors (high) |
| **Lead-unlock** — pay a small fee to contact/respond to a real host request, funded by prepaid **saldo** | **SECONDARY** (add when demand volume is real) | Value-aligned (pay only for a real party) but gated by host volume and carries lead-quality/trust failure modes. | Thumbtack/StarOfService/Oferteo prepaid-credit contact-unlock (high); trust failure quantified (medium) |
| **Verified badge** | Later / maybe | No evidence either way; revisit as a trust-layer product. | none found |
| **Commission on the booking** | ❌ **Never** | The transaction happens off-platform in cash. Uncapturable — trying to police it just pushes vendors away. | cash-economy research |
| **Monthly subscription** | ❌ **Never** | No micro-business subscription culture in this market. | payments research + Puebla review |

**Design principle:** sell a *certain* thing, prepaid, one-shot. Boost first because it
works from day one (needs only vendors, not host volume) and sidesteps the pay-per-lead
trust trap.

---

## 2. The capture flow — the money moment, with no human in it

### 2.1 Boost (primary, ships in Phase 2)
```
Listed vendor (already seeing free leads) taps "Aparecer primero — Destacado 30 días"
        ▼
We send a Mercado Pago / Conekta Link de Pago for the fixed boost price
        ▼
Vendor pays by  ► OXXO cash (reference, pay at any store)   ← required rail, ~45% unbanked
                ► card / SPEI
        ▼
PSP fires webhook (order.paid / charge.paid) → our Worker verifies signature
        ▼
Sets vendors.boosted_until = now + 30d  →  boost publishes automatically
```
No salesperson confirmed it. No invoice was issued. There is nothing to collect later.

### 2.2 Saldo wallet + lead-unlock (secondary, ships when host demand is real)
Once fiestas generate real lead volume, a per-lead charge means *many small
transactions* — and the fixed ~$4 peso PSP fee would eat each one. Solve it the way
every Mexican already understands: a **prepaid saldo wallet**.

```
Vendor "recarga saldo"  →  Link de Pago (OXXO cash / card)  →  webhook credits wallet
        ▼
Spends saldo on: unlock a fiesta lead (~$49)  OR  a boost (~$199)   ← internal ledger, no new PSP fee
```
- **Why a wallet:** the fixed fee is paid **once per recarga**, not once per lead. A
  $200 recarga funds ~4 lead-unlocks at ~5–7% blended cost instead of ~9% each.
- **Why it's low-friction:** ~84% of Mexican mobile lines are prepaid — "recarga tu
  saldo" is the single most familiar spending motion in the country. We map merchant
  monetization onto a mental model every vendor already owns.
- **Sequencing:** do **not** build the wallet for the boost MVP (a boost is one
  infrequent purchase — a direct pay-link is simpler). Introduce the wallet **with**
  lead-unlock, when small-ticket frequency justifies it.

---

## 3. Pricing (defensible starting points — A/B test, do not treat as final)

| Product | Launch price (MXN) | Test range | Anchor |
|---|---|---|---|
| **Destacado — 30 días** (appear first in category+zona) | **$199** | $99 / $149 / $199 / $299 | ~1–3% of one taquiza event ($5,750–18,000) |
| **Destacado — 7 días** (cheaper trial) | **$79** | $49 / $79 / $99 | entry price / impulse |
| **Lead-unlock** (per real fiesta lead) | **$49** | $29 / $49 / $79 | fraction of a single booked event |
| **Recarga saldo** tiers | **$100 / $200 / $500** | + bonus saldo on $500 | phone-recarga convention |

**Why these clear the fee floor:** a 100 MXN sale bleeds >6% to the fixed fee (verified).
Every price above starts at **≥$79**, and the flagship boost at **$199** keeps
all-in payment cost to **~5–6.7%** (higher on OXXO, +IVA). Net on a $199 boost ≈
**$186–189**.

**Affordability is not the constraint — willingness is.** Event economics prove a $199
boost is trivial against a $5,750+ taquiza or an $8,000+ DJ gig. The open question is
not "can they afford it" but "will they buy it," which only the pilot answers.

---

## 4. Unit economics per capture (verified fees)

| Sale | Rail | Gross | All-in fee (fee + IVA) | **Net to us** | Effective |
|---|---|---|---|---|---|
| $199 boost | OXXO cash (3.79%+$4) | $199 | ~$13.2 | **~$185.8** | 6.6% |
| $199 boost | card/SPEI (3.49%+$4) | $199 | ~$12.7 | **~$186.3** | 6.4% |
| $500 recarga | OXXO cash | $500 | ~$26.6 | **~$473.4** | 5.3% |
| $49 lead (from saldo) | — (paid at recarga) | $49 | $0 marginal | **~$49** | 0% marginal |
| $100 recarga | OXXO cash | $100 | ~$9.0 | **~$91.0** | 9.0% ← avoid small recargas |

**Takeaways:** (1) push recargas to **$200+** to dilute the fixed fee; (2) the boost is a
~100%-margin digital good — the only COGS is the ~6% payment fee; (3) lead-unlock funded
from pre-loaded saldo carries **zero marginal payment fee**, which is the whole reason
the wallet exists.

---

## 5. What it plausibly earns (illustrative — the conversion rate is unproven)

Driver = **active** fiesta vendors (listed **and** receiving leads) × boost-conversion
of active vendors × price. All three are pilot questions. Denominator is *active*
vendors, not total signups — the research's "~10–20% buy a boost" is of engaged vendors.

| | Conservative | Base | Optimistic |
|---|---|---|---|
| Listed fiesta vendors @ mo 12 | 60 | 150 | 300 |
| Active rate (got ≥1 lead) | 40% | 50% | 60% |
| Active → boost buyers / month | 8% | 12% | 18% |
| Boost price | $150 | $199 | $249 |
| **Boosts / month @ mo 12** | ~2 | ~9 | ~32 |
| **Gross boost run-rate @ mo 12** | ~$290/mo | ~$1,790/mo | ~$8,070/mo |
| **Year-1 gross (ramped)** | ~$1,500 | ~$9,000 | ~$40,000 |

Lead-unlock adds on top once demand is real (Year 1 H2 / Year 2) and scales with fiesta
volume, not vendor count. Seasonal fiesta peaks (Dec, XV/boda season) lift boost demand;
Jan/Sep cash dips depress it — time promotions accordingly.

> This is the **same order of magnitude** as the top-line organic model — small in Year
> 1, ~zero cost to run, compounding. The number that separates $1.5k from $40k is the
> boost-conversion rate, and **that is a pilot measurement, not a spreadsheet cell.**

---

## 6. The pilot that turns this from hypothesis into a number

1. Onboard **20–40 fiesta vendors** via QR in the densest Tehuacán corridors; route
   them **free** leads until they feel the value.
2. Turn on the **boost** pay-link for that cohort. Randomize price across **$99 / $149 /
   $199 / $299** to find the demand curve.
3. Measure: **% of active vendors who buy a boost/month**, repeat-purchase rate,
   **OXXO-vs-card split**, and price elasticity.
4. Only then layer in **saldo + lead-unlock** and measure lead→unlock conversion.
5. Feed the measured boost-conversion back into `organic-model-v2.md` §4 — that single
   number rewrites the whole revenue model.

---

## 7. Evidence base (this research pass)

| Finding | Confidence | Source |
|---|---|---|
| Largest MX event-vendor marketplace monetizes via **premium positioning, leads bundled — not pay-per-lead** | High (3-0) | bodas.com.mx/condiciones-legales-mx.php |
| **~84%** of Mexican mobile lines are **prepaid** (recarga/saldo is the universal model) | High (3-0) | IFT Q3 2024; blog.clip.mx; expansión |
| Pay-per-lead best run via **prepaid credits**; suits small transactions | High (3-0) | Point Nine; Thumbtack/StarOfService/Oferteo |
| Pay-per-lead charges on **contact regardless of winning**, ~$25–100 USD/lead, 10–30% job conversion → ~$250 CAC (trust failure mode) | Medium (3-0) | 7ten; pipelineon; auto-respond *(USD — translate, don't apply literally)* |
| Taquiza **$115–177 MXN/person** → ~$5,750–18,000 per 50-guest event | High (3-0) | taquizasjr.com; mexicazuelas.com.mx (primary) |
| DJ $8k–25k, photo $8k–25k, salón $15k–90k+ MXN/event | Medium (3-0) | solovivelo; redclubdjs; mercaditodelsur *(CDMX/wedding — overstates Tehuacán)* |

### What is NOT proven (and must not be sold as fact)
- **No Mexican precedent** was confirmed for a cash-loaded OXXO **saldo ad-wallet** for
  micro-vendors. The wallet rests on prepaid ubiquity (proven) + analogy (unproven).
- **Real Mexican destacado/boost prices** (Mercado Libre, Vivanuncios, FB Marketplace)
  were **not** found — the $99–299 boost price is inferred from event economics, not a
  sourced comp. A/B test it.
- **No measured free→paid conversion** exists for a hyperlocal fiesta-vendor niche. Every
  revenue figure here is a starting hypothesis.
- Unit economics skew **CDMX/wedding-inflated**; the taquiza floor ($115–177/person) is
  the most Tehuacán-representative anchor. Don't price off the salón/photo upper bounds.
- **Refuted, do not cite:** FB Ads $50–200 MXN/lead; specific Thumbtack conversion %;
  cheap DJ ($1,200–1,600) and catering ($160–300/guest) figures — all killed in review.

---

## 8. Decision summary

1. **Primary capture = one-shot Destacado boost**, ~**$199 MXN / 30 días**, via WhatsApp
   pay-link (OXXO + card) → webhook auto-publish. Ships in Phase 2. No sales, no
   collection.
2. **Secondary = prepaid saldo wallet + lead-unlock** (~$49/lead), added when fiesta
   demand is real. The wallet ("recarga saldo") is the cash-native, fee-amortizing,
   friction-free funding layer.
3. **Never** subscriptions, booking commission, or anything requiring the vendor to
   register/be "seen."
4. **Every price and conversion here is a hypothesis to A/B test in the boost pilot.**
   The pilot's measured boost-conversion is the one input that makes the financials real.
