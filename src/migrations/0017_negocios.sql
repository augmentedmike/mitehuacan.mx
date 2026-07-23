-- Self-serve business & service directory (Phase 2). A business scans the QR
-- flyer -> /combis/alta -> fills this form itself (no salesperson). Rows land
-- here via POST /api/negocios (functions/api/negocios.js). Publish-first: active=1
-- on submit; admin can soft-toggle active=0 to hide spam. Feeds the map directory
-- AND the fiestas vendor feed (fiesta=1). Distinct from `places` (OSM-gap search
-- index, field-captured) and `sponsors` (paid pins) — see PRD-phase2-fiesta-vendor-directory.md.
CREATE TABLE IF NOT EXISTS negocios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  category TEXT NOT NULL,                 -- primary category (from the controlled list)
  category2 TEXT,                         -- optional 2nd category (max 2 total)
  category_other TEXT,                    -- free text when category = 'otro'
  description TEXT,                       -- qué ofrece
  owner_name TEXT,                        -- nombre del contacto/dueño
  phone TEXT,                             -- normalized digits
  whatsapp TEXT,                          -- normalized digits — the key contact
  email TEXT,
  facebook TEXT,
  instagram TEXT,
  website TEXT,
  has_location INTEGER NOT NULL DEFAULT 0,-- 1 = tiene local físico
  lat REAL,
  lon REAL,
  address TEXT,                           -- calle y número
  colonia TEXT,
  municipio TEXT DEFAULT 'Tehuacán',
  service_area TEXT,                      -- zonas que atiende (negocios a domicilio)
  hours TEXT,                             -- horario (texto libre por ahora)
  price_from REAL,                        -- precio desde (opcional)
  price_note TEXT,                        -- "por persona", "por evento"...
  fiesta INTEGER NOT NULL DEFAULT 0,      -- ofrece servicios para fiestas (feed de fiestas)
  tags TEXT,                              -- palabras extra de búsqueda
  edit_token TEXT UNIQUE NOT NULL,        -- clave para editar (link retornable, futuro)
  source TEXT NOT NULL DEFAULT 'self',    -- self | field | denue-claimed
  qr_batch TEXT,                          -- de qué flyer/QR vino
  added_by TEXT,                          -- field_token del ayudante, si aplica
  active INTEGER NOT NULL DEFAULT 1,      -- publish-first; 0 = oculto (moderación)
  verified INTEGER NOT NULL DEFAULT 0,    -- sello de confianza (admin)
  boosted_until TEXT,                     -- Destacado activo hasta (Fase 4)
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_negocios_active ON negocios (active);
CREATE INDEX IF NOT EXISTS idx_negocios_category ON negocios (category);
CREATE INDEX IF NOT EXISTS idx_negocios_fiesta ON negocios (fiesta, active);
CREATE INDEX IF NOT EXISTS idx_negocios_edit_token ON negocios (edit_token);

-- Photos live apart (upload needs storage; wired later). Schema-ready now.
CREATE TABLE IF NOT EXISTS negocio_photos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  negocio_id INTEGER NOT NULL,
  url TEXT NOT NULL,
  sort INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_negocio_photos ON negocio_photos (negocio_id);
