/**
 * Admin write for sticker placements from the iOS app (scan → locate → save).
 *   GET  /api/admin/stickers        → placed/installed stickers (recent first)
 *   GET  /api/admin/stickers?id=X   → one sticker's current row (or null)
 *   POST /api/admin/stickers  {id, lat?, lon?, route_id?, unit_desc?, notes?}
 *                            → upsert the sticker row, status = installed
 *
 * Location is OPTIONAL. With lat+lon the placement is `fijo` (a fixed spot); without,
 * it's `combi` — the sticker is on something that moves, so the location is the route,
 * not a point. The row is upserted so a freshly printed code (not pre-seeded as a
 * batch) still saves. The /qr/<id> resolver and scan stats read the same table.
 *
 * Auth: Authorization: Bearer <ADMIN_PASS> (same admin account as lineas/sponsors).
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

const cleanId = (v) => String(v ?? "").toUpperCase().replace(/[^A-Z0-9-]/g, "").slice(0, 20);
const strOrNull = (v, n) => { const s = String(v ?? "").trim().slice(0, n); return s || null; };

export async function onRequestGet({ request, env }) {
  if (!authed(request, env)) return json({ error: "no autorizado" }, 401);
  const id = cleanId(new URL(request.url).searchParams.get("id") || "");
  const cols = "id,status,route_id,unit_desc,notes,placement,lat,lon,installed_at,updated_at";
  if (id) {
    const sticker = await env.DB.prepare(`SELECT ${cols} FROM stickers WHERE id = ?1`).bind(id).first();
    return json({ sticker: sticker || null });
  }
  const { results } = await env.DB.prepare(
    `SELECT ${cols} FROM stickers WHERE placement IS NOT NULL OR status != 'printed'
     ORDER BY updated_at DESC LIMIT 500`
  ).all();
  return json({ stickers: results });
}

export async function onRequestPost({ request, env }) {
  if (!authed(request, env)) return json({ error: "no autorizado" }, 401);
  let b;
  try { b = await request.json(); } catch { return json({ error: "bad json" }, 400); }

  const id = cleanId(b.id);
  if (!id) return json({ error: "id requerido" }, 400);

  const lat = Number(b.lat), lon = Number(b.lon);
  const hasLoc = Number.isFinite(lat) && Number.isFinite(lon);
  const placement = hasLoc ? "fijo" : "combi";     // no location ⇒ it moves (combi)
  const route_id = strOrNull(b.route_id, 80);
  const unit_desc = strOrNull(b.unit_desc, 120);
  const notes = strOrNull(b.notes, 300);
  const batch = id.includes("-") ? id.split("-")[0] : "campo";

  await env.DB.prepare(
    `INSERT INTO stickers
       (id, batch, status, route_id, unit_desc, notes, placement, lat, lon, installed_by, installed_at, updated_at)
     VALUES (?1, ?2, 'installed', ?3, ?4, ?5, ?6, ?7, ?8, 'michael', datetime('now'), datetime('now'))
     ON CONFLICT(id) DO UPDATE SET
       status='installed', route_id=?3, unit_desc=?4, notes=COALESCE(?5, notes),
       placement=?6, lat=?7, lon=?8, installed_by='michael',
       installed_at=datetime('now'), updated_at=datetime('now')`
  ).bind(id, batch, route_id, unit_desc, notes, placement,
         hasLoc ? lat : null, hasLoc ? lon : null).run();

  // best-effort audit (table exists from migration 0011)
  await env.DB.prepare("INSERT INTO audit (role, action, entity, detail) VALUES ('michael','sticker.place',?1,?2)")
    .bind("stickers:" + id, placement).run().catch(() => {});

  return json({ ok: true, id, placement });
}
