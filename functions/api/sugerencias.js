/**
 * POST /api/sugerencias — public intake for missing places ("¿Es tu negocio?
 * Agrégalo gratis"). The Instagram-only long tail can't be harvested legally,
 * so it registers itself. Rows land in `places` with active = 0 (pending) and
 * surface in the admin /lugares queue for approval; approving publishes to
 * search. Contact info doubles as a warm sponsorship lead.
 * Same public-write posture as /api/reportes and /api/pv: honeypot + caps.
 */
const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store", "X-Robots-Tag": "noindex" } });

export async function onRequestPost({ request, env }) {
  let b;
  try { b = await request.json(); } catch { return json({ error: "bad json" }, 400); }
  if (b.website) return json({ ok: true });   // honeypot: bots fill every field

  const name = String(b.name || "").trim().slice(0, 80);
  if (name.length < 3) return json({ error: "nombre requerido" }, 400);
  const kind = String(b.kind || "tienda").trim().slice(0, 24) || "tienda";
  const contact = String(b.contact || "").trim().slice(0, 120);
  let lat = parseFloat(b.lat), lon = parseFloat(b.lon);
  if (!isFinite(lat) || !isFinite(lon) || lat < 14 || lat > 33 || lon < -118 || lon > -86) {
    lat = null; lon = null;                    // location optional: admin pins it on approval
  }

  // crude flood control: max 20 pending public suggestions per day
  const recent = await env.DB.prepare(
    "SELECT COUNT(*) c FROM places WHERE added_by = 'sugerencia' AND created_at > datetime('now','-1 day')"
  ).first().catch(() => ({ c: 0 }));
  if (recent.c >= 20) return json({ ok: true, queued: true });  // silently accept, drop

  await env.DB.prepare(
    `INSERT INTO places (name, kind, lat, lon, aliases, notes, added_by, active)
     VALUES (?1, ?2, COALESCE(?3, 18.462), COALESCE(?4, -97.396), NULL, ?5, 'sugerencia', 0)`)
    .bind(name, kind, lat, lon,
          ("PENDIENTE · contacto: " + (contact || "—") + (lat === null ? " · SIN UBICACIÓN" : "")).slice(0, 300)).run();
  return json({ ok: true });
}
