/**
 * First-party analytics: server-side page-hit logging to D1 (no client beacon,
 * no third parties). Logs page views + /qr/ scans; static assets are skipped.
 * Visitor identity = first-party cookie (qcv) + IP fallback, so revisits vs new
 * visits are distinguishable. Retention: 90-day opportunistic purge.
 */
const COOKIE = "qcv";
const INTERNAL = "qint";   // ?internal=1 marks the operator's own device; excluded from real stats
const BOT_UA = /headless|\bbot\b|crawl|spider|slurp|\bcurl\b|wget|python|go-http|okhttp|java\/|libwww|phantom|puppeteer|playwright|lighthouse|node-fetch|scrapy|semrush|ahrefs/i;
function trafficKind(ua, referer, qint) {
  if (qint === "1") return "internal";
  const u = (ua || "").trim();
  if (!u) return "bot";
  if (BOT_UA.test(u)) return "bot";
  if (referer && /:\/\/[^/]*\.vercel\.app/i.test(referer)) return "bot";
  return "user";
}

export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);

  const isPage =
    request.method === "GET" &&
    (url.pathname === "/" || url.pathname.endsWith("/") || url.pathname.startsWith("/qr/"));

  let response = await next();

  if (isPage) {
    const cookies = Object.fromEntries(
      (request.headers.get("Cookie") || "").split(";").map(c => c.trim().split("=").map(decodeURIComponent)).filter(p => p[0])
    );
    let visitor = cookies[COOKIE];
    const isNew = !visitor;
    const internalOpt = url.searchParams.get("internal");   // "1" set, "0" clear
    const qint = internalOpt === "1" ? "1" : internalOpt === "0" ? "0" : (cookies[INTERNAL] || "0");
    if (isNew || internalOpt === "1" || internalOpt === "0") {
      response = new Response(response.body, response);
      if (isNew) {
        visitor = crypto.randomUUID();
        response.headers.append("Set-Cookie",
          `${COOKIE}=${visitor}; Path=/; Max-Age=31536000; SameSite=Lax; HttpOnly; Secure`);
      }
      if (internalOpt === "1") response.headers.append("Set-Cookie",
        `${INTERNAL}=1; Path=/; Max-Age=31536000; SameSite=Lax; HttpOnly; Secure`);
      if (internalOpt === "0") response.headers.append("Set-Cookie",
        `${INTERNAL}=; Path=/; Max-Age=0; SameSite=Lax; HttpOnly; Secure`);
    }
    if (env.DB) context.waitUntil(logHit(request, env, url, visitor, isNew, qint).catch(() => {}));
  }
  return response;
}

async function logHit(request, env, url, visitor, isNew, qint) {
  const ua = (request.headers.get("User-Agent") || "").slice(0, 300);
  const referer = (request.headers.get("Referer") || "").slice(0, 300) || null;
  const kind = trafficKind(ua, referer, qint);
  const cf = request.cf || {};
  const qr = url.pathname.startsWith("/qr/")
    ? url.pathname.slice(4)
    : url.searchParams.get("qr");

  await env.DB.prepare(
    `INSERT INTO hits (path, query, qr, visitor, is_new, ip, country, region, city, asn, ua, referer, lang, kind)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14)`
  ).bind(
    url.pathname.slice(0, 200),
    url.search.slice(0, 200) || null,
    qr ? qr.slice(0, 64) : null,
    visitor,
    isNew ? 1 : 0,
    request.headers.get("CF-Connecting-IP") || "unknown",
    cf.country || null,
    cf.region || null,
    cf.city || null,
    cf.asn ? String(cf.asn) : null,
    ua,
    referer,
    (request.headers.get("Accept-Language") || "").slice(0, 60) || null,
    kind
  ).run();

  // opportunistic retention purge (~1 in 100 hits): keep 90 days
  if (Math.random() < 0.01) {
    await env.DB.prepare("DELETE FROM hits WHERE ts < datetime('now','-90 days')").run();
  }
}
