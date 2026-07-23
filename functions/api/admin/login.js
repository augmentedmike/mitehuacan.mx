/**
 * POST /api/admin/login  { user, pass }
 * Validates the single admin account against Cloudflare secrets ADMIN_USER
 * (default "michael") and ADMIN_PASS. Returns 200 on success so the phone app
 * can confirm the PIN before storing it in the Keychain and unlocking writes.
 * The password lives ONLY as a Pages secret — never in this repo.
 */
const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store", "X-Robots-Tag": "noindex" },
  });

// constant-time string compare (avoids leaking length/among equal-length via early exit)
function teq(a, b) {
  const enc = new TextEncoder();
  const x = enc.encode(String(a)), y = enc.encode(String(b));
  if (x.length !== y.length) return false;
  let r = 0;
  for (let i = 0; i < x.length; i++) r |= x[i] ^ y[i];
  return r === 0;
}

export async function onRequestPost({ request, env }) {
  if (!env.ADMIN_PASS) return json({ error: "admin no configurado en el servidor" }, 503);
  let b;
  try { b = await request.json(); } catch { return json({ error: "bad json" }, 400); }
  const user = String(b.user || "");
  const okUser = env.ADMIN_USER || "michael";
  const ok = user === okUser && teq(String(b.pass || ""), env.ADMIN_PASS);
  return ok ? json({ ok: true, user: okUser }) : json({ error: "usuario o contraseña inválidos" }, 401);
}
