# Getting Paid Without a Sales Team — Payments in a Cash/P2P Economy

*2026-07-21. Fact-checked deep-research report scoped specifically to monetizing a
hyperlocal marketplace in Tehuacán, Puebla with **no sales team and no
cash-collection staff** — only technology and organic growth. Every claim below
survived a 3-vote adversarial verification (needs 2/3 to survive). Claims that were
investigated but **failed** verification are listed in §7 so we don't repeat them.
This is the evidence base for the rebuilt financials and the Phase 2 PRD's payment
design.*

*Method: 5 search angles → 23 sources fetched → 105 claims extracted → 25
adversarially verified → 17 confirmed, 8 killed. Confidence labels are the harness's.*

---

## 1. The headline design constraints (verified)

| Fact | Figure | Confidence | Source |
|---|---|---|---|
| Mexico is a cash economy | **>80% of transactions are cash**; 85% pay cash for purchases under 500 MXN (ENIF 2025) | High | Forbes MX; PCMI 2025 |
| Informal employment | **54.5–55.4%** (INEGI 2025) | High | Forbes MX; PCMI 2025 |
| Unbanked adults | **~45%** lack a bank account (Findex 2025: 55% have one) | High | Antom; MuralPay |
| The real barrier is non-economic | **"Fear of being seen"** by the tax authority (SAT) — traceability makes informal vendors feel exposed | High | Forbes MX; PCMI 2025 |

**What this dictates, non-negotiably:** the payment flow must (a) include a **cash
rail** (OXXO) so the ~45% unbanked can pay, (b) be **prepaid / pay-to-publish** so
there is nothing to collect and no late payment, and (c) **not force the vendor to
register anything traceable** — route money through consumer-side cash + a PSP that
abstracts the merchant relationship, so the vendor never feels "seen."

---

## 2. Why CoDi failed — and what it teaches us

