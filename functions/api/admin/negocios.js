/**
 * Admin review queue for self-registered businesses (the iOS app's "Negocios" tab).
 *   GET  /api/admin/negocios          -> listings awaiting review (reviewed=0), newest first
 *   POST /api/admin/negocios {id, action:"approve"|"reject"}
 *        approve -> reviewed=1            (stays live; just leaves the queue)
 *        reject  -> reviewed=1, active=0  (goes dark)
 *
 * Auth: Authorization: Bearer <ADMIN_PASS> (same account as /api/admin/sponsors).
 * Listings publish on submit; this is review-after-the-fact, so approving changes
 * nothing public — it only clears the item. Rejecting hides it (public read filters
 * active=1, so the pin/card drops within the read cache TTL, no deploy).
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

export async function onRequestGet({ request, env }) {
  if (!authed(request, env)) return json({ error: "no autorizado" }, 401);
  const { results } = await env.DB.prepare(
    `SELECT id, name, category, category2, category_other, description, owner_name,
            whatsapp, phone, email, facebook, instagram, website,
            has_location, lat, lon, address, colonia, service_area, hours,
            price_from, price_note, fiesta, qr_batch, created_at
       FROM negocios WHERE reviewed = 0
       ORDER BY created_at DESC, id DESC LIMIT 300`
  ).all();
  return json({ pending: results });
}

export async function onRequestPost({ request, env }) {
  if (!authed(request, env)) return json({ error: "no autorizado" }, 401);
  let b;
  try { b = await request.json(); } catch { return json({ error: "bad json" }, 400); }

  const id = Number(b.id);
  if (!Number.isFinite(id)) return json({ error: "id requerido" }, 400);

  if (b.action === "approve") {
    await env.DB.prepare(
      "UPDATE negocios SET reviewed = 1, updated_at = datetime('now') WHERE id = ?1").bind(id).run();
  } else if (b.action === "reject") {
    await env.DB.prepare(
      "UPDATE negocios SET reviewed = 1, active = 0, updated_at = datetime('now') WHERE id = ?1").bind(id).run();
  } else {
    return json({ error: "action inválida (approve|reject)" }, 400);
  }
  return json({ ok: true, id, action: b.action });
}
