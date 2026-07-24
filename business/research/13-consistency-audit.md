# Doc Consistency Audit — Gaps & Inconsistencies

*2026-07-24. A four-cluster audit (financials, roadmap/phase-order, sales-model,
PRD/data-model) of the strategy corpus, with resolution status after the two
revenue decisions of the same day (see
[`../../financials/revenue-model-of-record.md`](../../financials/revenue-model-of-record.md)).*

**Root cause:** a fast pivot (Jul 20→24) produced new canonical docs (`09`, `10–12`,
`PRD-phase2/3`, `organic-model-v2`, payments-rail-spec) that are internally coherent,
but (a) the superseded docs were never banner-marked, and (b) the new docs weren't
reconciled against the shipped D1 schema. Result: parallel truths.

**Legend:** ✅ resolved · 🟡 open (needs decision/pilot) · 🔧 pending mechanical fix

---

## HIGH

**1. Four competing revenue models; year-1 base spanned $9K–$1.55M.** ✅
`organic-model-v2` (~$13.5K) · `phase2-revenue-capture` (~$9K) ·
`business/roles/03-revenue-forecast` (~$31K) · `z-master` + `a–g` ($1.55M). None
marked canonical. **Resolved** by `revenue-model-of-record.md` — single plan of
record; the four demoted to scenario/history. Their numeric projections must be
rebuilt on the new model before being cited forward. 🔧 add superseded banners to
z-master + a–g.

**2. "No sales team" contradicted across the corpus — including the newest doc.** ✅
`marketing-plan` (salesperson + cobranza), `01`, `08`, and `03-revenue-forecast`
(dated today, re-introduces a human operator) all contradict `09`'s "no sales team."
**Resolved by decision, not deletion:** decision #2 confirms a human salesperson
closes paid deals with **digital collection** (SPEI/OXXO/bank). So `09` is *corrected*
(its phase order stands; its no-sales premise does not), and `marketing-plan` /
`03-revenue-forecast` are **re-validated**. The audit's original framing (marketing-plan
= wrong) **inverts**. 🔧 09 corrected inline (done); soften "no salesperson" language
in 10/11/12/PRD-phase2/PRD-phase3/payments-rail-spec (done via GTM notes).

**3. "Never subscriptions" vs six docs built on subscriptions.** ✅ (framework) / 🔧 (numbers)
`PRD-revenue` §1 leads with monthly subscription; financial phases `b–g` model
$300–$800/mo recurring; `z-master` encodes them. **Resolved in principle** —
revenue-model-of-record forbids subscriptions (prepaid paquetes/seasons/wallet only).
🔧 the `b–g` `$/mo` tables must be rebuilt on prepaid pricing; PRD-revenue banner added.

**4. Merchant-of-record / RFC / IVA — unmodeled go-live blocker.** 🟡 **OPEN, first-order.**
Every doc handles the *vendor's* RFC fear; none addresses that *MiTehuacán itself*
needs a registered entity + RFC to hold the PSP account, issue facturas, and remit 16%
IVA on revenue. The model books revenue, so this now gates going paid. **Needs a
decision.**

**5. Boost/promotion launch price below the mandated fee-floor.** 🟡 OPEN.
Payments research + `organic-v2`: "≥300 MXN required, thin below 200."
`phase2-revenue-capture` launches Destacado at $199, a $79 7-day trial, $99 A/B floor.
**Needs a decision:** hold ≥300, or justify sub-300 margins.

**6. Public site advertises "citas/dating," which doc 10 forbids.** 🔧 PENDING.
Live roadmap horizon lists dating as a product; doc 10 says fold into "grupos" (which
appears on no public surface). The one contradiction real users see. Fix the public copy.

## MEDIUM

**7. Three superseded phase-orders un-annotated (`04`/`05`/`06`).** 🔧
Fiestas at 7th vs 5th vs D/month-10; `05` invents phases (Reviews, Restaurants).
Order superseded by `09`. Banners added (this batch).

**8. Phase-number drift: `09`/PRDs vs live site.** 🔧
Directory = "Phase 2" (docs) / "Fase 1" (site); Fiestas = "Phase 3" / "Fase 2–3".
Order agrees; numbers off by one. Unify (pending — touches the live roadmap).

**9. Two self-inflicted spec↔schema conflicts (payments-rail-spec).** ✅ FIXED (this batch).
(a) proposed `boosts` table contradicted the already-shipped `negocios.boosted_until`;
(b) proposed `negocio_media` duplicated the shipped `negocio_photos`. Both corrected
to reuse the shipped schema.

**10. `leads` table homeless.** 🔧 OPEN.
PRD-phase2 §7 and PRD-phase3 §7/§10 both reference it; no migration creates it; it's the
core "free leads delivered" metric. Assign owner + migration.

**11. `edit_token` ships but no resolver/edit endpoint exists.** 🔧 OPEN.
Self-serve edit, the tokenized manage link, and pay-auth all depend on a token→negocio
resolver not yet built. Required for MVP.

**12. "Superseded" legacy sponsors flow still actively extended.** 🟡 re-opened.
`0020_sponsor_logo` + `prd-backoffice` §4 extend `sponsors/contracts/payments` in
parallel with the new rail. Decision #2 **re-activates** this ledger as the sales-closed
collection record — so it is *not* frozen. But it must be reconciled with the self-serve
`pagos` ledger into one source of truth (revenue-model-of-record §6.2).

**13. Conversion-rate conflict + misattributed benchmark.** 🟡 OPEN (pilot).
`organic-v2` = 2/3.5/6% of *listed*; `phase2-capture` = 8/12/18% of *active*, and
attributes "~10–20%" to research that actually says 2–5%/5–10%. Pick one denominator;
fix the citation. Remains a pilot measurement.

## LOW

**14.** 🔧 Currency: `a–g` files use bare "$" (only cohere as MXN); `06` and `z-master`
*do* label MXN. Add the label to `a–g`.
**15.** 🔧 `z-master` reports two Year-2 totals ($6,139,300 vs $6,043,800 — dropped
$95,500 unallocated bucket).
**16.** 🔧 `descubre` promotes an orphan "Rentas" product (no roadmap/doc) and fronts
far-future stubs while hiding the actual next builds.
**17.** 🔧 Supply layer has five names; "Tianguis" names two different products.
**18.** 🔧 Smart Search pulled forward on the live site vs `09`'s "5+".
**19.** 🔧 `z-master` milestone labels off by a month.

---

## Remaining actions after this batch

**Decisions still needed (Michael):**
- #4 merchant-of-record / RFC / IVA — the go-live blocker.
- #5 boost price floor (≥300 vs $199/$79).

**Mechanical fixes still pending:**
- #6 public "dating" → "grupos" copy (live roadmap html).
- #8 unify phase numbering (docs ↔ live site).
- #3/#1 rebuild `b–g` + `z-master` numbers on the prepaid/referral model; add their banners.
- #10 `leads` migration + owner; #11 `edit_token` resolver endpoint.
- #14–19 currency labels, z-master totals, descubre orphan, naming, Smart Search slot.

**Done this batch:** #1/#2/#3-framework resolved by the two decisions; #9 spec bugs
fixed; `09` corrected; GTM notes added; `04/05/06/PRD-revenue` bannered; this record
persisted.
