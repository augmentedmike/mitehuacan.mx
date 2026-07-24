# Payments Rail — Build Spec (one rail, three products)

*2026-07-24. The concrete engineering spec for the **self-serve** payment rail: the
**Página** premium tier, the **Destacado** boost (directory + fiesta scopes), and later
the **saldo** wallet. One PSP pay-link, one signed webhook, one grant mechanism, no
recurring billing.*

> **GTM note (2026-07-24):** This self-serve/webhook rail is the **secondary** collection
> channel. The **primary** path for paid deals is a **human salesperson close with digital
> collection** (SPEI / OXXO / bank) recorded against the contract — the legacy
> `0014_sponsors_contracts` ledger. The two ledgers, `0014 payments` (sales-closed) and
> `pagos` (self-serve, below), **must be reconciled into one source of truth.** Growth
> stays organic/free. See
> [`../financials/revenue-model-of-record.md`](../financials/revenue-model-of-record.md) §2.1.

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
        → APPLY GRANT: set negocios.premium_until / boosted_until / fiesta_boosted_until
        ▼
   The paid feature is live. No human confirmed the sale. Nothing to collect.
```

Every product is just `(target negocio, product, duration) → set a column`. The webhook
is the only thing that grants; the client is never trusted.

## 2. Schema (migrations — ship these first)

Next free indices continue `src/migrations/00NN_*.sql`. `negocios` already exists
(0017, reviewed in 0022); we **extend it and reuse its sibling tables** — we do not fork.

**What already ships in `negocios` (migration 0017) — reuse, don't recreate:**
`boosted_until` (the directory-boost grant), `edit_token` (UNIQUE — the tokenized
auth key), and the sibling `negocio_photos(negocio_id, url, sort, created_at)` (the
gallery). Earlier drafts of this spec proposed new `boosts` and `negocio_media`
tables — **dropped**: they would orphan the shipped `boosted_until` column and
duplicate `negocio_photos`.

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
the grant must apply exactly once. **Reconcile with the `0014 payments` ledger** (the
sales-closed path) so "who paid what" has one source of truth (GTM note above).

### 2.2 `negocios` — add the Página flag

```sql
-- 00NN_negocios_premium.sql
ALTER TABLE negocios ADD COLUMN premium_until TEXT;   -- nullable; NULL/past = free tier
```

A page is premium or not → a single-valued column, matching the shipped `boosted_until`
pattern.

### 2.3 Directory & fiesta boost — reuse `boosted_until`, add a fiesta column

`negocios` **already has `boosted_until`** (0017) — the directory-boost grant, which
PRD-phase2/3 already tell readers to use. The fiesta recommendation is a distinct,
higher-intent, higher-priced placement (PRD-phase3 §7b), so add a **second single-valued
column** rather than a separate table:

```sql
-- 00NN_negocios_fiesta_boost.sql
ALTER TABLE negocios ADD COLUMN fiesta_boosted_until TEXT;   -- nullable; the fiesta-scope boost
```

Directory ranking reads `boosted_until`; the fiesta match reads `fiesta_boosted_until`.
A vendor may hold one without the other. (A separate `boosts` table was considered and
dropped — it would orphan the shipped `boosted_until` and diverge from PRD-phase2/3.)

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

Gating (product decision, doc 11 §6): **free tier = 1 active promo** (to seed the
deals-feed habit across all businesses), **premium = unlimited**. Revisit if it
cannibalizes premium.

### 2.5 Gallery — reuse the shipped `negocio_photos`

The shipped schema **already has `negocio_photos(negocio_id, url, sort, created_at)`**
(migration 0017) — exactly a gallery. **Reuse it; do not create a new `negocio_media`
table.** Free tier exposes only `sort = 0` (one photo); premium (`premium_until > now`)
exposes the full set. Media is the one feature with real marginal cost (R2
storage/egress) — price the Página tier to cover it (doc 11 §5).

## 3. Grant logic (the only place money becomes features)

On a **verified, paid** webhook, map `product → grant` (all grants are column writes):

| product | grant applied | read by |
|---|---|---|
| `pagina` | `negocios.premium_until = max(now, premium_until) + grants_days` | `GET /api/negocios` field-gating; `/api/ofertas` promo cap |
| `boost_dir` | `negocios.boosted_until = max(now, boosted_until) + grants_days` | directory ranking |
| `boost_fiesta` | `negocios.fiesta_boosted_until = max(now, fiesta_boosted_until) + grants_days` | fiesta match ranking (PRD-phase3 §7) |
| `saldo` | credit wallet (deferred — phase-2 secondary) | lead-unlock |

**Grant rules:**
- Extend, don't overwrite: `... = max(now, existing) + days` so re-ups stack.
- Grant strictly from the **paid** webhook; `pending`/`failed` grant nothing.
- **Verify amount**: the webhook's paid amount must match `pagos.amount_mxn` for that
  `psp_ref` before granting (guards tampering / wrong-link reuse).

## 4. Endpoints (Cloudflare Pages Functions, `functions/api/`)

Same posture as existing public writes (`api/negocios`, `api/sugerencias`): honeypot
where relevant, daily flood caps, `X-Robots-Tag: noindex`, `env.DB` binding.

### 4.1 `POST /api/pay/create`  (new)
- **Auth:** the vendor's tokenized edit link (the shipped `negocios.edit_token`) →
  resolves to a `negocio_id`. No account/login. **Prereq:** the token→negocio resolver
  endpoint does not exist yet — it must be built (it also gates self-serve edit).
- **Body:** `{ product, term }` (term → `grants_days`, e.g. `30` | `180`).
- **Action:** price from a server-side table (never client), call PSP to create a Link
  de Pago (OXXO + card + SPEI), `INSERT pagos(status='pending', …)`, return checkout URL.
- **Returns:** `{ checkout_url }`.

### 4.2 `POST /api/pay/webhook`  (new — the critical one)
- **Verify the PSP signature** (reject unsigned/invalid → 401). The trust boundary.
- **Idempotent:** upsert on `(psp, psp_ref)`; if already `paid`, return 200 without
  re-granting (webhooks retry; OXXO can fire late).
- On `order.paid` / `charge.paid`: set `status='paid'`, `paid_at`, `rail`; **verify
  amount**; **apply the §3 grant** in the same transaction.
- Always return **200** on a handled event so the PSP stops retrying.
- Never grant from any other source.

### 4.3 `GET /api/negocios`  (extend the existing function)
- Already returns active businesses. Extend: expose premium-only fields (full gallery,
  extra links, catalog) **only when `premium_until > now`**; free rows return the free
  subset (current behavior + `sort=0` photo).
- **Ranking:** `boosted_until > now` first, then `verified DESC, id DESC` (current order
  preserved as the tiebreak). Promoted rows must be **labeled** `destacado: true` (the
  trust rule — never disguise paid as organic).

### 4.4 `GET /api/ofertas`  (new — the deals feed / weekly habit)
- Public, edge-cached (~60s, like `api/negocios`). Returns live promotions
  (`active=1 AND expires>now`, joined to active `negocios`), filterable by `zona` /
  route proximity. The consumer surface that gives the directory a weekly reason-to-open
  (doc 11 §4). Ship as soon as `promociones` has supply.

### 4.5 Fiesta match  (PRD-phase3 §7, reads this rail)
- The needs-list match reads `negocios` + `fiesta_boosted_until > now` to rank; labels
  promoted vendors `destacado`; keeps every relevant vendor visible (paid buys position,
  not existence); logs a `leads` row on WhatsApp handoff. **Note:** the `leads` table is
  referenced by PRD-phase2 §7 and PRD-phase3 but **not yet created** — assign a migration.

## 5. Security & correctness checklist

- [ ] **Signature verification** on the webhook (the whole rail's integrity hinges here).
- [ ] **Idempotency** via unique `(psp, psp_ref)` — grant exactly once across retries.
- [ ] **Amount check** — paid amount must equal the pending order's amount.
- [ ] **Server-side pricing** — never accept a client-supplied price.
- [ ] **OXXO async reality** — order stays `pending` until cash settles (can be days);
      UI shows "pendiente de pago"; grant only on the paid webhook.
- [ ] **Grant only from `paid`** — no grant on create/pending/failed.
- [ ] **PSP secret + webhook signing key** as Cloudflare secrets (redeploy to apply);
      never in the repo or `wrangler.toml`.
- [ ] **Ledger reconciliation** — `0014 payments` (sales-closed) and `pagos` (self-serve)
      unified into one reporting source (GTM note).
- [ ] **No PII leak** in `GET` reads (same discipline as `api/negocios` GET today).

## 6. Build order (MVPs — each shippable, schema-first)

| MVP | Ships | Migrations first | Then functions |
|---|---|---|---|
| **1 — Página** | Premium page tier (single flag) | `pagos`, `negocios.premium_until` | token resolver, `pay/create`, `pay/webhook`, extend `negocios` GET |
| **2 — Ofertas** | Deals feed = weekly habit | `promociones` (reuse `negocio_photos`) | `api/ofertas`, media upload to R2, gated fields |
| **3 — Boosts** | Directory + fiesta positioning | `negocios.fiesta_boosted_until` (dir uses shipped `boosted_until`) | boost products in `pay/create`; ranking in `negocios` GET + fiesta match |
| **4 — Saldo** | Wallet + lead-unlock (deferred) | `wallet`, `wallet_ledger`, `leads` | recarga product; lead-unlock spend |

MVP-1 is the smallest end-to-end proof of the *entire* rail (create → PSP → webhook →
grant). Everything after is another product on the proven rail, not new plumbing.

## 7. Open decisions (decide at build with re-verified 2026 pricing)

1. **Merchant of record / RFC / IVA** — *first-order blocker.* This rail books revenue
   through a PSP and (for SPEI/card) issues facturas + remits IVA. Which registered
   entity holds the account? Resolve before any line goes paid
   (revenue-model-of-record §7).
2. **PSP:** Mercado Pago vs Conekta — OXXO fee vs Conekta's cash minimum; both must
   expose OXXO + card + SPEI on one Link de Pago.
3. **Free-promo cap:** 1 free active promo (habit-seeding) vs 0 (premium-only). Start at
   1; measure cannibalization.
4. **Fiesta-boost quality gate:** the rating/verified floor to *buy* `boost_fiesta`
   (PRD-phase3 §7b).
5. **R2 media pricing:** measure real storage/egress per premium page; set the Página
   price to cover it + margin (doc 11 §5).

## 8. One-line summary

> One PSP pay-link, one signed idempotent webhook, one grant switch — `pagina`,
> `boost_dir`, `boost_fiesta` each set a **column on the shipped `negocios`** (reusing
> `boosted_until` and `negocio_photos`), all from OXXO/card/SPEI. This is the
> **secondary**, self-serve channel; the primary path is a salesperson close with digital
> collection against the `0014` ledger — reconcile the two ledgers. Ship migrations
> before functions; prove the rail with the Página MVP.
