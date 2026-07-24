/**
 * GET /api/foto/<key> — serve a stored photo from KV (binding FOTOS_KV), edge-cached.
 * Cached 1 day (NOT immutable): a moderation "reject" DELETES the KV entry, and the
 * short TTL lets that deletion propagate off the edge within a day without a manual
 * cache purge — the right tradeoff for user-moderated content. Most reads still hit
 * the edge cache (keeps us under the free KV read cap); a 404 here means it's gone.
 */
const CACHE_TTL = 86400; // 1 day — so rejected/deleted photos fall out of cache
export async function onRequestGet({ request, env, params, waitUntil }) {
  if (!env.FOTOS_KV) return new Response("storage unavailable", { status: 503 });

  const parts = params.path;
  const key = Array.isArray(parts) ? parts.join("/") : String(parts || "");
  if (!key || key.includes("..")) return new Response("not found", { status: 404 });

  const cache = caches.default;
  const cacheKey = new Request(new URL(request.url).toString(), request);
  const hit = await cache.match(cacheKey);
  if (hit) return hit;

  const { value, metadata } = await env.FOTOS_KV.getWithMetadata(key, { type: "arrayBuffer" });
  if (!value) return new Response("not found", { status: 404 });

  const headers = new Headers();
  headers.set("Content-Type", (metadata && metadata.mime) || "application/octet-stream");
  headers.set("Cache-Control", `public, max-age=${CACHE_TTL}`);
  headers.set("X-Content-Type-Options", "nosniff");

  const res = new Response(value, { headers });
  if (waitUntil) waitUntil(cache.put(cacheKey, res.clone()));
  return res;
}
