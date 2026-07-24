# PRD — Phase 3: Fiestas (the invitation loop)

**Status:** Draft v1
**Owner:** Michael
**Date:** 2026-07-24
**Depends on:** Phase 1 (transport, live) · Phase 2 (fiesta-vendor directory —
`negocios`, self-serve `/directorio/alta`, live)
**Feeds:** Phase 4 (self-serve boosts = first revenue) · every later section (the
plan-a-thing graph reuses this loop)
**Grounded in:** [`business/research/10-network-effects-and-organic-growth.md`](business/research/10-network-effects-and-organic-growth.md)
(why this is the keystone) · [`PRD-phase2-fiesta-vendor-directory.md`](PRD-phase2-fiesta-vendor-directory.md)
(the supply this consumes) · [`business/research/09-organic-phase-reorder.md`](business/research/09-organic-phase-reorder.md)
(phase order) · live roadmap `build/combis/roadmap/index.html` (Phase 2–3, Oct–Dec 2026)

---

## 1. Problem

Phase 2 seeds **supply** — fiesta vendors self-list via QR into `negocios`. But a
directory does not grow itself: listing a business is not a viral act, and a vendor
with no leads churns (the supply→demand gap, research §10). We have a faucet (combi
QR) and a moat-in-waiting (the directory), but **no viral loop** — nothing in the
live product recruits the next user as a native act of use.

Fiestas is the loop. A host plans a party and invites their people; **each
invitation is an acquisition event**, and each party is a burst of qualified vendor
demand. This is the one section on the roadmap that compounds. The Phase 2 PRD
explicitly deferred the consumer Fiestas tool as a non-goal — this PRD is that
tool, and it is the keystone the whole organic model rests on.

## 2. Strategic context — the invitation *is* the growth engine

- **Supply before demand before money.** Phase 2 built supply. This builds the
  demand that makes supply valuable. Money (Phase 4 boosts) comes only after free
  leads visibly flow to already-listed vendors.
- **The invitation is the product, not a feature of it.** The RSVP page is the ad;
  the needs-list is the demand signal; the party is a live acquisition event. Every
  design decision below optimizes the loop, not the planning UI.
- **Why it is viral here specifically:** invite fan-out is huge (XV ~150, bautizo
  ~60, posadas whole colonias) and cycle time is short and year-round (the Mexican
  fiesta calendar is a built-in growth cadence). See research §8.1.
- **It rides WhatsApp, it does not replace it.** The invite spreads *through*
  WhatsApp; the vendor lead rings *on* WhatsApp. We inject structure a WhatsApp
  group cannot hold (10 caterers with prices/photos), then hand the conversation
  back to WhatsApp.

## 3. Goals

1. **Create a fiesta in under 3 minutes** from a phone, no app install, no account
   — WhatsApp number is the identity (same posture as Phase 2 vendors).
2. **Invitation that spreads itself.** A shareable RSVP link with a beautiful OG
   unfurl; forwarding it in WhatsApp *is* the distribution. Guest→host CTA on every
   RSVP page.
3. **Needs-list → vendor match.** The host states what the party needs; we surface
   matching `negocios` vendors by category + zona and hand off to the vendor's
   WhatsApp. This is the free lead that warms Phase-4 conversion.
4. **Review harvest at the party.** Post-fiesta one-tap prompt to guests who
   attended — bootstraps the verified-trust data moat (research §6).
5. **Instrument the loop end-to-end** so the viral coefficient is *measured*, not
   assumed (§11): scan/open → create → invite sent → RSVP → guest→host → lead sent →
   review captured.
6. **Reuse, don't fork.** Reuse the Eventos renderer, the `negocios` read API, the
   WhatsApp-identity + tokenized-edit-link pattern, and the OXXO/SPEI rail Phase 2
   lays down.

### Non-goals (Phase 3)

- Charging anyone. Fiestas is **free for hosts forever.** Boosts are Phase 4.
- Full event-management (seating, gift registry, RSVP+N meal choices) — later.
- Replacing WhatsApp group chat. We are the structured index it links out to.
- Building Tianguis/Empleos/Rentas. Do not cold-start other sections until this
  loop's k-factor is proven (research §10).
- Payments/rake on vendor bookings — impossible in cash; never attempted (research §8.3).

## 4. Users

