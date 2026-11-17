import os, re, json, time, sqlite3, hashlib, logging, threading
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
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
CREATE TABLE IF NOT EXISTS measurements(id INTEGER PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, name TEXT NOT NULL, value TEXT NOT NULL, confidence REAL NOT NULL, provenance TEXT NOT NULL, ts REAL NOT NULL, media_id INTEGER);
CREATE TABLE IF NOT EXISTS uploads(id INTEGER PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, path TEXT NOT NULL, sha256 TEXT NOT NULL, user_id INTEGER, ts REAL NOT NULL);
CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, kind TEXT NOT NULL, created REAL NOT NULL, done INTEGER NOT NULL DEFAULT 0, done_by INTEGER, done_at REAL);
CREATE TABLE IF NOT EXISTS tracks(id INTEGER PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, title TEXT NOT NULL, album TEXT, source TEXT NOT NULL, source_id TEXT NOT NULL, preview_url TEXT, cover_url TEXT, duration INTEGER, popularity REAL, release_date TEXT, url TEXT, UNIQUE(artist_id,source,source_id));
CREATE TABLE IF NOT EXISTS media(id INTEGER PRIMARY KEY, artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE, kind TEXT NOT NULL, title TEXT NOT NULL, url TEXT, path TEXT, sha256 TEXT, status TEXT NOT NULL, result TEXT NOT NULL DEFAULT '{}', user_id INTEGER, ts REAL NOT NULL);
CREATE TABLE IF NOT EXISTS provider_stats(provider TEXT PRIMARY KEY, calls INTEGER NOT NULL DEFAULT 0, errors INTEGER NOT NULL DEFAULT 0, last_ok REAL, last_error TEXT, last_error_at REAL);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, ts REAL NOT NULL, user_id INTEGER, ip TEXT, event TEXT NOT NULL, detail TEXT NOT NULL, prev TEXT NOT NULL, hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS access_requests(id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, email TEXT NOT NULL, organization TEXT, role_title TEXT, region TEXT, notes TEXT, status TEXT NOT NULL DEFAULT 'pending', token TEXT UNIQUE NOT NULL, created_at REAL NOT NULL, reviewed_at REAL, reviewed_by INTEGER);
"""

log = logging.getLogger("msanii.db")

# Tables that have an integer `id` primary key. Only these get `RETURNING id` on PostgreSQL
# (settings, credentials, provider_stats and sessions are keyed by text and have no id column).
ID_TABLES = {"users", "invites", "artists", "observations", "reviews", "decisions", "runs", "measurements", "uploads", "tasks", "tracks", "media", "audit", "access_requests"}
_INSERT = re.compile(r"^\s*INSERT\s+INTO\s+(\w+)", re.I)


class Row(tuple):
    """sqlite3.Row look-alike for PostgreSQL: supports row[0], row["col"], row.keys() and dict(row)."""
    def __new__(cls, values, keys):
        o = super().__new__(cls, values); o._k = list(keys); return o
    def keys(self): return list(self._k)
    def __getitem__(self, i):
        if isinstance(i, str):
            try: return tuple.__getitem__(self, self._k.index(i))
            except ValueError: raise KeyError(i)
        return tuple.__getitem__(self, i)


def _plain(v):
    return bytes(v) if isinstance(v, memoryview) else v     # psycopg2 returns BYTEA as memoryview


class PgCursor:
    def __init__(self, cur, returning=False):
        self.cur, self.rowcount, self.lastrowid = cur, cur.rowcount, None
        self._keys = [c[0] for c in cur.description] if cur.description else []
        if returning:
            try:
                r = cur.fetchone(); self.lastrowid = r[0] if r else None
            except Exception: pass
    def _row(self, r): return Row([_plain(x) for x in r], self._keys)
    def fetchone(self):
        r = self.cur.fetchone(); return None if r is None else self._row(r)
    def fetchall(self): return [self._row(r) for r in self.cur.fetchall()]
    def __iter__(self):
        for r in self.cur: yield self._row(r)


class PgConnection:
    """Thin adapter so the app's SQLite-style SQL (`?` placeholders, lastrowid, executemany) runs on PostgreSQL."""
    def __init__(self, raw): self.conn = raw
    @staticmethod
    def _sql(sql): return sql.replace("%", "%%").replace("?", "%s")
    def execute(self, sql, params=None):
        m = _INSERT.match(sql); ret = bool(m and m.group(1).lower() in ID_TABLES and "returning" not in sql.lower())
        q = self._sql(sql.strip().rstrip(";")) + (" RETURNING id" if ret else "")
        cur = self.conn.cursor()
        try: cur.execute(q, tuple(params) if params is not None else ())
        except Exception: self.conn.rollback(); raise        # never leave the transaction in the aborted state
        return PgCursor(cur, ret)
    def executemany(self, sql, seq):
        cur = self.conn.cursor()
        try: cur.executemany(self._sql(sql.strip().rstrip(";")), [tuple(p) for p in seq])
        except Exception: self.conn.rollback(); raise
        return PgCursor(cur)
    def commit(self): self.conn.commit()
    def rollback(self): self.conn.rollback()


