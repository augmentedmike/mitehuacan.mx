-- Sponsor logo for the data-entry app (iOS): a small downscaled PNG stored as a
-- data: URL (or an asset path). Rendered on the admin list and, later, on the map
-- pin. Kept in the sponsors row so a single upsert carries identity + logo together.
ALTER TABLE sponsors ADD COLUMN logo TEXT;
