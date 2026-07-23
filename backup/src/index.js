/**
 * Daily D1 -> D1 backup. On its cron schedule (and via a token-gated GET for manual
 * runs), it snapshots the main database into the backup database: drops+recreates
 * every table, copies all rows (paginated + batched), recreates indexes, and stamps
 * the run in _backup_meta. Free tier only — Cron Trigger + D1 bindings, no R2/API tokens.
 *
 * The backup DB always holds the LATEST full snapshot (overwritten daily). For
 * point-in-time recovery within 30 days, use D1 Time Travel on the main DB.
 */
export default {
  async scheduled(event, env, ctx) { ctx.waitUntil(runBackup(env)); },
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!env.BACKUP_TOKEN || url.searchParams.get("token") !== env.BACKUP_TOKEN)
      return json({ error: "unauthorized" }, 401);
    try { return json(await runBackup(env)); }
    catch (e) { return json({ error: String((e && e.message) || e) }, 500); }
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

  let totalRows = 0;
  for (const t of tables) {
    await bak.prepare(`DROP TABLE IF EXISTS "${t.name}"`).run();
    await bak.prepare(t.sql).run();
    totalRows += await copyRows(src, bak, t.name);
  }

  // recreate indexes so the backup is query-ready (ignore failures — data is the point)
  const { results: idx } = await src.prepare(
    "SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL AND name NOT LIKE 'sqlite_%'").all();
  for (const i of idx) { try { await bak.prepare(i.sql).run(); } catch (e) { /* index optional */ } }

  await bak.prepare("CREATE TABLE IF NOT EXISTS _backup_meta (ts TEXT PRIMARY KEY, tables INTEGER, rows INTEGER)").run();
  await bak.prepare("INSERT OR REPLACE INTO _backup_meta (ts, tables, rows) VALUES (?1,?2,?3)")
    .bind(started, tables.length, totalRows).run();

  return { ok: true, started, finished: new Date().toISOString(), tables: tables.length, rows: totalRows };
}

async function copyRows(src, bak, table) {
  const PAGE = 500, BATCH = 25;
  let offset = 0, copied = 0, cols = null, insert = null;
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
    copied += rows.length;
    if (rows.length < PAGE) break;
    offset += PAGE;
  }
  return copied;
}
