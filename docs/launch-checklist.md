# Clean Launch Checklist

Stickers going up. What's done, what's left, who does it. Updated after the deploy
+ analytics cleanup.

## ✅ Done (live on prod)

- App deployed to mitehuacan.mx with all launch fixes: **self-hosted MapLibre**
  (CDN outage can't blank it), **Spanish default**, **map is the default view**,
  "verificando" label removed, mobile long-walk warning, QR-landing intro guard.
- Route data current on prod (77 routes, verificando gone), town coords fixed.
- **QR redirect live** (`/qr/<id>` → route/home, never 404s) and **scan tracking
  verified** end-to-end (hits table → admin hub "Stickers QR").
- **Sticker sheet print-ready**: `resources/stickers/mapa-de-rutas-sheet-01.pdf`
  — 18 stickers (TEH-0001…0018), 13×19", 1 cm margin, real unique tracking QRs.
- **Analytics clean**: test scans purged, QR counters at zero for launch.

## 🔲 Left before stickers go up

### Decisions — yours
1. **Sticker placement / coverage.** The map serves ~6 of 17 towns (Tehuacán +
   Ajalpan, Zapotitlán, Chilac, Santiago Miahuatlán, Azumbilla-near). **Rec: first
   wave = Tehuacán + those served towns.** Don't sticker a combi in a town with no
   mapped route.
2. **Route dedup** — is `7-san-agustin` the same combi as `7-tinaco` (42 m apart)?
   Also `c-valle`↔`rc-del-valle`, `3-de-mayo`↔`25-3-de-mayo`, `32`↔`32-colosio`.
   Tell me which (if any) to merge.
3. **Zinacatepec / Monte Chiquito routes** — real lines, no verified geometry.
   Include (record them) or leave out?

### Tasks — I can do on your word
4. **Seed the TEH-0001…0018 batch into D1** so the stickers show as managed,
   trackable items in the admin QR campaign page (install → assign to a route/
   location). Right now they redirect + log scans but aren't registered.
5. **Print the sheet(s)** — send the PDF to the print shop ($20/sheet, 18
   stickers ≈ $1.11 each). Want more sheets? `--start 19` makes sheet 2, etc.

## 🔲 Recommended soon (not launch-blocking) — admin repo, needs a deploy

6. **Recorder GPS-stall warning** — the field recorder silently stops when the
   phone locks/backgrounds; a rider can return a truncated route thinking it
   worked. Add a visible "keep screen on" warning before any field recording.
7. **Lock down DELETE** — any field token can delete production routes (no role
   separation). Gate DELETE behind the admin token.
8. **Field-token minting UI** — tokens are hand-inserted via SQL; needed before
   recruiting recorders (Monse/David).

## Notes

- **Publish flow:** a recorded route → live map is still a manual engineer step
  (no "publish" button). Fine if you tell me "publish route X"; I can build
  one-click publish (~a day) if you want it.
- **Discovery harvest** keeps growing on the daily cron (unified ~4.7k places +
  fiestas). Yoms! (@yoms.mx) and the rest sit in the approval queue — surfacing
  those to the live map is the "last mile" (push high-confidence unified places
  into the admin queue), a good post-launch build.