| Persona | Description | Primary needs |
|---|---|---|
| **Host** | Resident planning a fiesta (XV, boda, bautizo, cumple, posada, graduación) | Make an invite fast; track who's coming; find trusted vendors for what's missing; all from a phone, all via WhatsApp |
| **Guest** | Anyone invited | Open the invite with no install; RSVP in one tap; (later) become a host themselves |
| **Vendor** | A `negocios` listing in a fiesta category | Receive free qualified leads on WhatsApp; feel the value before any paid ask |
| **Coordinator** (Michael) | Runs the platform | Concierge the first parties, route leads by hand, watch the loop's k-factor |

## 5. Surfaces

1. **Create-a-fiesta** — `/fiesta/nueva`: name, type (chips: XV, boda, bautizo,
   cumpleaños, posada, graduación, otro), date, zona/colonia, optional cover photo.
   WhatsApp number = host identity; returns a tokenized edit/manage link.
2. **The invitation / RSVP page** — `/f/<slug>`: the public artifact. Beautiful,
   install-free, OG-unfurling. Shows the party; one-tap RSVP (sí / tal vez / no,
   + party size); footer CTA "¿Vas a hacer una fiesta? Crea la tuya gratis."
3. **Needs-list → vendor match** — the host toggles what the party needs (catering,
   pastel, DJ, decoración, mobiliario, salón, foto…); we query `GET /api/negocios`
   (active, matching category + zona) and present vendors with a WhatsApp handoff.
4. **Manage page** (host, tokenized) — RSVP counts, resend invite, edit needs.
5. **Post-fiesta review prompt** — to guests who RSVP'd "sí," a one-tap rate of the
   vendors that served the party. Feeds `negocios` trust data.

## 6. The invitation loop (the core of this PRD)

```
Host creates fiesta  (/fiesta/nueva — WhatsApp = identity, <3 min)
        │  → returns share link  /f/<slug>  + tokenized manage link
        ▼
Host forwards /f/<slug> in WhatsApp to 10–150 guests   ◄── the distribution IS the forward
        │
        ▼
Guest opens invite (no install, OG unfurl: "XV de Sofía · Sáb 12 oct · Salón El Roble")
        │  one-tap RSVP (sí / tal vez / no  + cuántos)
        ▼
RSVP page footer: "¿Vas a hacer una fiesta? Crea la tuya gratis"  ──► guest becomes host
        │                                                                    │
        └──────────────────────── loop closes ◄──────────────────────────────┘
```

**Design rules (all trace to research §8.1 and the cash/local playbook §9):**
- **The invite is the ad.** OG image + title/date/venue must unfurl richly in
  WhatsApp and Facebook — a forwarded link that looks like a real invitation is the
  billboard. Invest here first.
- **Zero install for guests.** Web only. An install wall kills fan-out.
- **WhatsApp is the identity and the channel.** No passwords/email. The manage link
  is tokenized and returnable (same pattern as Phase 2 vendor edit link).
- **Guest→host CTA on every RSVP view.** The compounding term of the k-factor lives
  here; make it prominent, not a footnote.
- **Party QR (physical surface).** A printable "esta fiesta se organizó en
  mitehuacán — crea la tuya / califica a los proveedores" card the host can place at
  the party. 40+ warm prospects in one room = a live acquisition + review event.

## 7. Needs-list → vendor match (the demand the directory consumes)

- Host toggles needed categories; each maps to `negocios.category` /
  `category2` (the FIESTA_CATS set already defined in `functions/api/negocios.js`).
- Query `GET /api/negocios` filtered to `active = 1`, matching category, ranked
  `verified DESC` (and, once boosts exist, `boosted_until` first — Phase 4 hook).