_DRIVER_UNSAFE = {"supa", "pgbouncer", "schema", "connection_limit", "pool_timeout"}   # added by Supabase/Prisma connection strings; libpq rejects them

def get_pg_url():
    """Connection string from SUPABASE_DB_URL, DATABASE_URL or POSTGRES_URL (the one the Supabase-Vercel integration creates).
    Query parameters that only Supabase/Prisma understand (e.g. `supa=base-pooler.x`) are removed because the PostgreSQL driver errors on them,
    and TLS is required unless the host is local."""
    u = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or ""
    if not u.startswith(("postgres://", "postgresql://")): return None
    parts = urlsplit(u)
    q = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in _DRIVER_UNSAFE]
    local = (parts.hostname or "") in ("localhost", "127.0.0.1", "::1") or not parts.hostname
    if not local and not any(k.lower() == "sslmode" for k, _ in q): q.append(("sslmode", "require"))     # Supabase only accepts TLS connections
    return urlunsplit(parts._replace(query=urlencode(q)))

get_supabase_url = get_pg_url    # backwards-compatible name

_pool, _pool_lock = None, threading.Lock()

def _get_pool(url):
    global _pool
    with _pool_lock:
        if _pool is None:
            from psycopg2.pool import ThreadedConnectionPool
            _pool = ThreadedConnectionPool(1, int(os.getenv("MSANII_PG_POOL", "5")), url, connect_timeout=10)
    return _pool

def reset_pool():
    global _pool
    with _pool_lock:
        if _pool is not None: _pool.closeall(); _pool = None

def db():
    if "db" not in g:
        url = get_pg_url()
        if url:                                                    # PostgreSQL is configured: never fall back silently to a throw-away SQLite file
            pool = _get_pool(url); raw = pool.getconn()
            if raw.closed: pool.putconn(raw, close=True); raw = pool.getconn()
            g.db, g.pg_pool = PgConnection(raw), pool
        else:
            g.db = sqlite3.connect(current_app.config["DB"], timeout=15)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

def close_db(e=None):
    d = g.pop("db", None); pool = g.pop("pg_pool", None)
    if d is None: return
    if pool is not None:
        try: d.conn.rollback()
        except Exception: pass
        pool.putconn(d.conn, close=bool(d.conn.closed))
    else: d.close()

def is_pg(): return bool(get_pg_url())

def apply_pg_schema(path):
    """Run supabase_schema.sql (idempotent) against the configured PostgreSQL database."""
    import psycopg2
    raw = psycopg2.connect(get_pg_url(), connect_timeout=10)
    try:
        with raw.cursor() as c: c.execute(open(path, encoding="utf-8").read())
        raw.commit()
    finally: raw.close()

MIGRATIONS = [
    ("artists", "bio", "TEXT"),
    ("artists", "story", "TEXT"),
    ("artists", "image_url", "TEXT"),
    ("artists", "links", "TEXT NOT NULL DEFAULT '{}'"),
    ("artists", "enriched_at", "REAL"),
    ("decisions", "sig", "TEXT"),
    ("access_requests", "organization", "TEXT"),
    ("measurements", "media_id", "INTEGER"),
]

def init_db(path):
    if get_pg_url(): return                  # PostgreSQL schema is applied with `python manage.py migrate-pg` (or the Supabase SQL editor)
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

_audit_lock = threading.Lock()

def _h(prev, ts, uid, ev, det): return hashlib.sha256(f"{prev}|{ts!r}|{uid}|{ev}|{det}".encode()).hexdigest()

def audit(event, detail=None, user_id=None):
    """Append-only, hash-chained audit record. Never put secrets in `detail`."""
    d = db(); ip = request.remote_addr if has_request_context() else "job"
    try: d.commit()
    except Exception: pass
    with _audit_lock:                                   # serialise chain extension within a process
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
