## Phase E — Home Services Marketplace

*Launches month 13. Request-to-provider matching for home services.*

**Product:** Residents request "I need a plumber/electrician/painter/cleaner." 
Professionals receive leads and pay for access.

**Price:**
- Monthly membership: $400/mo (10 leads included, then $50/lead)
- Pay-per-lead: $100/lead (no membership)
- Featured provider: $600/mo (appears first in results)

**Market:** ~2,000+ registered service professionals in Tehuacán area (DENUE
categories: talleres, servicios de reparación, construcción).

| Month | Active Providers | Monthly Revenue |
|---|---|---|
| 13 | 15 | $6,000 |
| 14 | 22 | $8,800 |
| 15 | 30 | $12,000 |
| 16 | 38 | $15,200 |
| 17 | 45 | $18,000 |
| 18 | 52 | $20,800 |
| 19 | 60 | $24,000 |
| 20 | 68 | $27,200 |
| 21 | 75 | $30,000 |
| 22 | 82 | $32,800 |
| 23 | 88 | $35,200 |
| 24 | 95 | $38,000 |

**Year 2 total (months 13-24): $232,000**

**Assumptions:** $400/mo average per provider (mix of membership and PPL). 95 providers
by month 24 = ~5% of addressable market. Feature takes ~3 weeks to build (D1 + API +
simple request form).

---

## Reconciliation from adversarial review [→ full review](challenges/phase-e--home-services-marketplace.md)

| Assumption | Projection | Adversarial challenge | Adjusted range |
|---|---|---|---|
| Platform-based trust model | 95 providers by month 24 | In Mexico, home services are sourced through personal networks (family, neighbors, compadres), not platforms. [1] | Trust barrier is structural |
| $400/mo membership | Providers pay for leads | A plumber making $8-15K/mo paying $400/mo (3-5% of revenue) for unproven leads from a new platform is a hard sell. PPL at $100 feels safer but needs volume. [2] | $250-400/mo avg |
| Month 13 launch dependency | User base must support service requests | Depends on Phase A-C user adoption. If Phase A is 55-65% of projection (see Phase A reconciliation), user base grows slower → fewer service requests → less provider value. | Month 16-18 launch more realistic |
| 2,000+ addressable professionals | DENUE formal count | Informal service professionals (plumbers, painters, cleaners without RFC) are not in DENUE and harder to reach/sell. [3] | 1,000-1,500 addressable |

**Net effect:** 50-60 providers by month 24 (not 95). Year 2 revenue $120K-150K (not $232K). Delayed launch likely.

[1] Adversarial difference #6: Trust networks replace advertising networks. "My comadre recommended this plumber" beats any platform listing.
[2] Adversarial difference #5: Informal economy means many professionals operate without formal registration and may not trust digital platforms.
[3] Adversarial difference #1: Cash economy — many providers expect cash payment and may not have bank accounts for subscription billing.

---

