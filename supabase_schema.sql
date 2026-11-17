-- MSANII PostgreSQL / Supabase schema. Idempotent: safe to run repeatedly (SQL editor, `python manage.py migrate-pg`, or a notebook cell).
-- Generated from msanii/db.py SCHEMA; keep the two in sync.
--
-- SECURITY MODEL: the Flask backend connects with its own database role (the `postgres` owner), which bypasses row level security.
-- Supabase also exposes the `public` schema through its REST/GraphQL Data API using the anon and authenticated roles. This app never uses
-- that API, so every table gets RLS ENABLED WITH NO POLICIES (deny by default) and all privileges are revoked from those roles.
-- Do NOT add `USING (true)` policies: they apply to every role and would expose password hashes, sessions and encrypted credentials.

CREATE TABLE IF NOT EXISTS users(id SERIAL PRIMARY KEY, email TEXT UNIQUE NOT NULL, pw_hash TEXT, role TEXT NOT NULL CHECK(role IN('admin','reviewer','viewer')), active INTEGER NOT NULL DEFAULT 1, totp_secret BYTEA, mfa_enabled INTEGER NOT NULL DEFAULT 0, created_at DOUBLE PRECISION NOT NULL);
CREATE TABLE IF NOT EXISTS invites(id SERIAL PRIMARY KEY, email TEXT NOT NULL, role TEXT NOT NULL, token_hash TEXT UNIQUE NOT NULL, expires_at DOUBLE PRECISION NOT NULL, used INTEGER NOT NULL DEFAULT 0, invited_by INTEGER);
CREATE TABLE IF NOT EXISTS sessions(sid_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, csrf TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL, expires_at DOUBLE PRECISION NOT NULL, ua TEXT);
CREATE TABLE IF NOT EXISTS artists(id SERIAL PRIMARY KEY, name TEXT NOT NULL, country TEXT NOT NULL DEFAULT '', city TEXT, genres TEXT NOT NULL DEFAULT '[]', stage TEXT, begin_year INTEGER, ids TEXT NOT NULL DEFAULT '{}', first_seen DOUBLE PRECISION NOT NULL, last_signal DOUBLE PRECISION, bio TEXT, story TEXT, image_url TEXT, links TEXT NOT NULL DEFAULT '{}', enriched_at DOUBLE PRECISION, UNIQUE(name,country));
CREATE TABLE IF NOT EXISTS observations(id SERIAL PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, ts DOUBLE PRECISION NOT NULL, metric TEXT NOT NULL, value DOUBLE PRECISION NOT NULL, source TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_obs ON observations(artist_id,metric,ts);
CREATE TABLE IF NOT EXISTS reviews(id SERIAL PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, user_id INTEGER NOT NULL REFERENCES users(id), scores TEXT NOT NULL, note TEXT, ts DOUBLE PRECISION NOT NULL);
CREATE TABLE IF NOT EXISTS decisions(id SERIAL PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id), user_id INTEGER NOT NULL REFERENCES users(id), action TEXT NOT NULL, rationale TEXT NOT NULL, owner TEXT, follow_up TEXT, tier TEXT, ts DOUBLE PRECISION NOT NULL, sig TEXT);
CREATE TABLE IF NOT EXISTS runs(id SERIAL PRIMARY KEY, kind TEXT NOT NULL, started DOUBLE PRECISION NOT NULL, finished DOUBLE PRECISION, found INTEGER DEFAULT 0, new_count INTEGER DEFAULT 0, errors TEXT NOT NULL DEFAULT '[]', user_id INTEGER);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_by INTEGER, updated_at DOUBLE PRECISION);
CREATE TABLE IF NOT EXISTS credentials(provider TEXT PRIMARY KEY, ciphertext BYTEA NOT NULL, updated_by INTEGER, updated_at DOUBLE PRECISION);
CREATE TABLE IF NOT EXISTS measurements(id SERIAL PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, name TEXT NOT NULL, value TEXT NOT NULL, confidence DOUBLE PRECISION NOT NULL, provenance TEXT NOT NULL, ts DOUBLE PRECISION NOT NULL, media_id INTEGER);
CREATE TABLE IF NOT EXISTS uploads(id SERIAL PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, path TEXT NOT NULL, sha256 TEXT NOT NULL, user_id INTEGER, ts DOUBLE PRECISION NOT NULL);
CREATE TABLE IF NOT EXISTS tasks(id SERIAL PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, kind TEXT NOT NULL, created DOUBLE PRECISION NOT NULL, done INTEGER NOT NULL DEFAULT 0, done_by INTEGER, done_at DOUBLE PRECISION);
CREATE TABLE IF NOT EXISTS tracks(id SERIAL PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, title TEXT NOT NULL, album TEXT, source TEXT NOT NULL, source_id TEXT NOT NULL, preview_url TEXT, cover_url TEXT, duration INTEGER, popularity DOUBLE PRECISION, release_date TEXT, url TEXT, UNIQUE(artist_id,source,source_id));
CREATE TABLE IF NOT EXISTS media(id SERIAL PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, kind TEXT NOT NULL, title TEXT NOT NULL, url TEXT, path TEXT, sha256 TEXT, status TEXT NOT NULL, result TEXT NOT NULL DEFAULT '{}', user_id INTEGER, ts DOUBLE PRECISION NOT NULL);
CREATE TABLE IF NOT EXISTS provider_stats(provider TEXT PRIMARY KEY, calls INTEGER NOT NULL DEFAULT 0, errors INTEGER NOT NULL DEFAULT 0, last_ok DOUBLE PRECISION, last_error TEXT, last_error_at DOUBLE PRECISION);
CREATE TABLE IF NOT EXISTS audit(id SERIAL PRIMARY KEY, ts DOUBLE PRECISION NOT NULL, user_id INTEGER, ip TEXT, event TEXT NOT NULL, detail TEXT NOT NULL, prev TEXT NOT NULL, hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS access_requests(id SERIAL PRIMARY KEY, full_name TEXT NOT NULL, email TEXT NOT NULL, organization TEXT, role_title TEXT, region TEXT, notes TEXT, status TEXT NOT NULL DEFAULT 'pending', token TEXT UNIQUE NOT NULL, created_at DOUBLE PRECISION NOT NULL, reviewed_at DOUBLE PRECISION, reviewed_by INTEGER);

-- upgrades for databases created by earlier versions
ALTER TABLE artists ADD COLUMN IF NOT EXISTS bio TEXT;
ALTER TABLE artists ADD COLUMN IF NOT EXISTS story TEXT;
ALTER TABLE artists ADD COLUMN IF NOT EXISTS image_url TEXT;
ALTER TABLE artists ADD COLUMN IF NOT EXISTS links TEXT NOT NULL DEFAULT '{}';
ALTER TABLE artists ADD COLUMN IF NOT EXISTS enriched_at DOUBLE PRECISION;
ALTER TABLE decisions ADD COLUMN IF NOT EXISTS sig TEXT;
ALTER TABLE access_requests ADD COLUMN IF NOT EXISTS organization TEXT;
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS media_id INTEGER;

-- indexes for the app's access paths
CREATE INDEX IF NOT EXISTS ix_reviews_artist ON reviews(artist_id);
CREATE INDEX IF NOT EXISTS ix_decisions_artist_ts ON decisions(artist_id, ts DESC);
CREATE INDEX IF NOT EXISTS ix_tracks_artist ON tracks(artist_id);
CREATE INDEX IF NOT EXISTS ix_media_artist ON media(artist_id, ts DESC);
CREATE INDEX IF NOT EXISTS ix_measurements_artist ON measurements(artist_id);
CREATE INDEX IF NOT EXISTS ix_measurements_media ON measurements(media_id);
CREATE INDEX IF NOT EXISTS ix_tasks_artist_kind ON tasks(artist_id, kind);
CREATE INDEX IF NOT EXISTS ix_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS ix_sessions_expiry ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS ix_artists_country ON artists(country);
CREATE INDEX IF NOT EXISTS ix_access_requests_status ON access_requests(status, created_at DESC);

-- row level security: ON for every table, no policies

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON users;
ALTER TABLE invites ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON invites;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON sessions;
ALTER TABLE artists ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON artists;
ALTER TABLE observations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON observations;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON reviews;
ALTER TABLE decisions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON decisions;
ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON runs;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON settings;
ALTER TABLE credentials ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON credentials;
ALTER TABLE measurements ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON measurements;
ALTER TABLE uploads ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON uploads;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON tasks;
ALTER TABLE tracks ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON tracks;
ALTER TABLE media ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON media;
ALTER TABLE provider_stats ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON provider_stats;
ALTER TABLE audit ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON audit;
ALTER TABLE access_requests ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS service_role_all ON access_requests;

DO $$
DECLARE r TEXT;
BEGIN
  FOREACH r IN ARRAY ARRAY['anon', 'authenticated'] LOOP
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
      EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA public FROM %I', r);
      EXECUTE format('REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM %I', r);
      EXECUTE format('REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM %I', r);
      EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM %I', r);
      EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM %I', r);
    END IF;
  END LOOP;
END $$;
