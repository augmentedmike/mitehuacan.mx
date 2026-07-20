/**
 * GET /api/sponsor-pins — PUBLIC read of publishable sponsor locations.
 * Publication rule (the deal is literal): sponsor active AND location active
 * AND (tier = 'barter' OR a SIGNED contract exists). Suspending a sponsor or
 * cancelling a contract drops the pins within the cache TTL — no deploy.
 * The map merges these with the static sponsors.js seed (which also carries
 * the logo assets); route matching happens client-side where the geometry lives.
 */
export async function onRequestGet({ env }) {
  const rows = await env.DB.prepare(
    `SELECT s.slug, s.name, s.tier, l.lat, l.lon, l.label
     FROM sponsors s JOIN sponsor_locations l ON l.sponsor_slug = s.slug
     WHERE s.active = 1 AND l.active = 1
       AND (s.tier = 'barter' OR EXISTS
            (SELECT 1 FROM contracts c WHERE c.sponsor_slug = s.slug AND c.status = 'signed'))
     ORDER BY s.slug`).all().catch(() => ({ results: [] }));
  const sponsors = {};
  for (const r of rows.results) {
    (sponsors[r.slug] ||= { name: r.name, tier: r.tier, locs: [] })
      .locs.push([r.lon, r.lat, r.label || ""]);
  }
  return new Response(JSON.stringify({ sponsors }), {
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=300",
      "X-Robots-Tag": "noindex",
    },
  });
}
