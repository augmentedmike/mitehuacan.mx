-- Portal feedback + bug reports (functions/api/feedback.js). Everything goes to
-- D1 — no email, no github. kind = idea | bug. Reviewed in the admin.
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  kind TEXT NOT NULL DEFAULT 'idea',   -- idea | bug
  message TEXT NOT NULL,
  contact TEXT,                        -- optional WhatsApp / name
  page TEXT,                           -- where it was sent from
  ip_hash TEXT NOT NULL,               -- sha256 of IP, rate-limit only
  status TEXT NOT NULL DEFAULT 'new'   -- new | reviewing | done
);
CREATE INDEX IF NOT EXISTS idx_feedback_ip_day ON feedback (ip_hash, created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_kind ON feedback (kind, status);
