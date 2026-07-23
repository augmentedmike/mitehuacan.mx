/**
 * POST /api/feedback — portal feedback + bug reports. Everything lands in D1
 * (table `feedback`, migration 0019) — no email, no github. Same public-write
 * posture as /api/reportes: honeypot + length caps + per-IP daily cap.
 *   { kind: "idea"|"bug", message, contact?, page?, website? (honeypot) }
 */
const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store", "X-Robots-Tag": "noindex" },
  });

export async function onRequestPost({ request, env }) {
  let b;
  try { b = await request.json(); } catch { return json({ error: "invalid json" }, 400); }
  if (b.website) return json({ ok: true }, 201);          // honeypot: bots fill every field

  const kind = b.kind === "bug" ? "bug" : "idea";
  const message = String(b.message || "").trim().slice(0, 1500);
  const contact = String(b.contact || "").trim().slice(0, 120) || null;
  const page = String(b.page || "").trim().slice(0, 120) || null;
  if (message.length < 5) return json({ error: "escribe un poco más" }, 422);

  const ipHash = await sha256(request.headers.get("CF-Connecting-IP") || "unknown");
  const { count } = await env.DB
    .prepare("SELECT COUNT(*) AS count FROM feedback WHERE ip_hash = ?1 AND created_at > datetime('now','-1 day')")
    .bind(ipHash).first().catch(() => ({ count: 0 }));
  if (count >= 20) return json({ ok: true }, 201);        // silently accept + drop

  await env.DB
    .prepare("INSERT INTO feedback (kind, message, contact, page, ip_hash) VALUES (?1,?2,?3,?4,?5)")
    .bind(kind, message, contact, page, ipHash).run();
  return json({ ok: true }, 201);
}

async function sha256(s) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(d)].map((x) => x.toString(16).padStart(2, "0")).join("");
}
