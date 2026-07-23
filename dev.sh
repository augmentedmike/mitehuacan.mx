#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# THE one command to run MiTehuacán locally, exactly as it deploys.
#
#     ./dev.sh
#
# Builds the events feed + the site, then serves the DEPLOY ROOT
# (build/combis — i.e. Combis at /, Eventos at /eventos, Descubre at /descubre)
# on http://localhost:8799.
#
# WHY build/combis and not build/:  vercel.json → outputDirectory = "build/combis".
# In production Vercel serves THAT folder at the domain root (Combis at /), and
# only proxies /api + /qr to the Cloudflare Pages functions. So the faithful local
# mirror is to serve build/combis statically at /. Serving build/ instead is what
# showed the old portal-at-root and caused the confusion — this script removes the
# ambiguity: there is one command and one root.
#
# /api and /qr are backed by Cloudflare Pages functions (with D1) that don't run
# in this static server; the app degrades gracefully (it has fetch fallbacks).
# Deploy to exercise the live API.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8799}"
ROOT_DIR="build/combis"        # the deploy root — Combis is served at /

echo "→ building events feed + site…"
python3 src/scripts/25_publish_events.py
python3 src/scripts/09_build_site.py

if lsof -ti "tcp:$PORT" >/dev/null 2>&1; then
  echo "→ freeing port $PORT (previous dev server)"
  lsof -ti "tcp:$PORT" | xargs kill -9 2>/dev/null || true
fi

echo
echo "  MiTehuacán dev · http://localhost:$PORT"
echo "    /           → Combis (rutas)   [home]"
echo "    /eventos/   → Eventos"
echo "    /descubre/  → Descubre"
echo
exec python3 -m http.server "$PORT" --directory "$ROOT_DIR"