CoDi (Banxico's free QR payment rail) was projected at **18M users / 27.9M annual
operations** and reached **~3.8M users and ~100k daily payments** — a drastic miss.
Banxico's own study blames: the pandemic, high cash use, informality, **fear of the
SAT**, and lack of internet phone lines. *(High confidence; Forbes MX citing Banxico.
Exact user count varies 1.6M–6.7M by source — the directional failure is solid, the
precise number is not.)*

**Design implication:** do **not** build on informal vendors adopting *merchant* CoDi
or registering as merchants. That is the exact thing they avoid. Instead put the
**consumer** on the paying side (OXXO cash / their own card) and let a PSP sit between.

> ⚠️ **Open question, not answered:** whether **DiMo** (Dinero Móvil, phone-number P2P
> on SPEI) is changing this where CoDi failed. Its adoption numbers did **not** survive
> verification. Do not assume DiMo solves the P2P problem — treat as unknown until
> re-researched.

---

## 3. The mechanism: self-serve payment link over WhatsApp → webhook auto-publish

This is the salesperson replacement, and it is **production-grade today**, not
speculative:

- **Mercado Pago "Link de Pago"** accepts, verbatim, *"tarjeta de crédito, débito,
  saldo en Mercado Pago Wallet, transferencia SPEI, depósitos en efectivo en Oxxo"*
  plus BNPL. Created in **3 steps** (amount → customize → share), **shared over
  WhatsApp or social**, and **the payer needs no MP account**. One tool covers card,
  bank transfer, and the cash rail. *(High; mercadopago.com.mx primary.)*
- **Payment webhooks auto-publish with zero human touch.** Both Conekta
  (`order.paid` / `charge.paid`, with retry + HMAC signing) and Mercado Pago deliver
  real-time payment events that "confirm payments without manual intervention." This
  is the technical mechanism that makes *pay-link → auto-publish the vendor's boost*
  work without staff. Requires building one receiver endpoint. *(High; Conekta
  developer docs + Mercately primary/secondary.)*

**The flow:** vendor taps "become Recomendado" in WhatsApp/app → we send a Link de
Pago for a fixed amount → they pay by card **or OXXO cash** → webhook fires → boost
publishes automatically. No human confirms the sale. No invoice. No collection.

---

## 4. Unit economics (verified 2025–2026 pricing — re-verify at build)

| Rail / provider | Fee | Settlement | Note |
|---|---|---|---|
| **Mercado Pago** card/SPEI | **3.49% + $4** instant → 3.19%+$4 (7d) → **2.95%+$4 (30d)** | instant–30d | +16% IVA |
| **Mercado Pago** OXXO cash | **3.79% + $4** | ≤3 days | +16% IVA; ~0.3pp over card |
| **Conekta** cash (OXXO Pay) | **2.6% + $3**, **min $5.4 commission** | — | +16% IVA; fixed floor hurts small tickets |
| **Conekta** card | 3.4% + $3 | — | +16% IVA |
| **Stripe MX** card | 3.6% + $3 (IVA incl) | — | — |
| Effective card rate on 1,500 MXN | Stripe 3.80% / Conekta 4.18% / MP 4.36% | — | Medium confidence (blog-corroborated) |

**The low-end trap:** Conekta's **$5.4 minimum commission** means a **100 MXN** sale
pays ~6.3 MXN incl. IVA = **~6.3% effective**. The fixed per-transaction peso fee
dominates at small tickets. **Implication: price the first paid product at ≥200 MXN**
(ideally 300–800), or bundle, so the fixed fee is diluted. On a 300 MXN boost, net
after fees ≈ **283–286 MXN**; on 800 MXN ≈ **765–770 MXN**. Viable — margins are fine
at ≥300 MXN, thin below 200.

> Note: Mercado Pago's **QR** option is cheaper (~0.99%, no fixed fee) than the payment
> link (3.49%+$4), but QR requires the payer present at a point of sale — not usable
> for a remote WhatsApp boost purchase. The link's convenience costs ~2.5pp; accept it.

---

## 5. Monetization model: one-shot prepaid, NOT subscription

- **Mexico has no micro-business subscription culture** (consistent with our own
  Puebla review). Advertising is bought one-shot. The model must be **prepaid
  "destacado/boost"** — buy 7 or 30 days of featured placement — not recurring billing.
- **Realistic free→paid conversion: 2–5% median, 5–10% top quartile.** *(Medium
  confidence — and this is the single largest modeling risk: the benchmark is
  **SaaS-derived and has NO validation in a cash-based Mexican hyperlocal market.**
  Treat 2–5% as a ceiling-anchored planning figure, not a promise. First Page Sage
  ~3.7% avg, Lenny Rachitsky 6–8% corroborate the band.)*
- **Worked example from the research:** if 1,000 vendors self-onboard via QR, plan
  **~20–50 paying for a boost per cycle at 200–800 MXN = ~4,000–40,000 MXN gross per
  cycle before fees.** This is the honest order of magnitude for a no-sales model — far
  below the old salesperson projections, but real.

---

## 6. The 2026 tailwind: Nivel 2 Bis accounts lower vendor friction

Published **June 17, 2026** in the DOF (amending Banxico circulars 3/2012 and 14/2017):
**"Nivel 2 Bis"** accounts — **no RFC required, online onboarding, monthly cap raised
to 15,000 UDIs (~130k MXN)** — explicitly target *tienditas, tortillerías, panaderías,
salones*. ~4.4M micro-businesses addressed. *(High confidence; NotiPress, corroborated
by El Financiero, El Cronista, Alto Nivel, El Imparcial.)*

**Why it matters:** a Tehuacán fiesta vendor can now hold an account that receives
digital payments up to ~130k MXN/month **without an RFC**, making a self-onboard "get
paid" path realistic where it wasn't before 2026. *Caveat: the reform is brand-new —
whether MP/Conekta/Clip actually expose a working Nivel-2-Bis self-onboarding flow, and
what documents it really needs, is not yet observable. Projected benefit, not proven.*

---

## 7. Claims that FAILED verification — do not use these

These surfaced in searches but were **killed** by the adversarial vote. Listed so we
don't accidentally cite them later:

| Killed claim | Vote | Why it matters |
|---|---|---|
| "Only 36% use debit / 11% credit cards (2024)" | 0-3 | Do **not** cite this card-penetration stat |
| "8.5M informal businesses = 63% of small businesses" | 0-3 | Business-count figure unreliable |
| "~9M business units, ~4M informal (44%)" | 0-3 | Business-count figure unreliable |
| "Conekta 2.9% + $0.30 USD; OXXO ~3.5%; MP ~3.5%" | 0-3 | Wrong fees — use §4 table instead |
| "Card fees 2.5–3.5% + $10–50 payout fee" | 1-2 | Use §4 |
| "Merchant onboarding takes weeks, needs notarized docs" | 0-3 | Not substantiated |
| "Informal merchants resist cards b/c requires bank acct + registration" | 0-3 | Plausible but unverified — don't state as fact |
| "Less than half have a bank account" | 1-2 | Superseded by verified ~55% have one / ~45% unbanked |

---

## 8. Open questions the research did NOT close

1. **DiMo's real adoption / P2P behavior change** — requested, no verified answer.
2. **Real willingness-to-pay and conversion for a boost among Tehuacán fiesta vendors
   specifically** — the 2–5% SaaS benchmark is unvalidated for this segment. *This is
   the number the whole revenue model hinges on; validate it with a live pilot before
   trusting any projection.*
3. **Whether a vendor can actually self-complete a Nivel-2-Bis onboarding from a phone
   today**, and what documents it truly requires.
4. **How comparable one-shot monetizers (Mercado Libre destacados, Facebook Marketplace
   boosts, DiDi/Rappi merchant) price and convert in Mexico** — asked, not quantified.

---

## 9. Bottom line for our model

1. **Payment stack:** Mercado Pago (or Conekta) **Link de Pago over WhatsApp**, must
   offer **OXXO cash** alongside card/SPEI, **webhook → auto-publish**. No human in the
   loop.
2. **Pricing:** one-shot prepaid boost, **≥300 MXN** to clear the fixed-fee floor. No
   subscriptions, no invoices, no collections.
3. **Cost of payments:** budget **~4–6.5% all-in** (higher on cash and small tickets,
   +16% IVA). Bakes straight into unit economics.
4. **Conversion:** model **2–5%** free→paid as a **ceiling-anchored planning figure**,
   flag it as the biggest risk, and **pilot to find the real number** before believing
   any revenue total.
5. **Timing:** respect the **January and September** cash-flow dips (our Puebla review);
   push boost promotions into strong-cash months.

---

### Sources (verified subset)

- Forbes México — *Por qué el CoDi ha fracasado* (Banxico study): https://forbes.com.mx/el-codi-ha-fracasado-como-medio-de-pago-por-la-informalidad-el-miedo-al-sat-y-la-pandemia/
- Mercado Pago — Link de Pago (fees, methods, WhatsApp): https://www.mercadopago.com.mx/herramientas-para-vender/link-de-pago
- Conekta — Pago en Efectivo / cash & pricing: https://www.conekta.com/payments/cash · https://www.conekta.com/pricing
- Conekta — Webhooks (order.paid/charge.paid): https://developers.conekta.com/v2.0/docs/eventos-webhooks
- Mercately — Mercado Pago webhook setup: https://support.mercately.com/es/articles/10579449
- PCMI — *LATAM informal economy & digital payments 2025*: https://paymentscmi.com/insights/2025-latin-america-informal-economy-digital-payments/
- Antom / MuralPay — OXXO Pay reach, unbanked %: https://knowledge.antom.com/mexicos-digital-economy-ripe-for-opportunity · https://muralpay.com/blog/top-payment-gateways-in-mexico-fees-settlement-fx
- NotiPress — Banxico Nivel 2 Bis (June 2026): https://notipress.mx/negocios/inclusion-financiera-llega-a-4-mill-comercios-nuevas-reglas-banxico-38114
- Free→paid conversion benchmarks 2026: https://knowledgelib.io/finance/saas-benchmarks/free-to-paid-conversion-benchmarks/2026
