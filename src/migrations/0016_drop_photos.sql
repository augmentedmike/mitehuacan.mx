-- The camera reads the placed QR to identify the sticker (jsQR in the admin
-- page) — no images are ever stored or hosted. Drop the photo table from 0015;
-- the stickers.placement/lat/lon columns stay (they ARE the location link).
DROP TABLE IF EXISTS sticker_photos;
