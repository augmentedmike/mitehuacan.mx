-- Review queue for self-registered businesses (the admin app's "Negocios" tab).
-- Listings auto-publish (active=1) and start reviewed=0 (in the queue). The admin
-- app then Approves -> reviewed=1 (stays live, just leaves the queue) or Rejects ->
-- reviewed=1 + active=0 (goes dark, leaves the queue). `reviewed` = "seen by admin".
ALTER TABLE negocios ADD COLUMN reviewed INTEGER NOT NULL DEFAULT 0;
CREATE INDEX IF NOT EXISTS idx_negocios_reviewed ON negocios (reviewed, active);
