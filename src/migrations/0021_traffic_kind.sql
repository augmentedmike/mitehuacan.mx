-- silo bots + exclude the operator from real-user analytics.
-- kind: 'user' (a real visitor) | 'bot' (headless/crawler/CLI/preview-deploy) |
-- 'internal' (the operator's own device — opts in via ?internal=1 → qint cookie).
-- Written at hit/event time (functions/api/pv.js, _middleware.js, api/evento.js);
-- /system counts users only and shows the bot/internal split separately.
ALTER TABLE hits   ADD COLUMN kind TEXT NOT NULL DEFAULT 'user';
ALTER TABLE events ADD COLUMN kind TEXT NOT NULL DEFAULT 'user';
CREATE INDEX IF NOT EXISTS idx_hits_kind   ON hits (kind);
CREATE INDEX IF NOT EXISTS idx_events_kind ON events (kind);

-- backfill existing rows: flag the obvious bots by user-agent / preview-deploy
-- referer. (internal stays 'user' — the operator opts in going forward.)
UPDATE hits SET kind='bot' WHERE kind='user' AND (
  ua IS NULL OR trim(ua)='' OR
  ua LIKE '%HeadlessChrome%' OR lower(ua) LIKE '%bot%' OR lower(ua) LIKE '%crawl%' OR
  lower(ua) LIKE '%spider%' OR lower(ua) LIKE '%slurp%' OR lower(ua) LIKE '%curl%' OR
  lower(ua) LIKE '%wget%' OR lower(ua) LIKE '%python%' OR lower(ua) LIKE '%go-http%' OR
  lower(ua) LIKE '%okhttp%' OR lower(ua) LIKE 'java/%' OR lower(ua) LIKE '%libwww%' OR
  lower(ua) LIKE '%phantom%' OR lower(ua) LIKE '%puppeteer%' OR lower(ua) LIKE '%playwright%' OR
  lower(ua) LIKE '%lighthouse%' OR lower(ua) LIKE '%node-fetch%' OR lower(ua) LIKE '%scrapy%' OR
  lower(ua) LIKE '%semrush%' OR lower(ua) LIKE '%ahrefs%' OR lower(ua) LIKE '%compatible)%' OR
  referer LIKE '%.vercel.app%'
);
UPDATE events SET kind='bot' WHERE kind='user' AND (
  ua IS NULL OR trim(ua)='' OR
  ua LIKE '%HeadlessChrome%' OR lower(ua) LIKE '%bot%' OR lower(ua) LIKE '%crawl%' OR
  lower(ua) LIKE '%curl%' OR lower(ua) LIKE '%python%' OR lower(ua) LIKE '%headless%' OR
  lower(ua) LIKE '%puppeteer%' OR lower(ua) LIKE '%playwright%'
);
