/**
 * GET /api/pv?p=<path+query> — first-party page-view beacon for hosts where
 * the HTML never touches Cloudflare (the Vercel-served domain). Same logging
 * and same qcv visitor cookie as the _middleware page path; the client only
 * calls this when it is NOT on *.pages.dev, so nothing double-counts.
 * No third parties, no client fingerprinting — identical data either way.
 */
const COOKIE = "qcv";

export async function onRequestGet({ request, env, waitUntil }) {
  const url = new URL(request.url);
  const p = (url.searchParams.get("p") || "/").slice(0, 400);
  const qIdx = p.indexOf("?");
  const path = qIdx === -1 ? p : p.slice(0, qIdx);
  const query = qIdx === -1 ? null : p.slice(qIdx, qIdx + 200);
  const qr = query ? new URLSearchParams(query).get("qr") : null;

  const cookies = Object.fromEntries(
    (request.headers.get("Cookie") || "").split(";").map(c => c.trim().split("=").map(decodeURIComponent)).filter(x => x[0]));
  let visitor = cookies[COOKIE];
  const isNew = !visitor;
  if (isNew) visitor = crypto.randomUUID();

  const cf = request.cf || {};
  if (env.DB) {
    waitUntil(env.DB.prepare(
      `INSERT INTO hits (path, query, qr, visitor, is_new, ip, country, region, city, asn, ua, referer, lang)
       VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13)`)
      .bind(path.slice(0, 200), query, qr ? qr.slice(0, 64) : null, visitor, isNew ? 1 : 0,
            request.headers.get("CF-Connecting-IP") || "unknown",
            cf.country || null, cf.region || null, cf.city || null,
            cf.asn ? String(cf.asn) : null,
            (request.headers.get("User-Agent") || "").slice(0, 300),
            (request.headers.get("Referer") || "").slice(0, 300) || null,
            (request.headers.get("Accept-Language") || "").slice(0, 60) || null)
      .run().catch(() => {}));
  }
  const res = new Response(null, { status: 204, headers: { "Cache-Control": "no-store" } });
  if (isNew) res.headers.append("Set-Cookie",
    `${COOKIE}=${visitor}; Path=/; Max-Age=31536000; SameSite=Lax; HttpOnly; Secure`);
  return res;
}
