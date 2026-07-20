/**
 * GET /api/lugares — PUBLIC read of curated places (captured via the admin
 * app's /lugares page). The map merges these into its search index with
 * priority over the OSM harvest, so a place saved in the field is searchable
 * within the cache TTL. Read-only here; writes live in the admin project.
 * Never exposes who added a record.
 */
export async function onRequestGet({ env }) {
  const { results } = await env.DB.prepare(
    "SELECT name, kind, lat, lon, aliases FROM places WHERE active = 1 ORDER BY name LIMIT 2000"
  ).all().catch(() => ({ results: [] }));
  const places = results.map(r => ({
    n: r.name, k: r.kind, c: [r.lon, r.lat], ...(r.aliases ? { a: r.aliases } : {}),
  }));
  return new Response(JSON.stringify({ places }), {
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=60",
      "X-Robots-Tag": "noindex",
    },
  });
}
