import os, json, time, sqlite3, hashlib
from flask import g, current_app, request, has_request_context

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, pw_hash TEXT, role TEXT NOT NULL CHECK(role IN('admin','reviewer','viewer')), active INTEGER NOT NULL DEFAULT 1, totp_secret BLOB, mfa_enabled INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS invites(id INTEGER PRIMARY KEY, email TEXT NOT NULL, role TEXT NOT NULL, token_hash TEXT UNIQUE NOT NULL, expires_at REAL NOT NULL, used INTEGER NOT NULL DEFAULT 0, invited_by INTEGER);
CREATE TABLE IF NOT EXISTS sessions(sid_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, csrf TEXT NOT NULL, created_at REAL NOT NULL, expires_at REAL NOT NULL, ua TEXT);
CREATE TABLE IF NOT EXISTS artists(id INTEGER PRIMARY KEY, name TEXT NOT NULL, country TEXT NOT NULL DEFAULT '', city TEXT, genres TEXT NOT NULL DEFAULT '[]', stage TEXT, begin_year INTEGER, ids TEXT NOT NULL DEFAULT '{}', first_seen REAL NOT NULL, last_signal REAL, bio TEXT, story TEXT, image_url TEXT, links TEXT NOT NULL DEFAULT '{}', enriched_at REAL, UNIQUE(name,country));
CREATE TABLE IF NOT EXISTS observations(id INTEGER PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, ts REAL NOT NULL, metric TEXT NOT NULL, value REAL NOT NULL, source TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_obs ON observations(artist_id,metric,ts);
CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, user_id INTEGER NOT NULL REFERENCES users(id), scores TEXT NOT NULL, note TEXT, ts REAL NOT NULL);
CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id), user_id INTEGER NOT NULL REFERENCES users(id), action TEXT NOT NULL, rationale TEXT NOT NULL, owner TEXT, follow_up TEXT, tier TEXT, ts REAL NOT NULL, sig TEXT);
CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY, kind TEXT NOT NULL, started REAL NOT NULL, finished REAL, found INTEGER DEFAULT 0, new_count INTEGER DEFAULT 0, errors TEXT NOT NULL DEFAULT '[]', user_id INTEGER);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_by INTEGER, updated_at REAL);
CREATE TABLE IF NOT EXISTS credentials(provider TEXT PRIMARY KEY, ciphertext BLOB NOT NULL, updated_by INTEGER, updated_at REAL);
CREATE TABLE IF NOT EXISTS measurements(id INTEGER PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, name TEXT NOT NULL, value TEXT NOT NULL, confidence REAL NOT NULL, provenance TEXT NOT NULL, ts REAL NOT NULL);
CREATE TABLE IF NOT EXISTS uploads(id INTEGER PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, path TEXT NOT NULL, sha256 TEXT NOT NULL, user_id INTEGER, ts REAL NOT NULL);
CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, kind TEXT NOT NULL, created REAL NOT NULL, done INTEGER NOT NULL DEFAULT 0, done_by INTEGER, done_at REAL);
CREATE TABLE IF NOT EXISTS tracks(id INTEGER PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, title TEXT NOT NULL, album TEXT, source TEXT NOT NULL, source_id TEXT NOT NULL, preview_url TEXT, cover_url TEXT, duration INTEGER, popularity REAL, release_date TEXT, url TEXT, UNIQUE(artist_id,source,source_id));
CREATE TABLE IF NOT EXISTS media(id INTEGER PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, kind TEXT NOT NULL, title TEXT NOT NULL, url TEXT, path TEXT, sha256 TEXT, status TEXT NOT NULL, result TEXT NOT NULL DEFAULT '{}', user_id INTEGER, ts REAL NOT NULL);
CREATE TABLE IF NOT EXISTS provider_stats(provider TEXT PRIMARY KEY, calls INTEGER NOT NULL DEFAULT 0, errors INTEGER NOT NULL DEFAULT 0, last_ok REAL, last_error TEXT, last_error_at REAL);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, ts REAL NOT NULL, user_id INTEGER, ip TEXT, event TEXT NOT NULL, detail TEXT NOT NULL, prev TEXT NOT NULL, hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS access_requests(id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, email TEXT NOT NULL, organization TEXT, role_title TEXT, region TEXT, notes TEXT, status TEXT NOT NULL DEFAULT 'pending', token TEXT UNIQUE NOT NULL, created_at REAL NOT NULL, reviewed_at REAL, reviewed_by INTEGER);
"""

class PostgresCursorWrapper:
    def __init__(self, cur):
        self.cur = cur
        self.lastrowid = None
        self.rowcount = cur.rowcount
    def fetchone(self):
        row = self.cur.fetchone()
        if row is None: return None
        return dict(row)
    def fetchall(self):
        return [dict(r) for r in self.cur.fetchall()]
    def __iter__(self):
        for r in self.cur:
            yield dict(r)

class PostgresConnectionWrapper:
    def __init__(self, raw_conn):
        self.conn = raw_conn
    def execute(self, sql, params=None):
        cur = self.conn.cursor()
        p_sql = sql
        # Adapt ? to %s for psycopg2/pg8000
        if params is not None:
            p_sql = p_sql.replace("?", "%s")
        # Handle lastrowid on insert
        needs_returning = "INSERT INTO" in p_sql.upper() and "RETURNING" not in p_sql.upper()
        if needs_returning:
            p_sql = p_sql.rstrip(";") + " RETURNING id"
        cur.execute(p_sql, params or ())
        wrap = PostgresCursorWrapper(cur)
        if needs_returning:
            try:
                r = cur.fetchone()
                if r:
                    wrap.lastrowid = r[0] if isinstance(r, (list, tuple)) else r.get("id")
            except Exception:
                pass
        return wrap
    def commit(self):
        self.conn.commit()
    def rollback(self):
        self.conn.rollback()
    def close(self):
        self.conn.close()

def get_supabase_url():
    return os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")

def db():
    if "db" not in g:
        pg_url = get_supabase_url()
        if pg_url and (pg_url.startswith("postgres://") or pg_url.startswith("postgresql://")):
            try:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                raw = psycopg2.connect(pg_url, cursor_factory=RealDictCursor, connect_timeout=10)
                g.db = PostgresConnectionWrapper(raw)
                return g.db
            except Exception:
                pass
        # SQLite local fallback with WAL mode
        g.db = sqlite3.connect(current_app.config["DB"], timeout=15)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

def close_db(e=None):
    d = g.pop("db", None)
    if d: d.close()

MIGRATIONS = [
    ("artists", "bio", "TEXT"),
    ("artists", "story", "TEXT"),
    ("artists", "image_url", "TEXT"),
    ("artists", "links", "TEXT NOT NULL DEFAULT '{}'"),
    ("artists", "enriched_at", "REAL"),
    ("decisions", "sig", "TEXT"),
    ("access_requests", "organization", "TEXT")
]

def init_db(path):
    pg_url = get_supabase_url()
    if pg_url and (pg_url.startswith("postgres://") or pg_url.startswith("postgresql://")):
        # Supabase PostgreSQL schema initialized via migration script
        return
    c = sqlite3.connect(path); c.execute("PRAGMA journal_mode=WAL"); c.executescript(SCHEMA)
    for t, col, decl in MIGRATIONS:      # upgrade databases created by earlier versions
        try:
            if col not in [r[1] for r in c.execute(f"PRAGMA table_info({t})")]:
                c.execute(f"ALTER TABLE {t} ADD COLUMN {col} {decl}")
        except Exception:
            pass
    c.commit(); c.close()
    try: os.chmod(path, 0o600)
    except OSError: pass

def _h(prev, ts, uid, ev, det): return hashlib.sha256(f"{prev}|{ts!r}|{uid}|{ev}|{det}".encode()).hexdigest()

def audit(event, detail=None, user_id=None):
    """Append-only, hash-chained audit record. Never put secrets in `detail`."""
    d = db(); ip = request.remote_addr if has_request_context() else "job"
    try:
        d.commit()
    except Exception: pass
    last = d.execute("SELECT hash FROM audit ORDER BY id DESC LIMIT 1").fetchone()
    prev = last["hash"] if last else "0" * 64; ts = time.time()
    det = json.dumps(detail or {}, sort_keys=True, default=str)
    d.execute("INSERT INTO audit(ts,user_id,ip,event,detail,prev,hash) VALUES(?,?,?,?,?,?,?)", (ts, user_id, ip, event, det, prev, _h(prev, ts, user_id, event, det)))
    d.commit()

def verify_audit():
    """Returns None if the chain is intact, else the id of the first broken record."""
    prev = "0" * 64
    for r in db().execute("SELECT * FROM audit ORDER BY id"):
        h = _h(prev, r["ts"], r["user_id"], r["event"], r["detail"])
        if r["prev"] != prev or r["hash"] != h: return r["id"]
        prev = h
    return None
