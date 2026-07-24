/**
 * Admin review queue for self-registered businesses (the iOS app's "Negocios" tab).
 *   GET  /api/admin/negocios          -> listings awaiting review (reviewed=0), newest first
 *   POST /api/admin/negocios {id, action:"approve"|"reject"}
 *        approve -> reviewed=1            (stays live; just leaves the queue)
 *        reject  -> reviewed=1, active=0  (goes dark)
 *   PUT  /api/admin/negocios {name, category, ...}  -> admin-create a business
 *        Lands active=1, reviewed=1, verified=1, source='admin' — publishes live and
 *        skips the review queue (the admin is the reviewer). Returns the new id.
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

const str = (v, max) => String(v == null ? "" : v).trim().slice(0, max);
const digits = (v) => String(v == null ? "" : v).replace(/\D/g, "");
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// categories whose presence marks a fiesta vendor (mirrors /api/negocios)
const FIESTA_CATS = new Set([
  "taquiza", "catering", "pastel", "reposteria", "dj", "sonido", "mariachi",
  "musica", "banda", "foto-video", "decoracion", "globos", "mobiliario",
  "carpas", "salon", "meseros", "flores", "brincolines", "pinatas", "dulces",
  "vajilla", "seguridad-eventos", "animacion", "bar-movil", "invitaciones",
]);

// PUT /api/admin/negocios — admin adds a business by hand (no honeypot/flood cap;
// the caller is authenticated). Publishes live and pre-approved.
export async function onRequestPut({ request, env }) {
  if (!authed(request, env)) return json({ error: "no autorizado" }, 401);
  let b;
  try { b = await request.json(); } catch { return json({ error: "bad json" }, 400); }

  const name = str(b.name, 80);
  if (name.length < 3) return json({ error: "Escribe el nombre del negocio." }, 400);

  const category = str(b.category, 48);
  if (!category) return json({ error: "Elige una categoría." }, 400);
  const category2 = str(b.category2, 48) || null;
  const category_other = str(b.category_other, 60) || null;

  const phone = digits(b.phone).slice(0, 15);
  const whatsapp = digits(b.whatsapp).slice(0, 15);

  const email = str(b.email, 120);
  if (email && !EMAIL_RE.test(email)) return json({ error: "El correo no es válido." }, 400);

  const has_location = b.has_location ? 1 : 0;
  let lat = parseFloat(b.lat), lon = parseFloat(b.lon);
  const inMexico = isFinite(lat) && isFinite(lon) && lat >= 14 && lat <= 33 && lon >= -118 && lon <= -86;
  if (has_location && !inMexico)
    return json({ error: "Marca la ubicación en el mapa." }, 400);
  if (!has_location || !inMexico) { lat = null; lon = null; }

  const priceRaw = parseFloat(b.price_from);
  const price_from = isFinite(priceRaw) && priceRaw >= 0 ? Math.min(priceRaw, 9999999) : null;

  const fiesta = (b.fiesta ||
    FIESTA_CATS.has(category) || (category2 && FIESTA_CATS.has(category2))) ? 1 : 0;

  const edit_token = crypto.randomUUID();

  const res = await env.DB.prepare(
    `INSERT INTO negocios
       (name, category, category2, category_other, description, owner_name,
        phone, whatsapp, email, facebook, instagram, website,
        has_location, lat, lon, address, colonia, municipio, service_area,
        hours, price_from, price_note, fiesta, tags, edit_token, source, qr_batch,
        active, reviewed, verified)
     VALUES
       (?1, ?2, ?3, ?4, ?5, ?6,
        ?7, ?8, ?9, ?10, ?11, ?12,
        ?13, ?14, ?15, ?16, ?17, ?18, ?19,
        ?20, ?21, ?22, ?23, ?24, ?25, 'admin', ?26, 1, 1, 1)`
  ).bind(
    name, category, category2, category_other,
    str(b.description, 600) || null, str(b.owner_name, 80) || null,
    phone || null, whatsapp || null, email || null,
    str(b.facebook, 200) || null, str(b.instagram, 200) || null, str(b.website, 200) || null,
    has_location, lat, lon,
    str(b.address, 160) || null, str(b.colonia, 80) || null,
    str(b.municipio, 60) || "Tehuacán", str(b.service_area, 200) || null,
    str(b.hours, 120) || null, price_from, str(b.price_note, 40) || null,
    fiesta, str(b.tags, 200) || null, edit_token, str(b.qr_batch, 40) || null
  ).run();

  const newId = res.meta?.last_row_id ?? null;
  return json({ ok: true, id: newId });
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
