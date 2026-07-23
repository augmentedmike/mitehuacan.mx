# Rebuilt Financial Model — Organic, No-Sales-Team (v2)

*2026-07-21. Replaces the salesperson-driven projections in
`06-phase-revenue-projections.md` and `z-master-combined.md`, which are invalid under
the real operating constraint: **no sales team, no cash-collection staff — only
technology and organic growth.** Payment mechanics, fees, and the conversion band are
grounded in `financials/research/payments-cash-economy-2026.md` (fact-checked). Phase
order follows `business/research/09-organic-phase-reorder.md`.*

> ⚠️ **Read this first.** This model is deliberately *smaller and slower* than the old
> one. The old model assumed a salesperson closing sponsors — that revenue engine does
> not exist here. This model earns less near-term on purpose, because it costs almost
> nothing to run and builds a compounding data/user moat. **The single number the whole
> model hinges on — the free→paid boost conversion rate — is unproven in this market and
> must be validated by a live pilot before any total here is trusted.**

---

## 1. What changed vs. the old model

| | Old model (v1) | This model (v2) |
|---|---|---|
| Growth engine | 1 full-time salesperson, cold close | Organic: combi QR + business QR self-onboard |
| Lead product | Route sponsorships (paid, sales-gated) | Free directory + free fiestas; paid boost is *last* |
| Pricing | $250–800/mo **subscription** | One-shot **prepaid boost** ≥300 MXN (no subs) |
| Collections | Implicit monthly billing (unmodeled cost) | **None** — prepaid pay-to-publish, nothing to collect |
| Payment cost | ~0% (ignored) | **~4–6.5% + IVA** baked into every peso |
| Year-1 gross (Phase A) | $1,312,000 | **See §4 — an order of magnitude smaller** |
| Biggest risk | Churn | **Conversion rate (unvalidated)** |

---

## 2. The organic funnel (where revenue comes from)

```
Combi QR stickers ─► app riders (free, already working)
Business QR handout ─► vendors self-list in directory (free)  ◄── seed fiesta categories
Free "Fiestas" tool ─► hosts post events + needs list (free)
        │
        └─► qualified leads flow to listed vendors (free)
                │
                └─► SOME vendors buy a one-shot BOOST to appear first  ◄── the only $$
                        (WhatsApp pay-link → OXXO cash/card → webhook auto-publishes)
```

Revenue = **(listed fiesta vendors) × (monthly boost-conversion %) × (boost price) −
payment fees.** Everything upstream is free and organic. No sales, no billing.

---

## 3. Assumptions (every one is a lever to validate — not a fact)

| Driver | Conservative | Base | Optimistic | Basis |
|---|---|---|---|---|
| Fiesta-relevant vendors reachable in service area | 300 | 500 | 800 | DENUE subset (catering, repostería, salones, mobiliario/carpas, DJ, foto/video, decoración, flores, meseros) — *estimate, verify against DENUE* |
| Listed fiesta vendors by month 12 (organic self-onboard, no sales) | 60 | 150 | 300 | QR handout + fiesta pull; **unproven ramp** |
| Monthly boost-conversion (% of listed who buy a boost that month) | 2% | 3.5% | 6% | Research band 2–5% median, 5–10% top quartile — **SaaS-derived, unvalidated here** |
| Boost price (one-shot, 30-day featured) | $300 | $400 | $500 | ≥300 to clear fixed-fee floor |
| All-in payment fee (blended card+OXXO, +IVA) | 6.0% | 5.0% | 4.5% | §4 of payments research |

**Seasonality:** apply a **−40% dip in January and September** (cash-lean months, per
Puebla review) and a **+30% lift in the strong fiesta/cash months** around
Dec, May (bodas/XV season varies) — netted out, keep annual figures flat-to-slightly-up.

---

## 4. Base-case revenue ramp (illustrative — NOT a promise)

Listed fiesta vendors ramp organically to 150 by month 12. Boosts = listed × 3.5%/mo ×
$400, less 5% fees.

