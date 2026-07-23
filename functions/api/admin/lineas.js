/**
 * Admin write for combi line metadata + per-day schedule (Phase 1).
 *   GET  /api/admin/lineas         → list all lines (for the app to reconcile-read)
 *   POST /api/admin/lineas  {slug,name,first_run,last_run,headway_min,
 *                            sat_first,sat_last,sat_headway,
 *                            sun_first,sun_last,sun_headway,notes}  → upsert one line
 *
 * Auth: Authorization: Bearer <ADMIN_PASS>. Reads on this endpoint are also gated
 * (it exposes the full admin dataset). The public map still reads /api/horarios.
 * Writes land in combi_lines (slug = routes.js properties.id) and the live map
 * picks them up via /api/horarios within its cache window — no redeploy.
 */
const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store", "X-Robots-Tag": "noindex" },
  });

function teq(a, b) {
  const enc = new TextEncoder();
  const x = enc.encode(String(a)), y = enc.encode(String(b));
  if (x.length !== y.length) return false;
  let r = 0;
  for (let i = 0; i < x.length; i++) r |= x[i] ^ y[i];
  return r === 0;
}
function authed(request, env) {
  if (!env.ADMIN_PASS) return false;
  const h = request.headers.get("Authorization") || "";
  const t = h.startsWith("Bearer ") ? h.slice(7) : "";
  return teq(t, env.ADMIN_PASS);
}

const hhmm = (v) => { const s = String(v ?? "").trim().slice(0, 5); return /^\d{1,2}:\d{2}$/.test(s) ? s : null; };
const mins = (v) => { const x = parseInt(v, 10); return Number.isFinite(x) && x > 0 && x <= 240 ? x : null; };
const pesos = (v) => { const x = parseInt(v, 10); return Number.isFinite(x) && x >= 0 && x <= 2000 ? x : null; };

export async function onRequestGet({ request, env }) {
  if (!authed(request, env)) return json({ error: "no autorizado" }, 401);
  const { results } = await env.DB.prepare(
    "SELECT slug,name,first_run,last_run,headway_min,sat_first,sat_last,sat_headway," +
    "sun_first,sun_last,sun_headway,notes,updated_at FROM combi_lines"
  ).all();
  return json({ lines: results });
}

export async function onRequestPost({ request, env }) {
  if (!authed(request, env)) return json({ error: "no autorizado" }, 401);
  let b;
  try { b = await request.json(); } catch { return json({ error: "bad json" }, 400); }
  const slug = String(b.slug || "").trim().slice(0, 80);
  if (!slug) return json({ error: "slug requerido" }, 400);
  const name = String(b.name || slug).trim().slice(0, 120);
  const notes = String(b.notes || "").slice(0, 500) || null;

  await env.DB.prepare(
    `INSERT INTO combi_lines
       (slug,name,first_run,last_run,headway_min,sat_first,sat_last,sat_headway,sun_first,sun_last,sun_headway,fare_mxn,notes,updated_at)
     VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,datetime('now'))
     ON CONFLICT(slug) DO UPDATE SET
       name=?2, first_run=?3, last_run=?4, headway_min=?5,
       sat_first=?6, sat_last=?7, sat_headway=?8,
       sun_first=?9, sun_last=?10, sun_headway=?11,
       fare_mxn=?12, notes=?13, updated_at=datetime('now')`
  ).bind(
    slug, name, hhmm(b.first_run), hhmm(b.last_run), mins(b.headway_min),
    hhmm(b.sat_first), hhmm(b.sat_last), mins(b.sat_headway),
    hhmm(b.sun_first), hhmm(b.sun_last), mins(b.sun_headway), pesos(b.fare_mxn), notes
  ).run();
  return json({ ok: true, slug });
}
