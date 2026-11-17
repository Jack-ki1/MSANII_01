import re, hmac, json, time, base64, struct, hashlib, secrets, threading
from collections import defaultdict, deque
from functools import wraps
from flask import request, g, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
from .db import db, audit

SID, SESSION_TTL = "msanii_sid", 8 * 3600
ROLES = {"viewer": 1, "reviewer": 2, "admin": 3}
EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,}$")
EXEMPT = {"api.login", "api.accept_invite", "api.request_access"}      # no session yet; protected by Origin check + JSON-only + rate limits
DUMMY = generate_password_hash("not-a-real-password")

class ApiError(Exception):
    def __init__(self, msg, status=400): self.msg, self.status = msg, status

def ip(): return request.remote_addr or "?"
def tok(): return secrets.token_urlsafe(32)
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def hash_pw(p): return generate_password_hash(p, method="scrypt")
def check_pw(h, p): return bool(h) and check_password_hash(h, p)
def pw_ok(p): return isinstance(p, str) and 10 <= len(p) <= 128 and bool(re.search(r"[A-Za-z]", p)) and bool(re.search(r"\d", p))

# ---- secrets at rest (Fernet) ----
def enc(obj): return Fernet(current_app.config["FERNET_KEY"]).encrypt(json.dumps(obj).encode())
def dec(blob): return json.loads(Fernet(current_app.config["FERNET_KEY"]).decrypt(blob))

# ---- TOTP (RFC 6238) ----
def new_totp_secret(): return base64.b32encode(secrets.token_bytes(20)).decode()
def totp(secret, t=None):
    c = int((t or time.time()) // 30); h = hmac.new(base64.b32decode(secret), struct.pack(">Q", c), hashlib.sha1).digest(); o = h[-1] & 15
    return str((struct.unpack(">I", h[o:o + 4])[0] & 0x7FFFFFFF) % 10 ** 6).zfill(6)
def totp_ok(secret, code): return any(hmac.compare_digest(totp(secret, time.time() + w * 30), str(code)) for w in (-1, 0, 1))

# ---- rate limiting (per process; use Redis/gateway limits when running several workers) ----
_hits, _lock = defaultdict(deque), threading.Lock()
def limited(key, n, per):
    now = time.time()
    with _lock:
        q = _hits[key]
        while q and q[0] < now - per: q.popleft()
        if len(q) >= n: return True
        q.append(now); return False

# ---- validation ----
def body():
    if not request.is_json: raise ApiError("JSON body required", 415)
    d = request.get_json(silent=True)
    if not isinstance(d, dict): raise ApiError("invalid JSON object")
    return d

def field(d, k, typ=str, mn=0, mx=500, choices=None, req=True):
    v = d.get(k)
    if v is None or v == "":
        if req: raise ApiError(f"{k} is required")
        return None
    if typ is str:
        if not isinstance(v, str): raise ApiError(f"{k} must be text")
        v = v.strip()
        if not mn <= len(v) <= mx: raise ApiError(f"{k} length must be {mn}-{mx}")
    elif typ in (int, float):
        if isinstance(v, bool) or not isinstance(v, (int, float)): raise ApiError(f"{k} must be a number")
        if not mn <= v <= mx: raise ApiError(f"{k} out of range")
    elif typ is bool and not isinstance(v, bool): raise ApiError(f"{k} must be true or false")
    if choices is not None and v not in choices: raise ApiError(f"{k} invalid")
    return v

# ---- sessions: opaque random id in an HttpOnly cookie; only its hash is stored server-side ----
def start_session(uid):
    sid, csrf, now = tok(), tok(), time.time(); d = db()
    d.execute("INSERT INTO sessions VALUES(?,?,?,?,?,?)", (sha(sid), uid, csrf, now, now + SESSION_TTL, request.headers.get("User-Agent", "")[:200])); d.commit()
    return sid, csrf

def load_session():
    g.user = None; sid = request.cookies.get(SID)
    if not sid: return
    r = db().execute("SELECT s.csrf,s.sid_hash,s.expires_at,u.id,u.email,u.role,u.active FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.sid_hash=?", (sha(sid),)).fetchone()
    if r and r["expires_at"] > time.time() and r["active"]:
        g.user = {"id": r["id"], "email": r["email"], "role": r["role"], "csrf": r["csrf"], "sid_hash": r["sid_hash"]}

def before_request():
    if request.method == "OPTIONS": return "", 204
    if not request.path.startswith("/api/"): return
    if limited(("g", ip()), current_app.config["RATE_GLOBAL"], 60): return jsonify(error="rate limit exceeded"), 429
    load_session()
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        o = request.headers.get("Origin")
        if o and o not in current_app.config["ORIGINS"] and o != request.host_url.rstrip("/"): return jsonify(error="origin not allowed"), 403
        if request.endpoint not in EXEMPT:
            if not g.user: return jsonify(error="authentication required"), 401
            if not hmac.compare_digest(request.headers.get("X-CSRF-Token", ""), g.user["csrf"]):
                audit("csrf_rejected", {"path": request.path}, g.user["id"]); return jsonify(error="csrf check failed"), 403

def require(role="viewer"):
    def deco(f):
        @wraps(f)
        def w(*a, **k):
            if not g.get("user"): return jsonify(error="authentication required"), 401
            if ROLES[g.user["role"]] < ROLES[role]:
                audit("forbidden", {"path": request.path, "need": role}, g.user["id"]); return jsonify(error="forbidden"), 403
            return f(*a, **k)
        return w
    return deco

def safe_url(u, mx=500):
    """Only https URLs without whitespace or markup characters are ever stored or rendered as links."""
    return u if isinstance(u, str) and u.startswith("https://") and len(u) <= mx and not re.search(r"[\s<>\"']", u) else None
