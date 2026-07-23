/**
 * Admin data entry for sponsors + their locations (no payments — that's contracts).
 *   GET  /api/admin/sponsors  → every sponsor with its nested locations (+ logo)
 *   POST /api/admin/sponsors  {slug,name,contact_name,contact_email,phone,tier,
 *                              notes,active,logo,locations:[{label,lat,lon,active}]}
 *                            → upsert one sponsor and FULL-REPLACE its locations
 *
 * Auth: Authorization: Bearer <ADMIN_PASS> (same account as /api/admin/lineas).
 * Both read and write are gated — this exposes the full sponsor dataset. The public
 * map keeps reading /api/sponsor-pins, which applies the publication rules; suspend
 * a sponsor (active=0) here and its pins drop within the pin cache TTL, no deploy.
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

const strOrNull = (v, n) => { const s = String(v ?? "").trim().slice(0, n); return s || null; };
const num = (v) => { const x = Number(v); return Number.isFinite(x) ? x : null; };
// only accept a data:image URL (or a short asset path), and cap the size so a huge
// paste can't bloat the row. ~400KB of base64 ≈ a 240px PNG with lots of headroom.
function validLogo(v) {
  const s = String(v ?? "").trim();
  if (!s) return null;
  if (s.length > 400_000) return null;
  if (s.startsWith("data:image/") || s.startsWith("patrocinadores/")) return s;
  return null;
}

export async function onRequestGet({ request, env }) {
  if (!authed(request, env)) return json({ error: "no autorizado" }, 401);
  const { results: sp } = await env.DB.prepare(
    "SELECT slug,name,contact_name,contact_email,phone,tier,notes,active,logo FROM sponsors ORDER BY name"
  ).all();
  const { results: locs } = await env.DB.prepare(
    "SELECT id,sponsor_slug,label,lat,lon,active FROM sponsor_locations ORDER BY id"
  ).all();
  const byslug = {};
  for (const l of locs) {
    (byslug[l.sponsor_slug] ||= []).push({ id: l.id, label: l.label, lat: l.lat, lon: l.lon, active: l.active });
  }
  const sponsors = sp.map((s) => ({ ...s, locations: byslug[s.slug] || [] }));
  return json({ sponsors });
}

export async function onRequestPost({ request, env }) {
  if (!authed(request, env)) return json({ error: "no autorizado" }, 401);
  let b;
  try { b = await request.json(); } catch { return json({ error: "bad json" }, 400); }

  const slug = String(b.slug || "").trim().slice(0, 80);
  if (!slug) return json({ error: "slug requerido" }, 400);
  const name = String(b.name || slug).trim().slice(0, 120);
  const tier = b.tier === "paid" ? "paid" : "barter";
  const active = b.active ? 1 : 0;

  await env.DB.prepare(
    `INSERT INTO sponsors (slug,name,contact_name,contact_email,phone,tier,notes,active,logo)
     VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9)
     ON CONFLICT(slug) DO UPDATE SET
       name=?2, contact_name=?3, contact_email=?4, phone=?5,
       tier=?6, notes=?7, active=?8, logo=?9`
  ).bind(
    slug, name, strOrNull(b.contact_name, 120), strOrNull(b.contact_email, 160),
    strOrNull(b.phone, 40), tier, strOrNull(b.notes, 500), active, validLogo(b.logo)
  ).run();

  // full-replace this sponsor's locations (the app owns the complete set per push)
  await env.DB.prepare("DELETE FROM sponsor_locations WHERE sponsor_slug = ?1").bind(slug).run();
  const locs = Array.isArray(b.locations) ? b.locations : [];
  const ins = env.DB.prepare(
    "INSERT INTO sponsor_locations (sponsor_slug,label,lat,lon,active) VALUES (?1,?2,?3,?4,?5)"
  );
  const batch = [];
  for (const l of locs) {
    const lat = num(l.lat), lon = num(l.lon);
    if (lat === null || lon === null) continue;
    batch.push(ins.bind(slug, strOrNull(l.label, 80), lat, lon, l.active ? 1 : 0));
  }
  if (batch.length) await env.DB.batch(batch);

  return json({ ok: true, slug, locations: batch.length });
}
