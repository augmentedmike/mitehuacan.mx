-- Sponsorship module (PRD §4 + contracts): sponsor -> locations -> contract
-- (X months × X MXN per location) -> click-to-sign -> payments (SPEI transfer
-- or cash). The public map's sponsor pins will read from these tables once the
-- publication rules land; until then pins stay on the static sponsors.js seed.
CREATE TABLE IF NOT EXISTS sponsors (
  slug TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  contact_name TEXT,
  contact_email TEXT,
  phone TEXT,
  tier TEXT NOT NULL DEFAULT 'paid',        -- paid | barter
  notes TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sponsor_locations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sponsor_slug TEXT NOT NULL,
  label TEXT,                               -- "sucursal centro", "1 Oriente"
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sponsor_locations ON sponsor_locations (sponsor_slug);

CREATE TABLE IF NOT EXISTS contracts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sponsor_slug TEXT NOT NULL,
  token TEXT UNIQUE NOT NULL,               -- signing-link token (/firmar?c=...)
  months INTEGER NOT NULL,
  price_per_location_mxn REAL NOT NULL,
  n_locations INTEGER NOT NULL,
  total_mxn REAL NOT NULL,
  start_date TEXT,
  status TEXT NOT NULL DEFAULT 'draft',     -- draft | sent | signed | cancelled
  sent_to TEXT, sent_at TEXT,
  signed_name TEXT, signed_at TEXT, signed_ip TEXT, signed_ua TEXT,
  created_by TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  contract_id INTEGER NOT NULL,
  amount_mxn REAL NOT NULL,
  method TEXT NOT NULL DEFAULT 'transferencia',  -- transferencia | efectivo | otro
  reference TEXT,                                -- SPEI clave de rastreo / folio
  paid_at TEXT NOT NULL,
  notes TEXT,
  recorded_by TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_payments_contract ON payments (contract_id);

-- small config the client-facing contract page needs (bank/SPEI details, provider name)
CREATE TABLE IF NOT EXISTS settings (
  k TEXT PRIMARY KEY,
  v TEXT
);
