# Payments Rail — Build Spec (one rail, three products)

*2026-07-24. The concrete engineering spec for the self-serve payment rail that all
monetization rides: the **Página** premium tier, the **Destacado** boost (directory
+ fiesta scopes), and later the **saldo** wallet. One PSP pay-link, one signed
webhook, one grant mechanism. No salesperson, no collections, no recurring billing.

Implements the capture design in
[`../financials/phase2-revenue-capture.md`](../financials/phase2-revenue-capture.md)
and the product/trust rules in
[`../business/research/11-storefront-freemium-monetization.md`](../business/research/11-storefront-freemium-monetization.md),
[`../business/research/12-seed-then-monetize-playbook.md`](../business/research/12-seed-then-monetize-playbook.md),
and [`../PRD-phase3-fiestas.md`](../PRD-phase3-fiestas.md) §7b.

**Deploy discipline (non-negotiable — see the `deploy` skill):** every migration in
§2 ships and applies to D1 (**staging → prod**) *before* any function in §4 that
reads its columns/tables. A function must never ship ahead of its table.*

---

## 1. The model in one picture

```
Vendor (already free-listed in negocios, seeing free leads) taps a paid action
        │
        ▼  POST /api/pay/create  { negocio, product }   ← auth = tokenized edit link
   We call the PSP (Mercado Pago / Conekta) → create a Link de Pago (checkout URL)
        │   and INSERT a `pagos` row (status=pending, amount, product, grants_days)
        ▼
   Vendor pays:  ► OXXO cash (reference, may settle days later)   ← mandatory rail
                 ► card / SPEI
        │
        ▼  PSP → POST /api/pay/webhook   (signed)
   Verify signature → look up psp_ref (idempotent) → status=paid, paid_at
        → APPLY GRANT: set negocios.premium_until  OR  INSERT boosts(scope,…)
        ▼
   The paid feature is live. No human confirmed the sale. Nothing to collect.
```

Every product is just `(target negocio, product, duration) → set a flag / insert a
row`. The webhook is the only thing that grants; the client is never trusted.

## 2. Schema (migrations — ship these first)

Next free indices continue `src/migrations/00NN_*.sql`. `negocios` already exists
(0017, reviewed in 0022); we extend it, we don't fork it.

### 2.1 `pagos` — the order/payment ledger (idempotency + audit)

```sql
-- 00NN_pagos.sql
CREATE TABLE pagos (
  id          INTEGER PRIMARY KEY,
  psp         TEXT NOT NULL,                 -- 'mercadopago' | 'conekta'
  psp_ref     TEXT NOT NULL,                 -- external order/payment id
  negocio_id  INTEGER NOT NULL,              -- → negocios.id
  product     TEXT NOT NULL,                 -- 'pagina' | 'boost_dir' | 'boost_fiesta' | 'saldo'
  amount_mxn  INTEGER NOT NULL,              -- pesos, integer
  rail        TEXT,                          -- 'oxxo' | 'card' | 'spei' (known at/after pay)
  grants_days INTEGER,                       -- season length to grant on paid (e.g. 30, 180)
  status      TEXT NOT NULL DEFAULT 'pending', -- 'pending' | 'paid' | 'expired' | 'failed'
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  paid_at     TEXT
);
CREATE UNIQUE INDEX ux_pagos_psp_ref ON pagos (psp, psp_ref);  -- webhook idempotency
CREATE INDEX ix_pagos_negocio ON pagos (negocio_id, status);
```

The **unique `(psp, psp_ref)`** is the idempotency guarantee: PSP webhooks retry, and
the grant must apply exactly once.

### 2.2 `negocios` — add the Página flag

```sql
-- 00NN_negocios_premium.sql
ALTER TABLE negocios ADD COLUMN premium_until TEXT;   -- nullable; NULL/past = free tier
```

A page is premium or not → a single-valued column is correct here (unlike boosts,
which are multi-scope → their own table).

### 2.3 `boosts` — scoped positioning (directory + fiesta)

```sql
-- 00NN_boosts.sql
CREATE TABLE boosts (
  id         INTEGER PRIMARY KEY,
  negocio_id INTEGER NOT NULL,               -- → negocios.id
  scope      TEXT NOT NULL,                  -- 'directory' | 'fiesta'  (priced differently)
  starts     TEXT NOT NULL DEFAULT (datetime('now')),
  expires    TEXT NOT NULL,
  pago_id    INTEGER                         -- → pagos.id (provenance)
);
CREATE INDEX ix_boosts_active ON boosts (scope, expires);
```