- Present 3–8 vendors per category with photo, price_from, zona, and a **WhatsApp
  deep-link** prefilled with the party context ("Hola, organizo una fiesta el
  <fecha> en <zona>, ¿tienen disponibilidad?").
- Log a `lead` row on tap (vendor_id, fiesta_ref, channel) — this is the free lead
  that warms Phase-4 conversion and the metric that proves vendor value.
- **No rake, no in-app booking.** We produce the introduction; the deal happens in
  WhatsApp + cash. We monetize *position* later (Phase 4 boost), never the transaction.

### 7b. Paid placement in the recommendation (Phase-4 hook) — and the trust rule

The fiesta needs-list match is the **highest-intent demand on the platform**: a host
actively planning a party, in a specific category + zona + date. Placement here is
worth more than a generic directory boost — price it as bottom-of-funnel intent, not
an impression. This is the Phase-4 "Destacado en Fiestas" / "Recomendado" product
(Bodas.com.mx-style premium positioning into real purchase intent).

**But "recommendation" sells trust, and pay-to-play recommendation erodes the very
trust that makes it valuable — uniquely toxic in a viral-loop product, where a burned
host tells the WhatsApp group and the damage propagates backward through the growth
channel.** The design rule is therefore a hard separation:

| Signal | Source | Buyable? | Shown as |
|---|---|---|---|
| **Earned trust** | Guest reviews (§8), `verified`, completed-party count | **Never** | The "Recomendado" framing attaches *here* |
| **Paid position** | `boosted_until` (Phase-4 pay-link) | Yes | Labeled **"Destacado"** (promoted), visibly distinct |

Guardrails:
- **Free tier stays complete.** Every relevant vendor still appears in the match —
  paying buys *position*, not *existence*. Otherwise low-quality vendors buy their way
  in front of hosts and the loop rots.
- **Never sell the trust signal.** Sell placement; the word/label that implies
  curation stays tied to earned, unbuyable signals, or is explicitly marked promoted.
- **Quality-gate the paid slot (recommended).** A vendor may only *buy* Destacado
  after clearing a rating/verified floor. This protects the host experience and makes
  the paid product scarcer and more valuable — not a pay-any-junk-in auction.
- **Same rail as everything else:** OXXO/SPEI pay-link → webhook → `boosted_until`.
  Priced above the directory boost (higher intent). See
  [`financials/phase2-revenue-capture.md`](financials/phase2-revenue-capture.md) and
  [`business/research/11-storefront-freemium-monetization.md`](business/research/11-storefront-freemium-monetization.md).

## 8. Post-fiesta review harvest (the trust moat)

- Day after the fiesta date, prompt guests who RSVP'd "sí": *"¿Cómo estuvo la
  taquiza / el DJ de la fiesta de <host>?"* — one-tap star + optional photo.
- Only guests of that fiesta can review its vendors → structurally harder to fake
  than open reviews; this is the low-trust-market bootstrap (research §9.3).
- Reviews attach to `negocios` and raise `verified`/rating used in §7 ranking →
  data NFX: more parties → more reviews → better matches → more hosts.

## 9. Grupos — dating as an event-type experiment (low-cost appendix)

Per research §8.2, **do not build a dating vertical.** Instead, add **"grupo" /
"salida en grupo"** as a fiesta *type* (a 4–8 person outing). Reuses everything:
create → invite → RSVP → venue-as-vendor. The double-date safety/pairing mechanic
(each person brings a friend; the constrained side self-supplies with social cover)
is captured *without* a swipe app, a separate brand, or standalone-dating liability.

- Ship it as one more chip in the type selector + a slightly different copy tone.
- Gate any "meet new people" matching behind an explicit opt-in; default grupos are
  private, invite-only (same as any fiesta). No public singles directory in v1.
- **Kill/keep by data:** if grupos show organic creation and repeat use, graduate to
  its own surface; if not, it cost one chip. Do not invest further until the core
  fiesta k-factor (§11) is proven first.

## 10. Data model (extend, don't fork)

Reuse `negocios` (Phase 2) as-is for supply. Add a fiesta layer. Illustrative —
engineering owns final schema; **this PRD does not change code:**

```
fiestas
  id, slug (public), host_whatsapp, name, type (xv|boda|bautizo|cumple|posada|grad|grupo|otro),
  event_date, colonia, lat, lon (optional), cover_url,
  manage_token (tokenized host link), active, created_at, updated_at
rsvps
  id, fiesta_id, guest_whatsapp (nullable — anonymous RSVP allowed), status (si|talvez|no),
  party_size, became_host (bool — the loop-closure flag), created_at
fiesta_needs
  fiesta_id, category            -- what the party needs (maps to negocios categories)
leads
  id, fiesta_id, vendor_id (→ negocios.id), channel (whatsapp), created_at
                                  -- the free lead; Phase-2 §7 already anticipates this table
reviews
  id, vendor_id (→ negocios.id), fiesta_id, rating, photo_url (nullable),
  reviewer_whatsapp, created_at   -- only from a guest of that fiesta
```

- **Public write posture** matches `api/negocios` / `api/sugerencias`: honeypot +
  daily flood cap; publish-first, soft-moderate after.
- **`negocios` gets the Phase-4 hook** (`boosted_until`) it was already speced for;
  §7 ranking reads it. No schema fork.
- New migration(s) follow the `src/migrations/00NN_*.sql` sequence (next free index).

## 11. Metrics — the loop, instrumented from day one

The whole point is to *measure* the viral coefficient, not assume it. Reuse the
first-party `api/evento` beacon.

| Stage | Metric | Why |
|---|---|---|
| Reach | Invites forwarded per fiesta | Fan-out (the multiplier term) |
| Open | RSVP-page opens per invite | Does the invite travel? |
| **Loop** | **Guest→host conversion within one cycle** | **The compounding term of k** |
| **Viral** | **k = invites/host × (new hosts ÷ invitees)** | **Is it ≥1 within a fiesta cycle?** |
| Demand | Leads sent to vendors (free) | The value that warms Phase-4 conversion |
| Supply health | Time-to-first-lead for a seeded vendor | The supply→demand gap (research §10) |
| Trust | Review capture rate post-fiesta | Is the moat accreting? |
| Density | Vendors per category in the pilot colonia | Are match results non-empty? |

**Kill/scale gate:** if k and guest→host move after the invite page is genuinely
good, the model is real and self-funding → scale + turn on Phase-4 boosts. If they
stall well below 1, the viral thesis is wrong — fix the invite artifact before
building anything downstream. No directory seeding saves a broken loop.

## 12. Bootstrap — do things that don't scale

1. **One colonia/corridor** (Centro first, per marketing-plan territory order). Win
   its fiesta market completely before spreading. A dense atomic network beats a
   thin citywide layer (research §6, §12).
2. **Concierge the first ~20 real fiestas by hand.** Founder/helpers create invites
   with real hosts and *manually route leads* to seeded vendors so vendors feel
   value before any paid ask (Airbnb playbook).
3. **Seed against the calendar.** Time the first push to a fiesta-dense window and
   pre-seed the needed vendor categories ~6 weeks ahead (research §9.5).
4. **Party QR at every concierge'd fiesta** to harvest the first hosts + reviews on
   site.

## 13. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Invite doesn't spread (weak OG / install friction) | Invest in the OG unfurl + zero-install web first; it is the ad. Measure open-per-invite before scaling |
| Supply→demand gap (vendors churn lead-less) | Launch close behind Phase 2; concierge the first leads (§12) |
| Hosts plan on WhatsApp anyway | We don't replace the chat — we add the structured invite + vendor match it can't hold, and link back to WhatsApp |
| Disintermediation (no rake) | By design: monetize position (Phase-4 boost), never the transaction |
| Grupos/dating brand risk | Private invite-only default; no public singles directory; data-gated graduation (§9) |
| Fake reviews | Only guests of a fiesta can review its vendors (§8) |
| Seasonality (Jan/Sep cash dips) | Free tool is seasonality-proof; time *paid* asks (Phase 4) to strong months |

## 14. Milestones within Phase 3

| # | Deliverable | Gates |
|---|---|---|
| 3.0 | Fiesta types + needs categories finalized (map to `negocios` FIESTA_CATS) | Match works |
| 3.1 | Create-a-fiesta + tokenized manage link (WhatsApp identity) | Hosts can create |
| 3.2 | **Invitation/RSVP page with rich OG unfurl + guest→host CTA** | **The loop is live — the keystone** |
| 3.3 | Needs-list → `negocios` match + WhatsApp handoff + `leads` logging | Free leads flow |
| 3.4 | Loop instrumentation (k-factor, guest→host, lead, review) via `api/evento` | Measurement live |
| 3.5 | Post-fiesta review harvest → `negocios` trust data | Moat accretes |
| 3.6 | Party-QR print + concierge pilot in one colonia (~20 fiestas) | **Real k-factor number** |
| 3.7 | Grupos event-type (experiment appendix) | Cheap dating test |

## 15. One-line summary

> Give hosts a free, install-free fiesta invitation that spreads itself through
> WhatsApp — every RSVP recruits the next host, every needs-list sends a free lead
> to a Phase-2 vendor, every party harvests reviews that build the trust moat.
> **This is the viral loop the whole organic model was missing; Phase 2 built the
> supply, this turns the demand on, and Phase 4 flips the money — supply before
> demand before money.**