| Month | Listed fiesta vendors | Boosts/mo (3.5%) | Gross boost rev | Net (−5% fees) |
|---|---|---|---|---|
| 1 | 5 | 0 | $0 | $0 |
| 2 | 12 | 0 | $0 | $0 |
| 3 | 22 | 1 | $400 | $380 |
| 4 (Fiestas launches) | 35 | 1 | $480 | $456 |
| 5 | 50 | 2 | $700 | $665 |
| 6 | 68 | 2 | $952 | $904 |
| 7 | 85 | 3 | $1,190 | $1,131 |
| 8 | 100 | 4 | $1,400 | $1,330 |
| 9 | 115 | 4 | $1,610 | $1,530 |
| 10 | 128 | 4 | $1,792 | $1,702 |
| 11 | 140 | 5 | $1,960 | $1,862 |
| 12 | 150 | 5 | $2,100 | $1,995 |

**Year-1 gross boost revenue (base): ~$13,000–14,000 MXN.** Net after fees ~$12,000.
Exit run-rate ~$2,000/mo gross. *(Conservative case ≈ half this; optimistic ≈ 4–5×.)*

> This is the honest number. It is **~1% of the old model's Year-1 $1.31M.** The old
> number required a salesperson you do not have. This number requires nothing but the
> QR handout and the free feature loop — and it **compounds** (§6).

### Scenario spread, Year 1 gross boost revenue

| | Conservative | Base | Optimistic |
|---|---|---|---|
| Listed vendors @ mo 12 | 60 | 150 | 300 |
| Conversion / mo | 2% | 3.5% | 6% |
| Boost price | $300 | $400 | $500 |
| **Year-1 gross** | **~$4,000** | **~$13,500** | **~$55,000** |
| Exit run-rate (mo 12) | ~$650/mo | ~$2,100/mo | ~$9,000/mo |

---

## 5. Why this is still worth doing (the case against the small number)

1. **Cost to run ≈ zero.** No salesperson salary/commission (the old model paid the
   salesperson **$262,400/yr**), no cash-collection route, no ad spend. The QR handout
   and self-serve payments are the entire go-to-market. Near-100% of net is retained.
2. **It builds the moat while it earns.** Every free listing and every fiesta is data
   and habit — the 28,727-business DENUE layer becomes a *populated, self-verified*
   directory. That is the asset later phases monetize.
3. **Conversion is warm, not cold.** Once a vendor is listed and sees free leads
   arrive, the boost is an inside-sale ("you got 3 leads free — want them first?"), not
   the cold close our Puebla review says takes 3–5 visits. This is the structural win.
4. **Optionality.** If the pilot shows conversion at the top of the band (or higher —
   plausible because the boost is bought against *visible* leads, not a SaaS trial),
   revenue scales fast with zero added cost.

---

## 6. How it compounds beyond Year 1 (the flywheel, monetized)

Each layer reuses the same free-listing + WhatsApp-pay-link + webhook rails. No new
sales capability required.

| Layer | Adds | When |
|---|---|---|
| **Fiesta boosts** (above) | One-shot featured for fiesta vendors | Phase 4 (first $) |
| **Seasonal fiesta packages** | Higher-priced bundles into XV/boda/Dec season | Year 1 H2 |
| **Category "Recomendado"** | One-shot featured in directory search (dentist, farmacia…) | Year 2 |
| **Event-host upsells** | Premium invitations, extra RSVP capacity (host-side, tiny) | Year 2 |
| **Other verticals** (home services, tianguis, jobs) | Same rails, new categories | Year 2+ |

Year-2 modeling is deferred until the **pilot returns a real conversion number**.
Projecting Year 2 on an unvalidated conversion rate would repeat the exact error this
document is correcting.

---

## 7. What must happen before these numbers mean anything

1. **Run a boost pilot** with 20–40 already-listed fiesta vendors receiving free leads.
   Measure the **real monthly boost-conversion %** and willingness-to-pay. That single
   number rewrites §4.
2. **Confirm the DENUE fiesta-vendor pool** (the 300/500/800 estimate) against the
   actual data layer.
3. **Stand up the payment flow** (MP/Conekta Link de Pago with OXXO + webhook
   auto-publish) — see the Phase 2 PRD.
4. **Instrument the funnel**: QR scans → listings → leads → boost purchases, so
   conversion is measured, not assumed.

---

## 8. One-line summary

> Give the map and the directory away, let fiestas create demand, and sell one-shot
> boosts self-serve to warm, already-listed vendors. **Year 1 is small (~$4k–55k MXN
> gross, base ~$13k) but costs almost nothing and compounds.** The number that decides
> whether it's $4k or $55k is the boost-conversion rate — and that is a **pilot
> question, not a spreadsheet question.**
