-- Route recorder (/grabar): one row per recorded ride. The telemetry itself
-- lands in the existing positions table with device = 'rec-' || id, so the
-- /map editor loads recordings exactly like Traccar devices — zero changes.
CREATE TABLE IF NOT EXISTS ride_sessions (
  id TEXT PRIMARY KEY,               -- r<epoch36><rand>, generated client-side
  line_slug TEXT,                    -- combi_lines.slug it was recorded for
  name TEXT,                         -- free label when the line doesn't exist yet
  recorded_by TEXT,                  -- person credited (field token name / admin)
  started_at TEXT NOT NULL,
  ended_at TEXT,
  n_points INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'recording',  -- recording | done | discarded
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- taps of the PARADA button while riding: real stop locations, future stop pins
CREATE TABLE IF NOT EXISTS stop_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  fix_ts TEXT NOT NULL,
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  kind TEXT NOT NULL DEFAULT 'parada',
  label TEXT
);
CREATE INDEX IF NOT EXISTS idx_stop_events_session ON stop_events (session_id);
