# Storefront Freemium — Monetizing the Directory Without Subscriptions

*2026-07-24. Design + validation for a freemium **business page** product: every
store gets a page; free tier drives coverage, paid features (gallery, promotions,
catalog) fund the infrastructure and build a slow up-trending revenue stream.

This idea is good and already half-present on the roadmap (Phase 4 "premium
profiles"). But it collides with a hard constraint the financials' original
Phase-B framing missed — so this doc **reconciles it into the cash-native form**
and, more importantly, shows it does something the revenue alone doesn't: it gives
the directory the **weekly habit** the growth model was missing.

Supersedes the **$300/mo subscription** framing in
[`financials/projections/b-business-directory-and-premium-profiles.md`](../../financials/projections/b-business-directory-and-premium-profiles.md).
Grounded in [`financials/phase2-revenue-capture.md`](../../financials/phase2-revenue-capture.md)
(the "never subscriptions / one-shot prepaid" rail), the payments research
(`financials/research/payments-cash-economy-2026.md`), and
[`10-network-effects-and-organic-growth.md`](10-network-effects-and-organic-growth.md)
(the weekly-habit gap and the "one city completely" moat).*

---

## 1. The idea, stated

Every business in the directory (`negocios`) gets its own **page**. A **freemium
ladder** governs what the page can show:

- **Free** keeps the page useful enough that coverage stays complete (the moat).
- **Paid features** (photo gallery, promotions/discounts, product/menu catalog,
  links, appear-first) are worth money to the business and cost us money to serve.
- Priced so the paid tier **covers the added infrastructure + a margin**, producing
  a **slow up-trending revenue stream** — bootstrapped, no VC, no sales team.

The instinct is correct. Two things have to be true for it to work here, and one
of them contradicts how the financials originally modeled it.

## 2. The collision: this is NOT a subscription

The original Phase-B projection priced this at **$300 MXN/month per profile** and
assumed self-serve adoption + 15% churn. Both the Puebla adversarial review and the
Phase-2 revenue-capture decision **kill that framing**:

- *"'Subscription' is a foreign concept … self-serve adoption for paid digital
  products is near zero among micro-businesses"* (Phase-B challenge).
- *"**Never** monthly subscription — no micro-business subscription culture in this
  market"* (Phase-2 capture §1, a hard **never**).
- Real churn on a monthly digital product for MX micro-business: **30–40%**, not
  15% — because recurring billing in a cash economy is a monthly re-decision, and
  each one is a collections event we have no staff for.

**"Slow up-trending revenue stream" reads as MRR.** MRR is precisely the mechanism
this market resists hardest. Keep the goal; change the mechanism.

## 3. The fix: sell **time**, not a subscription

Map the page product onto the **same one-shot prepaid rail** the boost already uses:

```
Business (already free-listed, seeing free views/leads) taps "Mejora tu página"
        ▼
WhatsApp pay-link (OXXO cash / card / SPEI) for a fixed PREPAID SEASON
        ▼
Webhook verifies → sets negocios.premium_until = now + 30d (or 6 months)
        ▼
Premium features unlock automatically. No salesperson, no invoice, no collection.
        ▼
On expiry → page auto-downgrades to FREE tier (features LOCKED, nothing deleted)
        ▼
Re-up is a fresh voluntary purchase — never a failed charge, never a cobranza visit
```

Why this preserves the model:
- **No recurring billing, ever.** An expiry is not a churn event requiring a
  collections call; it is a silent downgrade the business re-buys when it wants to.
- **Same rail as the boost.** `premium_until` is the sibling of the already-speced
  `boosted_until`; one webhook receiver serves both. Zero new go-to-market.
- **Cash-native re-up.** Prepaid seasons match how these businesses already buy
  advertising (perifoneo, flyers, radio — all one-shot; see marketing-plan §6).

### Where the "up-trend" actually comes from

Not from per-customer MRR retention. From three stacked, cash-compatible sources:

1. **Cohort stacking** — more of the 28,727 businesses cross free→paid as directory
   density and resident usage grow.
2. **Price rising with sell-through** — founding rate locked for early adopters;
   new pages cost more as the map fills and traffic is provable (vision doc's
   "digital real estate" logic, made self-serve).
3. **Re-up rate on prepaid seasons** — the honest analogue of retention, but
   voluntary and fee-free, driven by the per-page stats + promotions ROI (§6).

## 4. Why this is more than revenue: it fills the weekly-habit gap

Research §5 (the frequency ladder) named a hole: the directory is **weekly-value at
best and has no pull** — nobody opens a business directory for fun, so attention
never transfers from the daily transport habit to the monetizable surface.

**Promotions/discounts are the fix.** *"Ofertas cerca de ti / en tu ruta hoy"* is a
reason for a resident to open the app weekly, and it is the single freemium feature
a cash micro-business actually understands — because the ROI is **foot traffic,
same-day, in cash**, not an abstract "impressions" number a SaaS dashboard sells.

So the store-page product does double duty:
- **For the business:** a paid feature whose value is legible in pesos through the
  door (the only ROI that converts a cash operator).
- **For the platform:** a **weekly consumer habit** (a deals feed) that thickens the
  directory into something people browse — the browse-time surface the loop needs.

This is why promotions should arguably lead the paid feature set, not the static
product catalog: promotions are self-expiring (stay fresh with no staff) and they
generate the consumer-side habit; catalogs go stale and generate none.

## 5. The infra-cost alignment (why "freemium pays for infra" is literally true)

The stack is cheap-by-default (Cloudflare Pages + D1 + Workers). The one feature
with a real **marginal** cost is **media**: photo galleries = R2 storage +
egress. That is *also* one of the top paid features.

> Price the media/gallery tier to cover its own storage + bandwidth + a margin, and
> the freemium model is **self-funding by construction** — the feature that costs
> money is the feature that's paid for. Exactly the "freemium pays for the
> additional infrastructure" design goal, made structural rather than hopeful.

Everything else (promotions, catalog text, links, appear-first) is near-zero
marginal cost — effectively ~100%-margin digital goods, the same profile as the
boost (Phase-2 capture §4). So the blended economics are strong; the constraint is
willingness-to-pay, not cost.

## 6. The freemium line (tune carefully — the moat depends on it)

| Tier | What it includes | Purpose |
|---|---|---|
| **Gratis** | Listing, category, zona, WhatsApp/phone, hours, **1 photo**, map pin, appear in search | **Keep coverage complete.** The moat is *every* business listed (research §6); a stingy free tier kills density and hands the market back to Facebook |
| **Página** (prepaid season) | Photo **gallery**, **promociones/cupones**, product/menu **catálogo**, FB/IG/web links, "abierto ahora", richer description | The digital storefront — the up-trending stream; promotions drive the weekly habit (§4) |
| **Destacado** (boost, Phase-4) | Appear **first** in category+zona, **Recomendado** badge, promo pushed to the deals feed / route views | Scarcity/position product — the already-speced one-shot boost |

Design rules:
- **Free must stay genuinely useful.** Density (complete coverage) is worth more
  than squeezing the free tier; the moat is coverage, not the paywall.
- **Don't make paid a features-checklist; make it a customer-count promise.** What
  converts a cash operator is "más clientes," not "unlock analytics." Frame every
  paid feature as foot traffic / a ringing WhatsApp.
- **Self-maintained forever** via the tokenized WhatsApp edit link (the Phase-2
  pattern) — no staff touches a page after creation.
- **Prefer self-expiring content (promotions) over static (catalogs)** early, so
  freshness survives with zero staff.

## 7. Honest challenges (the adversarial pass)

| Challenge (from Phase-B review + payments research) | Response under this design |
|---|---|
| "Self-serve paid adoption is near zero; every signup needs hand-holding" | Mitigated, not solved: the business is **already free-listed and seeing free views/leads** before any ask (warm, not cold), and the pay is one-shot OXXO — but this remains a **pilot question**, same as the boost. Measure it; don't assume it |
| "$300/mo vs a free Facebook page — value prop is thin" | Correct — which is why we **don't** compete with FB on profile-hosting. We sell (a) transit-adjacency discovery, (b) a **deals feed with a weekly audience** FB's algorithm doesn't give a tiendita, (c) appear-first scarcity. Not "a page," but "clientes que ya vienen pasando" |
| "30–40% churn on monthly digital products" | Sidestepped: **no monthly product exists.** Expiry → silent downgrade → voluntary re-up. Re-up rate replaces churn and carries no collections cost |
| Content goes stale (catalogs) | Lead with self-expiring promotions; catalog is optional; tokenized self-edit keeps it the owner's job |
| Absolute revenue is modest | **True and acceptable.** This is an infra-covering, ramen-profitable, compounding stream — matching the whole no-VC ethos. It is not a venture outcome and should not be modeled as one |

## 8. What's measurable (the pilot extension)

Fold into the boost pilot (Phase-2 capture §6) — same cohort, one more product:

- **free→Página conversion** of active listings (the hinge, like boost-conversion).
- **Re-up rate** on prepaid seasons (the honest retention analogue).
- **Promotions posted per premium page / month** (is the weekly-habit engine fed?).
- **Deals-feed opens per resident / week** (did the directory get a heartbeat?).
- **Media cost per premium page** vs price (is the infra-alignment §5 holding?).
- **OXXO-vs-card split**, price elasticity across season tiers.

## 9. Data model note (extend, don't fork)

`negocios` already holds the profile fields (photos handled via a media table).
Add the season flag as the sibling of the boost hook:

```
negocios: ...existing..., premium_until (nullable), boosted_until (nullable)
promociones ( id, negocio_id → negocios.id, text, discount, starts, expires, active )
negocio_media ( negocio_id, url (R2), sort )          -- gallery; gated by premium_until
```

One webhook receiver sets `premium_until` / `boosted_until` from the signed PSP
event. The public `GET /api/negocios` reads `premium_until` to decide which fields
to expose; a new `GET /api/ofertas` powers the deals feed (active, unexpired
promotions, by zona/route). No schema fork; same rail.

## 10. One-line summary

> Give every store a page; keep the free tier strong enough to hold complete local
> coverage (the moat); sell the rich page as a **prepaid season, not a
> subscription** (auto-downgrade + voluntary re-up = no churn, no collections);
> lead the paid features with **promotions**, because they convert cash operators
> on same-day foot traffic **and** give the directory the weekly consumer habit the
> growth model was missing; and price the **media** tier to cover its own R2 cost so
> the freemium ladder funds its own infrastructure. Slow, compounding,
> cash-native, self-serve — the up-trending stream you wanted, minus the one
> mechanism this market rejects.
