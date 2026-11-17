"""Hits every GET endpoint with seeded demo data and the main write paths. Catches SQL that works on SQLite but not on PostgreSQL."""
import io, json, time, struct, math, tempfile, unittest
from cryptography.fernet import Fernet
from msanii import create_app, demo, engine
from msanii.db import db
from msanii.security import hash_pw
from . import pgsupport

PW = "Passw0rd!xx"

def wav(seconds=12, sr=22050):
    n = seconds * sr; pcm = b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 220 * i / sr))) for i in range(n))
    h = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, sr, sr * 2, 2, 16) + b"data" + struct.pack("<I", len(pcm))
    return h + pcm

class Sweep(unittest.TestCase):
    def setUp(self):
        pgsupport.prepare(); t = tempfile.mkdtemp()
        self.app = create_app({"DB": f"{t}/t.db", "UPLOAD_DIR": f"{t}/up", "FERNET_KEY": Fernet.generate_key(), "ORIGINS": ["http://x"], "RATE_GLOBAL": 100000})
        with self.app.app_context():
            db().execute("INSERT INTO users(email,pw_hash,role,created_at) VALUES(?,?,?,?)", ("a@x.t", hash_pw(PW), "admin", time.time())); db().commit(); demo.seed()
            self.aid = db().execute("SELECT id FROM artists ORDER BY id LIMIT 1").fetchone()["id"]
        self.c = self.app.test_client(); r = self.c.post("/api/auth/login", json={"email": "a@x.t", "password": PW}); self.h = {"X-CSRF-Token": r.json["csrf"]}

    def test_every_get_endpoint_returns_no_server_error(self):
        seen = 0
        for rule in self.app.url_map.iter_rules():
            if "GET" not in rule.methods or not rule.rule.startswith("/api/") or rule.endpoint in ("api.logout",): continue
            args = {a: (self.aid if "int" in type(rule._converters[a]).__name__.lower() else "x") for a in rule.arguments}
            if rule.arguments and any(a not in ("aid", "mid", "uid", "rid", "tid") for a in rule.arguments): continue
            url = rule.rule
            for a, v in args.items(): url = url.replace(f"<int:{a}>", str(v)).replace(f"<{a}>", str(v))
            if "<" in url: continue
            r = self.c.get(url); seen += 1
            self.assertLess(r.status_code, 500, f"{url} -> {r.status_code} {r.data[:200]!r}")
        self.assertGreaterEqual(seen, 15)

    def test_write_paths(self):
        c, h, aid = self.c, self.h, self.aid
        self.assertEqual(c.post(f"/api/artists/{aid}/reviews", headers=h, json={"scores": {k: 4 for k in engine.CRIT}, "note": "good"}).status_code, 201)
        self.assertEqual(c.post("/api/decisions", headers=h, json={"artist_id": aid, "action": "Monitor", "rationale": "watching closely"}).status_code, 201)
        self.assertEqual(c.post(f"/api/artists/{aid}/observations", headers=h, json={"metric": "ugc_videos", "value": 123, "date": "2026-11-01"}).status_code, 201)
        th = c.get("/api/settings").json["thresholds"]; self.assertEqual(c.put("/api/settings/thresholds", headers=h, json=th).status_code, 200)      # settings upsert (no id column)
        cr = c.put("/api/providers/Spotify/credentials", headers=h, json={"client_id": "abc", "client_secret": "def"}); self.assertLess(cr.status_code, 500, cr.data[:200])    # encrypted BYTEA upsert
        with self.app.app_context(): engine.generate_reviews()                                      # the SUM(CASE ...) query
        self.assertEqual(c.get("/api/tasks").status_code, 200)
        up = c.post(f"/api/artists/{aid}/media", headers=h, data={"title": "demo", "rights_cleared": "true", "file": (io.BytesIO(wav()), "t.wav")}, content_type="multipart/form-data")
        self.assertLess(up.status_code, 500, up.data[:300])
        self.assertEqual(up.status_code, 201, up.data[:300]); mid = up.json["media"]["id"]
        self.assertEqual(c.delete(f"/api/media/{mid}", headers=h).status_code, 200)                  # media_id column replaces json_extract
        with self.app.app_context(): self.assertEqual(db().execute("SELECT COUNT(*) FROM measurements WHERE media_id=?", (mid,)).fetchone()[0], 0)
        self.assertIsNone(c.get("/api/audit").json["chain_broken_at"])
        self.assertEqual(c.get("/api/system").json["database"], "postgresql" if pgsupport.PG_URL else "sqlite")
        exp = c.get("/api/export/artists"); self.assertLess(exp.status_code, 500)
