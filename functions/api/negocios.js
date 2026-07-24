/**
 * POST /api/negocios — public self-serve intake for the business & service
 * directory (Phase 2). A business scans the QR flyer, opens /combis/alta, and
 * registers itself — no salesperson. Rows land in `negocios` with active = 1
 * (publish-first); admin can soft-hide spam. See PRD-phase2-fiesta-vendor-directory.md.
 * Same public-write posture as /api/sugerencias: honeypot + daily flood cap.
 */
const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store", "X-Robots-Tag": "noindex" },
  });

const str = (v, max) => String(v == null ? "" : v).trim().slice(0, max);
const digits = (v) => String(v == null ? "" : v).replace(/\D/g, "");
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// categories whose presence marks a fiesta vendor (feeds the fiestas vendor feed)
const FIESTA_CATS = new Set([
  "taquiza", "catering", "pastel", "reposteria", "dj", "sonido", "mariachi",
  "musica", "banda", "foto-video", "decoracion", "globos", "mobiliario",
  "carpas", "salon", "meseros", "flores", "brincolines", "pinatas", "dulces",
  "vajilla", "seguridad-eventos", "animacion", "bar-movil", "invitaciones",
]);

// GET /api/negocios — public directory read: active businesses, only the fields
// a customer needs (no email/owner_name/edit_token/qr_batch/ip). Edge-cached 60s.
export async function onRequestGet({ env }) {
  const { results } = await env.DB.prepare(
    `SELECT id, name, category, category2, category_other, description,
            whatsapp, phone, facebook, instagram, website,
            colonia, service_area, hours, price_from, price_note, fiesta,
            has_location, lat, lon, verified
       FROM negocios WHERE active = 1
       ORDER BY verified DESC, id DESC LIMIT 500`).all().catch(() => ({ results: [] }));
  return new Response(JSON.stringify({ businesses: results }), {
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=60",
      "X-Robots-Tag": "noindex",
    },
  });
}

export async function onRequestPost({ request, env }) {
  let b;
  try { b = await request.json(); } catch { return json({ error: "Datos inválidos." }, 400); }
  if (b.fax) return json({ ok: true });   // honeypot: bots fill hidden fields

  const name = str(b.name, 80);
  if (name.length < 3) return json({ error: "Escribe el nombre del negocio." }, 400);

  const category = str(b.category, 48);
  if (!category) return json({ error: "Elige una categoría." }, 400);
  const category2 = str(b.category2, 48) || null;
  const category_other = str(b.category_other, 60) || null;

  const phone = digits(b.phone).slice(0, 15);
  const whatsapp = digits(b.whatsapp).slice(0, 15);
  if (phone.length < 10 && whatsapp.length < 10)
    return json({ error: "Deja un WhatsApp o teléfono de 10 dígitos para que te contacten." }, 400);

  const email = str(b.email, 120);
  if (email && !EMAIL_RE.test(email)) return json({ error: "El correo no es válido." }, 400);

  const has_location = b.has_location ? 1 : 0;
  let lat = parseFloat(b.lat), lon = parseFloat(b.lon);
  const inMexico = isFinite(lat) && isFinite(lon) && lat >= 14 && lat <= 33 && lon >= -118 && lon <= -86;
  if (has_location && !inMexico)
    return json({ error: "Marca la ubicación de tu local en el mapa." }, 400);
  if (!has_location || !inMexico) { lat = null; lon = null; }

  const priceRaw = parseFloat(b.price_from);
  const price_from = isFinite(priceRaw) && priceRaw >= 0 ? Math.min(priceRaw, 9999999) : null;

  // fiesta flag: client hint OR either category is a known fiesta category
  const fiesta = (b.fiesta ||
    FIESTA_CATS.has(category) || (category2 && FIESTA_CATS.has(category2))) ? 1 : 0;

  // crude flood control: max 80 self-signups per day (matches /api/sugerencias posture)
  const recent = await env.DB.prepare(
    "SELECT COUNT(*) c FROM negocios WHERE source = 'self' AND created_at > datetime('now','-1 day')"
  ).first().catch(() => ({ c: 0 }));
  if (recent.c >= 80) return json({ ok: true, queued: true });   // silently accept + drop

  const edit_token = crypto.randomUUID();

  await env.DB.prepare(
    `INSERT INTO negocios
       (name, category, category2, category_other, description, owner_name,
        phone, whatsapp, email, facebook, instagram, website,
        has_location, lat, lon, address, colonia, municipio, service_area,
        hours, price_from, price_note, fiesta, tags, edit_token, source, qr_batch, active)
     VALUES
       (?1, ?2, ?3, ?4, ?5, ?6,
        ?7, ?8, ?9, ?10, ?11, ?12,
        ?13, ?14, ?15, ?16, ?17, ?18, ?19,
        ?20, ?21, ?22, ?23, ?24, ?25, 'self', ?26, 1)`
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

  return json({ ok: true, edit_token });
}
