-- Field proof for QR stickers: a photo of the placed code + where it lives.
-- placement 'combi' = the location IS the route (it moves); 'fijo' = lat/lon
-- captured at install time. Photos are downscaled client-side (<=~300KB) and
-- stored as D1 blobs for now; the /api/foto interface is R2-ready — enabling
-- R2 in the dashboard swaps storage without touching callers.
ALTER TABLE stickers ADD COLUMN placement TEXT;   -- combi | fijo
ALTER TABLE stickers ADD COLUMN lat REAL;
ALTER TABLE stickers ADD COLUMN lon REAL;
ALTER TABLE stickers ADD COLUMN photo_id INTEGER;

CREATE TABLE IF NOT EXISTS sticker_photos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sticker_id TEXT NOT NULL,
  mime TEXT NOT NULL DEFAULT 'image/jpeg',
  data BLOB NOT NULL,
  taken_by TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sticker_photos ON sticker_photos (sticker_id);
