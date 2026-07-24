/**
 * Daily D1 -> D1 backup + gzipped point-in-time archives. On its cron schedule
 * (and via a token-gated GET for manual runs / downloads), it:
 *   1. snapshots the main database into the backup database (drops+recreates
 *      every table, copies all rows, recreates indexes) — the LATEST full mirror;
 *   2. writes a gzipped JSON archive of the data into `_snapshots` (chunked BLOB
 *      rows) so older point-in-time copies survive;
 *   3. purges archives older than RETAIN_DAYS (10) — keeps ~24h/48h/5d/10d etc.
 *
 * Free tier only — Cron Trigger + D1 (no R2, no paid storage). The archives are
 * tiny gzip blobs kept in the backup DB, well inside D1's free limits.
 *
 * Endpoints (need ?token=BACKUP_TOKEN):
 *   GET /?token=..            -> run a backup now (JSON summary)
 *   GET /?token=..&list       -> list retained archives (ts, size, rows)
 *   GET /?token=..&download=latest | download=<ts>  -> the gzip file
 *
 * Restore: D1 Time Travel (30-day PITR) on the main DB is the primary path; the
 * backup DB is the latest mirror; the gzip archives are the older point-in-times.
 */
const RETAIN_DAYS = 10;
const CHUNK = 512 * 1024;   // 512 KB BLOB chunks — under D1's per-query limits

export default {
  async scheduled(event, env, ctx) { ctx.waitUntil(runBackup(env)); },
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!env.BACKUP_TOKEN || url.searchParams.get("token") !== env.BACKUP_TOKEN)
      return json({ error: "unauthorized" }, 401);
    try {
      if (url.searchParams.has("list")) return json({ archives: await listArchives(env) });
      const dl = url.searchParams.get("download");
      if (dl) return await downloadArchive(env, dl);
      return json(await runBackup(env));
    } catch (e) { return json({ error: String((e && e.message) || e) }, 500); }
  },
};

const json = (o, s = 200) =>
  new Response(JSON.stringify(o, null, 2), { status: s, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });

async function runBackup(env) {
  const src = env.SRC, bak = env.BAK;
  const started = new Date().toISOString();

  // every user/app table (skip sqlite + cloudflare internals)
  const { results: tables } = await src.prepare(
    "SELECT name, sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL " +
    "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%'").all();

  // ---- 1. full mirror (latest snapshot, overwritten each run) ----
  let totalRows = 0;
  const dump = { v: 1, ts: started, tables: [] };
  for (const t of tables) {
    await bak.prepare(`DROP TABLE IF EXISTS "${t.name}"`).run();
    await bak.prepare(t.sql).run();
    const rows = await copyRows(src, bak, t.name);
    totalRows += rows.length;
    dump.tables.push({ name: t.name, sql: t.sql, rows });   // for the gzip archive
  }

  // recreate indexes so the backup is query-ready (ignore failures — data is the point)
  const { results: idx } = await src.prepare(
    "SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL AND name NOT LIKE 'sqlite_%'").all();
  for (const i of idx) { try { await bak.prepare(i.sql).run(); } catch (e) { /* index optional */ } }

  await bak.prepare("CREATE TABLE IF NOT EXISTS _backup_meta (ts TEXT PRIMARY KEY, tables INTEGER, rows INTEGER)").run();
  await bak.prepare("INSERT OR REPLACE INTO _backup_meta (ts, tables, rows) VALUES (?1,?2,?3)")
    .bind(started, tables.length, totalRows).run();

  // ---- 2. gzipped point-in-time archive (chunked BLOB rows in the backup DB) ----
  dump.meta = { tables: tables.length, rows: totalRows };
  const gz = await gzip(JSON.stringify(dump));
  await bak.prepare(
    "CREATE TABLE IF NOT EXISTS _snapshots (ts TEXT NOT NULL, chunk INTEGER NOT NULL, " +
    "data BLOB NOT NULL, bytes INTEGER NOT NULL, rows INTEGER, tables INTEGER, " +
    "PRIMARY KEY (ts, chunk))").run();
  // (idempotent) replace any partial archive for this exact ts, then write chunks
  await bak.prepare("DELETE FROM _snapshots WHERE ts = ?1").bind(started).run();
  let chunks = 0;
  for (let off = 0, i = 0; off < gz.length; off += CHUNK, i++) {
    const part = gz.slice(off, off + CHUNK);   // fresh Uint8Array -> own ArrayBuffer
    await bak.prepare(
      "INSERT INTO _snapshots (ts, chunk, data, bytes, rows, tables) VALUES (?1,?2,?3,?4,?5,?6)")
      .bind(started, i, part.buffer, gz.length, totalRows, tables.length).run();
    chunks++;
  }

  // ---- 3. retention: purge archives older than RETAIN_DAYS ----
  const cutoff = new Date(Date.now() - RETAIN_DAYS * 86400 * 1000).toISOString();
  const purged = await bak.prepare("DELETE FROM _snapshots WHERE ts < ?1").bind(cutoff).run();

  return {
    ok: true, started, finished: new Date().toISOString(),
    tables: tables.length, rows: totalRows,
    archive: { bytes: gz.length, chunks, retain_days: RETAIN_DAYS, purged_before: cutoff },
  };
}