Two scopes because the fiesta recommendation is a distinct, higher-intent, higher-priced
placement than the generic directory boost (PRD-phase3 §7b) — and a vendor may hold one
without the other. (A single `boosted_until` column would conflate them; don't.)

### 2.4 `promociones` — the deals feed (the weekly-habit surface)

```sql
-- 00NN_promociones.sql
CREATE TABLE promociones (
  id          INTEGER PRIMARY KEY,
  negocio_id  INTEGER NOT NULL,              -- → negocios.id
  titulo      TEXT NOT NULL,
  descripcion TEXT,
  descuento   TEXT,                          -- free text: "2x1", "-20%", "$50"
  starts      TEXT NOT NULL DEFAULT (datetime('now')),
  expires     TEXT NOT NULL,                 -- self-expiring → stays fresh with no staff
  active      INTEGER NOT NULL DEFAULT 1,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX ix_promos_live ON promociones (active, expires);
```

Gating (product decision, doc 11 §6): **free tier = 1 active promo** (deliberately, to
seed the deals-feed habit across all businesses), **premium = unlimited**. The
1-promo-free choice is what gives `/api/ofertas` enough supply to be a real weekly
surface from day one; revisit if it cannibalizes premium.

### 2.5 `negocio_media` — the gallery (the infra-cost feature)

```sql
-- 00NN_negocio_media.sql
CREATE TABLE negocio_media (
  id         INTEGER PRIMARY KEY,
  negocio_id INTEGER NOT NULL,               -- → negocios.id
  url        TEXT NOT NULL,                  -- R2 object key
  sort       INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX ix_media_negocio ON negocio_media (negocio_id, sort);
```

Free tier exposes only `sort = 0` (one photo); premium exposes the full gallery. Media
is the one feature with real marginal cost (R2 storage/egress) — price the Página tier
to cover it (doc 11 §5).

## 3. Grant logic (the only place money becomes features)

On a **verified, paid** webhook, map `product → grant`:

| product | grant applied | read by |
|---|---|---|
| `pagina` | `negocios.premium_until = max(now, premium_until) + grants_days` | `GET /api/negocios` field-gating; `/api/ofertas` promo cap |
| `boost_dir` | `INSERT boosts(scope='directory', expires=now+grants_days)` | directory ranking |
| `boost_fiesta` | `INSERT boosts(scope='fiesta', expires=now+grants_days)` | fiesta match ranking (PRD-phase3 §7) |
| `saldo` | credit wallet (deferred — phase-2 secondary) | lead-unlock |

**Grant rules:**
- Extend, don't overwrite: `premium_until = max(now, existing) + days` so re-ups stack.
- Grant strictly from the **paid** webhook; `pending`/`failed` grant nothing.
- **Verify amount**: the webhook's paid amount must match the `pagos.amount_mxn` for
  that `psp_ref` before granting (guards tampering / wrong-link reuse).

## 4. Endpoints (Cloudflare Pages Functions, `functions/api/`)

Same posture as existing public writes (`api/negocios`, `api/sugerencias`): honeypot
where relevant, daily flood caps, `X-Robots-Tag: noindex`, `env.DB` binding.

### 4.1 `POST /api/pay/create`  (new)
- **Auth:** the vendor's tokenized edit link (the Phase-2 WhatsApp edit key) → resolves
  to a `negocio_id`. No account/login.
- **Body:** `{ product, term }` (term → `grants_days`, e.g. `30` | `180`).
- **Action:** price from a server-side table (never client), call PSP to create a Link
  de Pago (OXXO + card + SPEI enabled), `INSERT pagos(status='pending', …)`, return the
  checkout URL. Prices are server-owned and A/B-testable (phase-2 capture §3).
- **Returns:** `{ checkout_url }`.

### 4.2 `POST /api/pay/webhook`  (new — the critical one)
- **Verify the PSP signature** (reject unsigned/invalid → 401). This is the trust boundary.
- **Idempotent:** upsert on `(psp, psp_ref)`; if already `paid`, return 200 without
  re-granting (webhooks retry; OXXO can fire late).
- On `order.paid` / `charge.paid`: set `status='paid'`, `paid_at`, `rail`; **verify
  amount**; **apply the §3 grant** in the same transaction.
- Always return **200** on a handled event so the PSP stops retrying.
- Never grant from any other source. The client cannot self-grant.

### 4.3 `GET /api/negocios`  (extend the existing function)
- Already returns active businesses. Extend: expose premium-only fields (full gallery,
  extra links, catalog) **only when `premium_until > now`**; free rows return the free
  subset (current behavior + `sort=0` photo).
- **Ranking:** active `boosts(scope='directory')` first, then `verified DESC, id DESC`
  (current order preserved as the tiebreak). Promoted rows must be **labeled**
  `destacado: true` in the payload (the trust rule — never disguise paid as organic).

### 4.4 `GET /api/ofertas`  (new — the deals feed / weekly habit)
- Public, edge-cached (~60s, like `api/negocios`). Returns live promotions
  (`active=1 AND expires>now`, joined to active `negocios`), filterable by `zona` /
  route proximity (reuse the places/proximity pipeline).
- This is the consumer surface that gives the directory a weekly reason-to-open
  (doc 11 §4). Ship it as soon as `promociones` has supply.

### 4.5 Fiesta match  (PRD-phase3 §7, reads this rail)
- The needs-list match reads `negocios` + active `boosts(scope='fiesta')` to rank;
  labels promoted vendors `destacado`; keeps every relevant vendor visible (paid buys
  position, not existence); logs a `leads` row on WhatsApp handoff.

## 5. Security & correctness checklist

- [ ] **Signature verification** on the webhook (the whole rail's integrity hinges here).
- [ ] **Idempotency** via unique `(psp, psp_ref)` — grant exactly once across retries.
- [ ] **Amount check** — paid amount must equal the pending order's amount.
- [ ] **Server-side pricing** — never accept a client-supplied price.
- [ ] **OXXO async reality** — order stays `pending` until cash settles (can be days);
      UI shows "pendiente de pago"; grant only on the paid webhook.
- [ ] **Grant only from `paid`** — no grant on create/pending/failed.
- [ ] **PSP secret + webhook signing key** as Cloudflare secrets (redeploy to apply —
      see the `cloudflare-account` note); never in the repo or `wrangler.toml`.
- [ ] **No PII leak** in `GET` reads (same discipline as `api/negocios` GET today).

## 6. Build order (MVPs — each shippable, schema-first)

| MVP | Ships | Migrations first | Then functions |
|---|---|---|---|
| **1 — Página** | Premium page tier (single flag) | `pagos`, `negocios.premium_until` | `pay/create`, `pay/webhook`, extend `negocios` GET |
| **2 — Ofertas** | Deals feed = weekly habit | `promociones`, `negocio_media` | `api/ofertas`, media upload to R2, gated fields |
| **3 — Boosts** | Directory + fiesta positioning | `boosts` | boost products in `pay/create`; ranking in `negocios` GET + fiesta match |
| **4 — Saldo** | Wallet + lead-unlock (deferred) | `wallet`, `wallet_ledger` | recarga product; lead-unlock spend |

MVP-1 is the smallest end-to-end proof of the *entire* rail (create → PSP → webhook →
grant). Everything after is another product on the proven rail, not new plumbing.

## 7. Open decisions (decide at build with re-verified 2026 pricing)

1. **PSP:** Mercado Pago vs Conekta — OXXO fee (MP 3.79%+$4) vs Conekta's $5.4 cash
   minimum; both must expose OXXO + card + SPEI on one Link de Pago (phase-2 §14).
2. **Free-promo cap:** 1 free active promo (habit-seeding) vs 0 (premium-only). Start
   at 1; measure cannibalization.
3. **Fiesta-boost quality gate:** the rating/verified floor a vendor must clear to
   *buy* `boost_fiesta` (PRD-phase3 §7b) — set the threshold at build.
4. **R2 media pricing:** measure real storage/egress per premium page; set the Página
   price to cover it + margin (doc 11 §5).

## 8. One-line summary

> One PSP pay-link, one signed idempotent webhook, one grant switch — `pagina` sets a
> column, `boost_*` inserts a scoped row, all from OXXO/card/SPEI with no human in the
> loop. Ship the migrations before the functions, prove the whole rail with the Página
> MVP, then hang every other price-tag on it. The three monetization products are not
> three builds — they are one rail with three grants.
