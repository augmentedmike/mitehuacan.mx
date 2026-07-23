/**
 * /qr/<sticker> — every printed QR passes through here. Records nothing itself
 * (the app's hit middleware logs ?qr= on landing); its job is the SMART
 * redirect: a sticker installed on a combi deep-links straight to its route,
 * anything else lands on the map home. Never 404s — printed codes outlive
 * database rows.
 */
export async function onRequestGet({ request, env, params }) {
  const id = String(params.id || "").toUpperCase().replace(/[^A-Z0-9-]/g, "").slice(0, 20);
  // behind the Vercel domain proxy the request carries X-Forwarded-Host —
  // redirect there (app at /); direct pages.dev hits keep /combis/
  const fwd = request.headers.get("X-Forwarded-Host");
  const proxied = fwd && !fwd.endsWith("pages.dev");
  const origin = proxied ? "https://" + fwd : new URL(request.url).origin;
  const base = proxied ? "/" : "/combis/";
  let route = null;
  try {
    const row = await env.DB.prepare(
      "SELECT route_id, status FROM stickers WHERE id = ?1").bind(id).first();
    if (row && row.route_id && row.status !== "retired") route = row.route_id;
  } catch (e) { /* table missing or db hiccup: plain landing still works */ }
  const to = origin + base + "?" + (route ? "ruta=" + encodeURIComponent(route) + "&" : "") +
             "qr=" + encodeURIComponent(id);
  return Response.redirect(to, 302);
}