async function copyRows(src, bak, table) {
  const PAGE = 500, BATCH = 25;
  let offset = 0, cols = null, insert = null;
  const all = [];
  for (;;) {
    const { results: rows } = await src.prepare(`SELECT * FROM "${table}" LIMIT ${PAGE} OFFSET ${offset}`).all();
    if (!rows.length) break;
    if (!cols) {
      cols = Object.keys(rows[0]);
      const ph = "(" + cols.map((_, i) => "?" + (i + 1)).join(",") + ")";
      insert = `INSERT INTO "${table}" (${cols.map(c => `"${c}"`).join(",")}) VALUES ${ph}`;
    }
    for (let i = 0; i < rows.length; i += BATCH) {
      await bak.batch(rows.slice(i, i + BATCH).map(r => bak.prepare(insert).bind(...cols.map(c => r[c]))));
    }
    for (const r of rows) all.push(serializeRow(r));   // collect for the archive
    if (rows.length < PAGE) break;
    offset += PAGE;
  }
  return all;
}

// JSON-safe row: BLOB columns (ArrayBuffer) become base64 with a marker so the
// archive round-trips even if a table ever holds binary data.
function serializeRow(r) {
  const o = {};
  for (const k in r) {
    const v = r[k];
    o[k] = (v instanceof ArrayBuffer) ? { $b64: b64(new Uint8Array(v)) } : v;
  }
  return o;
}

function b64(u8) {
  let s = "";
  for (let i = 0; i < u8.length; i++) s += String.fromCharCode(u8[i]);
  return btoa(s);
}

async function gzip(str) {
  const cs = new CompressionStream("gzip");
  const w = cs.writable.getWriter();
  w.write(new TextEncoder().encode(str));
  w.close();
  const parts = [];
  const reader = cs.readable.getReader();
  for (;;) { const { done, value } = await reader.read(); if (done) break; parts.push(value); }
  const total = parts.reduce((n, p) => n + p.length, 0);
  const out = new Uint8Array(total);
  let o = 0;
  for (const p of parts) { out.set(p, o); o += p.length; }
  return out;
}

async function listArchives(env) {
  await env.BAK.prepare(
    "CREATE TABLE IF NOT EXISTS _snapshots (ts TEXT NOT NULL, chunk INTEGER NOT NULL, " +
    "data BLOB NOT NULL, bytes INTEGER NOT NULL, rows INTEGER, tables INTEGER, PRIMARY KEY (ts, chunk))").run();
  const { results } = await env.BAK.prepare(
    "SELECT ts, MAX(bytes) bytes, MAX(rows) rows, MAX(tables) tables, COUNT(*) chunks " +
    "FROM _snapshots GROUP BY ts ORDER BY ts DESC").all();
  return results;
}

async function downloadArchive(env, sel) {
  let ts = sel;
  if (sel === "latest") {
    const row = await env.BAK.prepare("SELECT ts FROM _snapshots ORDER BY ts DESC LIMIT 1").first();
    if (!row) return json({ error: "no archives yet" }, 404);
    ts = row.ts;
  }
  const { results } = await env.BAK.prepare(
    "SELECT data FROM _snapshots WHERE ts = ?1 ORDER BY chunk").bind(ts).all();
  if (!results.length) return json({ error: "not found: " + ts }, 404);
  const parts = results.map(r => r.data instanceof ArrayBuffer ? new Uint8Array(r.data) : Uint8Array.from(r.data));
  const total = parts.reduce((n, p) => n + p.length, 0);
  const out = new Uint8Array(total);
  let o = 0;
  for (const p of parts) { out.set(p, o); o += p.length; }
  return new Response(out, { headers: {
    "Content-Type": "application/gzip",
    "Content-Disposition": `attachment; filename="mitehuacan-${ts.replace(/[:.]/g, "-")}.json.gz"`,
    "Cache-Control": "no-store",
  }});
}
