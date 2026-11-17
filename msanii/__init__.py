import os, time
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException
from cryptography.fernet import Fernet
from .db import init_db, close_db, db, get_pg_url
from .security import before_request, ApiError, hash_pw, pw_ok
from .api import bp

CSP = ("default-src 'self'; img-src 'self' data: https:; media-src 'self' https:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; frame-src https://www.youtube-nocookie.com https://open.spotify.com; "
       "frame-ancestors 'none'; base-uri 'none'; form-action 'self'")

def create_app(test_config=None):
    app = Flask(__name__, static_folder=None)
    on_vercel = bool(os.getenv("VERCEL"))        # serverless: the deployment bundle is read-only, only /tmp is writable (and it is ephemeral)
    env = os.getenv("MSANII_ENV") or ("production" if os.getenv("VERCEL_ENV") in ("production", "preview") else "development")
    prod = env == "production"
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data = "/tmp/msanii" if on_vercel else os.path.join(root, "data")
    app.config.update(
        DB=os.getenv("MSANII_DB", os.path.join(data, "msanii.db")), UPLOAD_DIR=os.getenv("MSANII_UPLOAD_DIR", os.path.join(data, "uploads")),
        STATIC_DIR=os.path.join(root, "static"), SECURE_COOKIES=prod, MAX_CONTENT_LENGTH=25 * 1024 * 1024, RATE_GLOBAL=240,
        ORIGINS=[o.strip() for o in os.getenv("MSANII_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()],
        CONTACT=os.getenv("MSANII_CONTACT", "set-MSANII_CONTACT"), FERNET_KEY=os.getenv("MSANII_FERNET_KEY"))
    if test_config: app.config.update(test_config)
    if on_vercel and prod and not get_pg_url():
        raise RuntimeError("SUPABASE_DB_URL (a postgresql:// connection string) is required on Vercel: the serverless filesystem is ephemeral, so SQLite would lose all data")
    os.makedirs(os.path.dirname(app.config["DB"]), exist_ok=True); os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)
    if not app.config["FERNET_KEY"]:
        if prod: raise RuntimeError("MSANII_FERNET_KEY is required in production")
        kf = os.path.join(os.path.dirname(app.config["DB"]), ".fernet_key")
        if not os.path.exists(kf):
            fd = os.open(kf, os.O_WRONLY | os.O_CREAT, 0o600); os.write(fd, Fernet.generate_key()); os.close(fd)
        app.config["FERNET_KEY"] = open(kf, "rb").read().strip()
    init_db(app.config["DB"])
    if os.getenv("MSANII_PROXIES") == "1" or on_vercel:    # real client IP for rate limiting / audit (Vercel and most PaaS sit behind exactly one proxy)
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    app.teardown_appcontext(close_db); app.before_request(before_request); app.register_blueprint(bp, url_prefix="/api")

    @app.after_request
    def headers(r):
        r.headers.update({"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer", "Content-Security-Policy": CSP,
                          "Permissions-Policy": "camera=(), microphone=(), geolocation=()", "Cross-Origin-Opener-Policy": "same-origin"})
        if prod: r.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        if request.path.startswith("/api/"): r.headers["Cache-Control"] = "no-store"
        o = request.headers.get("Origin")
        if o and o in app.config["ORIGINS"]:
            r.headers.update({"Access-Control-Allow-Origin": o, "Access-Control-Allow-Credentials": "true", "Vary": "Origin",
                              "Access-Control-Allow-Headers": "Content-Type, X-CSRF-Token", "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE"})
        return r

    @app.errorhandler(ApiError)
    def _api(e): return jsonify(error=e.msg), e.status
    @app.errorhandler(HTTPException)
    def _http(e): return jsonify(error=e.name), e.code
    @app.errorhandler(Exception)
    def _any(e): app.logger.exception("unhandled error"); return jsonify(error="internal error"), 500

    @app.get("/")
    def index():
        if os.path.exists(os.path.join(app.config["STATIC_DIR"], "index.html")): return send_from_directory(app.config["STATIC_DIR"], "index.html")
        return jsonify(service="msanii-api", note="build the frontend into ./static or run it separately")
    @app.get("/static/<path:f>")
    def static_files(f): return send_from_directory(app.config["STATIC_DIR"], f)

    with app.app_context():   # optional bootstrap: MSANII_ADMIN_EMAIL + MSANII_ADMIN_PASSWORD when no users exist
        e, p = os.getenv("MSANII_ADMIN_EMAIL"), os.getenv("MSANII_ADMIN_PASSWORD")
        try: empty = not db().execute("SELECT 1 FROM users").fetchone()
        except Exception as ex:
            if get_pg_url(): raise RuntimeError("PostgreSQL schema missing: run `python manage.py migrate-pg` (or paste supabase_schema.sql into the Supabase SQL editor)") from ex
            raise
        if e and p and empty:
            if not pw_ok(p): raise RuntimeError("MSANII_ADMIN_PASSWORD must be 10+ characters with letters and numbers")
            db().execute("INSERT INTO users(email,pw_hash,role,created_at) VALUES(?,?,?,?)", (e.lower(), hash_pw(p), "admin", time.time())); db().commit()
    return app
