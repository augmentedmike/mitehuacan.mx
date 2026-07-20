-- Curated places: the search entries OSM doesn't have (3B, Miniso, tortillerías,
-- El Paseo stores...). Captured in the field from /lugares in the admin app
-- ("usar mi ubicación" at the storefront); the public app reads them via
-- GET /api/lugares (public project, same DB) and merges them into search
-- with priority over the OSM harvest.
CREATE TABLE IF NOT EXISTS places (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'tienda',   -- spanish chip: tienda, súper, farmacia, ...
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  aliases TEXT,                          -- extra search words: "3b, tres b, tres be"
  notes TEXT,
  added_by TEXT,                         -- person credited (from their field token)
  active INTEGER NOT NULL DEFAULT 1,     -- 0 = removed from search (soft delete)
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_places_active ON places (active);

-- Per-person field tokens: everyone who captures data gets their own token so
-- records credit them by name. Admin creates rows (no UI yet):
--   INSERT INTO field_tokens (token, name) VALUES ('<random>', 'María');
CREATE TABLE IF NOT EXISTS field_tokens (
  token TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
