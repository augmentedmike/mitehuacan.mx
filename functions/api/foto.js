/**
 * POST /api/foto — public self-serve photo upload for listings (negocios, rentas,
 * …). The image bytes go to KV (binding FOTOS_KV — the no-card free-tier store; R2
 * is the drop-in upgrade later); a row in `fotos` indexes them for moderation +
 * rate limiting. Publish-first, same posture as /api/negocios (no account, no
 * salesperson). Served back by GET /api/foto/<key> (foto/[[path]].js).
 *
 * Request: the raw image as the body, with Content-Type: image/jpeg|png|webp.
 *   Optional query: ?entity=negocio&id=123  pre-attaches the photo to a listing.
 *
 * CLIENT CONTRACT: downscale + re-encode the image (canvas → toBlob('image/jpeg'))
 * BEFORE upload. That shrinks the file and — critically — strips EXIF/GPS, so a
 * user never leaks their home coordinates. The server does NOT resize (the Workers
 * runtime can't decode images); it enforces mime + a hard byte cap as defense in
 * depth. Real resizing/thumbnails can be added later via Cloudflare Image Resizing.
 *
 * Response: { ok:true, key, url }  — store `key` (or `url`) on the listing row.
 */
const ALLOWED = { "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp" };
const MAX_BYTES = 800 * 1024;   // 800KB hard cap — the client should send <=~400KB
const DAILY_CAP = 40;           // uploads per visitor (or IP) per rolling 24h

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store", "X-Robots-Tag": "noindex" },
  });

export async function onRequestPost({ request, env }) {
  if (!env.FOTOS_KV) return json({ error: "storage_unavailable" }, 503);

  const mime = (request.headers.get("Content-Type") || "").split(";")[0].trim().toLowerCase();
  const ext = ALLOWED[mime];
  if (!ext) return json({ error: "tipo_no_permitido" }, 415);

  const buf = await request.arrayBuffer();
  const bytes = buf.byteLength;
  if (!bytes) return json({ error: "archivo_vacío" }, 400);
  if (bytes > MAX_BYTES) return json({ error: "muy_grande", max: MAX_BYTES }, 413);

  const cookies = request.headers.get("Cookie") || "";
  const visitor = (cookies.match(/(?:^|;\s*)qcv=([^;]+)/) || [])[1] || null;
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const ua = (request.headers.get("User-Agent") || "").slice(0, 300);

  // rate cap (by visitor cookie, else IP) — mirrors the negocios daily flood cap
  if (env.DB) {
    const col = visitor ? "visitor" : "ip";
    const val = visitor || ip;
    const row = await env.DB.prepare(
      `SELECT COUNT(*) AS n FROM fotos WHERE ${col} = ?1 AND created_at > datetime('now','-1 day')`
    ).bind(val).first().catch(() => null);
    if (row && row.n >= DAILY_CAP) return json({ error: "límite_diario" }, 429);
  }

  const url = new URL(request.url);
  const entity = (url.searchParams.get("entity") || "").toLowerCase().replace(/[^a-z]/g, "").slice(0, 16) || null;
  const eid = (url.searchParams.get("id") || "").replace(/[^a-zA-Z0-9_-]/g, "").slice(0, 40) || null;

  const key = `${entity || "sin-asignar"}/${crypto.randomUUID()}.${ext}`;
  // KV value = the raw bytes; mime travels in the ≤1KB metadata (read back on serve)
  await env.FOTOS_KV.put(key, buf, { metadata: { mime, bytes } });

  if (env.DB) {
    await env.DB.prepare(
      `INSERT INTO fotos (r2_key, mime, bytes, entity_type, entity_id, visitor, ip, ua)
       VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)`
    ).bind(key, mime, bytes, entity, eid, visitor, ip, ua).run().catch(() => {});
  }

  return json({ ok: true, key, url: `/api/foto/${key}` });
}
