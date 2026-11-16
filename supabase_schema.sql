-- ========================================================================
-- MSANII A&R INTELLIGENCE PLATFORM · SUPABASE POSTGRESQL SCHEMA
-- Ready for direct execution in Supabase SQL Editor
-- ========================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. CORE USERS & ACCESS
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    pw_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'reviewer', 'viewer')),
    active INTEGER NOT NULL DEFAULT 1,
    totp_secret BYTEA,
    mfa_enabled INTEGER NOT NULL DEFAULT 0,
    created_at DOUBLE PRECISION NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW())
);

CREATE TABLE IF NOT EXISTS access_requests (
    id BIGSERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    organization TEXT,
    role_title TEXT,
    region TEXT,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
    token TEXT UNIQUE NOT NULL,
    created_at DOUBLE PRECISION NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW()),
    reviewed_at DOUBLE PRECISION,
    reviewed_by BIGINT REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS invites (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    role TEXT NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,
    expires_at DOUBLE PRECISION NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    invited_by BIGINT REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    sid_hash TEXT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    csrf TEXT NOT NULL,
    created_at DOUBLE PRECISION NOT NULL,
    expires_at DOUBLE PRECISION NOT NULL,
    ua TEXT
);

-- 3. ARTISTS & ACOUSTIC DOSSIERS
CREATE TABLE IF NOT EXISTS artists (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL DEFAULT '',
    city TEXT,
    genres TEXT NOT NULL DEFAULT '[]',
    stage TEXT DEFAULT 'Upcoming',
    begin_year INTEGER,
    ids TEXT NOT NULL DEFAULT '{}',
    first_seen DOUBLE PRECISION NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW()),
    last_signal DOUBLE PRECISION,
    bio TEXT,
    story TEXT,
    image_url TEXT,
    links TEXT NOT NULL DEFAULT '{}',
    enriched_at DOUBLE PRECISION,
    UNIQUE(name, country)
);

CREATE TABLE IF NOT EXISTS observations (
    id BIGSERIAL PRIMARY KEY,
    artist_id BIGINT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    ts DOUBLE PRECISION NOT NULL,
    metric TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    source TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_obs ON observations(artist_id, metric, ts);

CREATE TABLE IF NOT EXISTS reviews (
    id BIGSERIAL PRIMARY KEY,
    artist_id BIGINT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id),
    scores TEXT NOT NULL,
    note TEXT,
    ts DOUBLE PRECISION NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW())
);

CREATE TABLE IF NOT EXISTS decisions (
    id BIGSERIAL PRIMARY KEY,
    artist_id BIGINT NOT NULL REFERENCES artists(id),
    user_id BIGINT NOT NULL REFERENCES users(id),
    action TEXT NOT NULL,
    rationale TEXT NOT NULL,
    owner TEXT,
    follow_up TEXT,
    tier TEXT,
    ts DOUBLE PRECISION NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW()),
    sig TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    id BIGSERIAL PRIMARY KEY,
    kind TEXT NOT NULL,
    started DOUBLE PRECISION NOT NULL,
    finished DOUBLE PRECISION,
    found INTEGER DEFAULT 0,
    new_count INTEGER DEFAULT 0,
    errors TEXT NOT NULL DEFAULT '[]',
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    updated_at DOUBLE PRECISION NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW())
);

CREATE TABLE IF NOT EXISTS credentials (
    provider TEXT PRIMARY KEY,
    ciphertext BYTEA NOT NULL,
    updated_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    updated_at DOUBLE PRECISION NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW())
);

CREATE TABLE IF NOT EXISTS measurements (
    id BIGSERIAL PRIMARY KEY,
    artist_id BIGINT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    provenance TEXT NOT NULL,
    ts DOUBLE PRECISION NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW())
);

CREATE TABLE IF NOT EXISTS uploads (
    id BIGSERIAL PRIMARY KEY,
    artist_id BIGINT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    ts DOUBLE PRECISION NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW())
);

CREATE TABLE IF NOT EXISTS tasks (
    id BIGSERIAL PRIMARY KEY,
    artist_id BIGINT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    created DOUBLE PRECISION NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW()),
    done INTEGER NOT NULL DEFAULT 0,
    done_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    done_at DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS tracks (
    id BIGSERIAL PRIMARY KEY,
    artist_id BIGINT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    album TEXT,
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    preview_url TEXT,
    cover_url TEXT,
    duration INTEGER,
    popularity DOUBLE PRECISION,
    release_date TEXT,
    url TEXT,
    UNIQUE(artist_id, source, source_id)
);

CREATE TABLE IF NOT EXISTS media (
    id BIGSERIAL PRIMARY KEY,
    artist_id BIGINT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    path TEXT,
    sha256 TEXT,
    status TEXT NOT NULL,
    result TEXT NOT NULL DEFAULT '{}',
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    ts DOUBLE PRECISION NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW())
);

CREATE TABLE IF NOT EXISTS provider_stats (
    provider TEXT PRIMARY KEY,
    calls INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0,
    last_ok DOUBLE PRECISION,
    last_error TEXT,
    last_error_at DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS audit (
    id BIGSERIAL PRIMARY KEY,
    ts DOUBLE PRECISION NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW()),
    user_id BIGINT,
    ip TEXT,
    event TEXT NOT NULL,
    detail TEXT NOT NULL,
    prev TEXT NOT NULL,
    hash TEXT NOT NULL
);

-- 4. ROW LEVEL SECURITY (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE access_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE artists ENABLE ROW LEVEL SECURITY;
ALTER TABLE observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE tracks ENABLE ROW LEVEL SECURITY;
ALTER TABLE decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY service_role_all ON users FOR ALL USING (true);
CREATE POLICY service_role_artists ON artists FOR ALL USING (true);
CREATE POLICY service_role_access ON access_requests FOR ALL USING (true);
CREATE POLICY service_role_obs ON observations FOR ALL USING (true);
CREATE POLICY service_role_tracks ON tracks FOR ALL USING (true);
CREATE POLICY service_role_decisions ON decisions FOR ALL USING (true);
CREATE POLICY service_role_audit ON audit FOR ALL USING (true);
