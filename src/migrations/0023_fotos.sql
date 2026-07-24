-- User-uploaded photo ledger. The image BYTES live in KV (Pages binding FOTOS_KV
-- — the no-card free-tier store; R2 is the drop-in upgrade when a card is added);
-- this table is the index + moderation + rate-limit ledger — one row per stored
-- object. `r2_key` holds the storage key (kept generic across KV/R2). Written by
-- POST /api/foto; served by GET /api/foto/<key>.
--
-- Publish-first (status='active' on upload), consistent with `negocios`: an admin
-- can flip a row to 'rejected', which also DELETES the stored object, so it stops
-- serving (a 404 on the serve route == gone). To switch to pre-moderation later,
-- change the default to 'pending' and gate the serve route on status.
--
-- Photos are downscaled + re-encoded CLIENT-side before upload (a canvas re-encode
-- both shrinks the file AND strips EXIF/GPS). /api/foto enforces mime + a hard
-- byte cap as defense in depth — Workers can't decode/resize images server-side.
CREATE TABLE IF NOT EXISTS fotos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  r2_key TEXT UNIQUE NOT NULL,             -- object key in the R2 bucket
  mime TEXT NOT NULL,                       -- image/jpeg | image/png | image/webp
  bytes INTEGER NOT NULL,
  entity_type TEXT,                         -- 'negocio' | 'renta' | ... (null = not yet attached)
  entity_id TEXT,                           -- id within that entity
  status TEXT NOT NULL DEFAULT 'active',    -- active | rejected
  visitor TEXT,                             -- qcv cookie (rate limit + attribution)
  ip TEXT,
  ua TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_fotos_entity ON fotos (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_fotos_status ON fotos (status);
CREATE INDEX IF NOT EXISTS idx_fotos_visitor_rate ON fotos (visitor, created_at);
CREATE INDEX IF NOT EXISTS idx_fotos_ip_rate ON fotos (ip, created_at);
