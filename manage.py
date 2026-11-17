#!/usr/bin/env python3
"""Admin CLI: create-admin | set-password | migrate-pg | backup | discover | monitor | scheduler | seed-demo | clear-demo"""
import argparse, getpass, os, sqlite3, time
from msanii import create_app, engine
from msanii.db import db, apply_pg_schema, get_pg_url
from msanii.security import hash_pw, pw_ok

def main():
    ap = argparse.ArgumentParser(); s = ap.add_subparsers(dest="cmd", required=True)
    s.add_parser("create-admin").add_argument("email"); s.add_parser("set-password").add_argument("email"); s.add_parser("backup"); s.add_parser("migrate-pg"); s.add_parser("discover"); s.add_parser("monitor"); s.add_parser("scheduler"); s.add_parser("seed-demo"); s.add_parser("clear-demo")
    a = ap.parse_args()
    if a.cmd == "migrate-pg":
        if not get_pg_url(): raise SystemExit("set SUPABASE_DB_URL to a postgresql:// connection string first")
        apply_pg_schema(os.path.join(os.path.dirname(os.path.abspath(__file__)), "supabase_schema.sql")); print("PostgreSQL schema applied"); return
    app = create_app()
    with app.app_context():
        if a.cmd == "create-admin":
            pw = getpass.getpass("Password (10+ chars, letters and numbers): ")
            if not pw_ok(pw): raise SystemExit("password too weak")
            db().execute("INSERT INTO users(email,pw_hash,role,created_at) VALUES(?,?,?,?)", (a.email.lower(), hash_pw(pw), "admin", time.time())); db().commit(); print("admin created")
        elif a.cmd == "set-password":
            pw = getpass.getpass("New password (10+ chars, letters and numbers): ")
            if not pw_ok(pw): raise SystemExit("password too weak")
            c = db().execute("UPDATE users SET pw_hash=? WHERE email=?", (hash_pw(pw), a.email.lower())); db().execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE email=?)", (a.email.lower(),)); db().commit(); print("updated" if c.rowcount else "no such user")
        elif a.cmd == "backup":
            if get_pg_url(): raise SystemExit("backups of the PostgreSQL database are handled by Supabase (Database > Backups) or pg_dump")
            os.makedirs("backups", exist_ok=True); p = time.strftime("backups/msanii-%Y%m%d-%H%M%S.db")
            src, dst = sqlite3.connect(app.config["DB"]), sqlite3.connect(p); src.backup(dst); dst.close(); src.close(); os.chmod(p, 0o600); print("backup written:", p)
        elif a.cmd == "discover": print("run", engine.run_discovery("manual"))
        elif a.cmd == "seed-demo": from msanii import demo; print("demo artists added:", demo.seed())
        elif a.cmd == "clear-demo": from msanii import demo; print("demo artists removed:", demo.clear())
        elif a.cmd == "monitor": engine.monitor(); print("monitoring pass done")
    if a.cmd == "scheduler":     # run as ONE separate process; honours Settings > discovery.auto_minutes (0 = off)
        last = last_mon = 0.0
        while True:
            with app.app_context():
                try:
                    db().execute("INSERT INTO settings(key,value,updated_at) VALUES('_heartbeat',?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at", (str(time.time()), time.time())); db().commit()
                    m = engine.get_setting("discovery")["auto_minutes"]
                    if m and time.time() - last >= m * 60: last = time.time(); engine.run_discovery("auto")
                    engine.generate_reviews()
                    if time.time() - last_mon >= 86400: last_mon = time.time(); engine.monitor()
                except Exception: app.logger.exception("scheduled job failed")
            time.sleep(30)

if __name__ == "__main__": main()
