-- Per-day service schedule on combi_lines, edited from the iPhone admin app.
-- Weekday reuses the existing first_run / last_run / headway_min columns;
-- these add Saturday and Sunday (start, end, interval-minutes-between-combis).
ALTER TABLE combi_lines ADD COLUMN sat_first TEXT;      -- 'HH:MM'
ALTER TABLE combi_lines ADD COLUMN sat_last TEXT;
ALTER TABLE combi_lines ADD COLUMN sat_headway INTEGER; -- minutes between combis (Sat)
ALTER TABLE combi_lines ADD COLUMN sun_first TEXT;
ALTER TABLE combi_lines ADD COLUMN sun_last TEXT;
ALTER TABLE combi_lines ADD COLUMN sun_headway INTEGER; -- minutes between combis (Sun)
