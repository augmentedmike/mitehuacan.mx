-- stickers: the physical QR lifecycle (PRD-backoffice §3). Printed codes are
-- pre-seeded per batch; /qr/<id> scans (hits.qr) drive verify/dead automatically.
CREATE TABLE IF NOT EXISTS stickers (
  id TEXT PRIMARY KEY,            -- printed code, e.g. TEH-0042
  batch TEXT NOT NULL,            -- print batch, e.g. 2026-07-A
  status TEXT NOT NULL DEFAULT 'printed',
                                  -- printed | installed | verified | dead | retired
  route_id TEXT,                  -- line it was installed on
  unit_desc TEXT,                 -- "combi blanca, placa SXY-123-A"
  installed_by TEXT,
  installed_at TEXT,
  last_scan TEXT,
  scans_30d INTEGER DEFAULT 0,
  notes TEXT,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_stickers_status ON stickers (status);
CREATE INDEX IF NOT EXISTS idx_stickers_batch ON stickers (batch);

-- universal write audit (PRD-backoffice §1)
CREATE TABLE IF NOT EXISTS audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL DEFAULT (datetime('now')),
  role TEXT NOT NULL,
  action TEXT NOT NULL,
  entity TEXT,
  detail TEXT
);
