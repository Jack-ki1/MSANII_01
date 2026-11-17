import os, io, time, tempfile, unittest
from cryptography.fernet import Fernet
from msanii import create_app, engine, security
from msanii.db import db, verify_audit
from msanii.security import hash_pw, totp
from . import pgsupport

PW = "Passw0rd!xx"
class Fake:
    def search(self, q=None, country=None, limit=25, genre=None): return [{"name": f"Test Artist {country}", "country": country, "genres": ["afrobeats"], "begin_year": 2023, "ids": {"musicbrainz": f"x{country}"}}]
    def signals(self, a): return [("deezer_fans", 1000, "Deezer:1")]
    def profile(self, a): return {"bio": "A bio.", "image_url": "http://insecure.test/x.png", "links": {"Site": "https://x.test/a", "Bad": "javascript:alert(1)"}, "tracks": [{"title": "T1", "source": "Fake", "source_id": "1", "preview_url": "https://cdn.test/p.mp3"}]}

class T(unittest.TestCase):
    def setUp(self):
        security._hits.clear(); t = tempfile.mkdtemp(); pgsupport.prepare()
        self.app = create_app({"DB": f"{t}/t.db", "UPLOAD_DIR": f"{t}/up", "FERNET_KEY": Fernet.generate_key(), "ORIGINS": ["http://ok.test"]})
        self._b = engine.build; engine.build = lambda n: Fake()
        for e, r in (("admin@x.test", "admin"), ("rev@x.test", "reviewer"), ("view@x.test", "viewer")): self.mk(e, r)
    def tearDown(self): engine.build = self._b
    def mk(self, e, r):
        with self.app.app_context(): db().execute("INSERT INTO users(email,pw_hash,role,created_at) VALUES(?,?,?,?)", (e, hash_pw(PW), r, time.time())); db().commit()
    def login(self, email, **extra):
        c = self.app.test_client(); r = c.post("/api/auth/login", json={"email": email, "password": PW, **extra}); return c, r, (r.json or {}).get("csrf")
    def post(self, c, csrf, url, **kw): return c.post(url, headers={"X-CSRF-Token": csrf}, **kw)

    def test_auth_csrf_rbac(self):
        c = self.app.test_client(); self.assertEqual(c.get("/api/artists").status_code, 401)
        self.assertEqual(c.post("/api/auth/login", json={"email": "admin@x.test", "password": "wrong-pass-1"}).status_code, 401)
        c, r, csrf = self.login("rev@x.test"); self.assertEqual(r.status_code, 200); self.assertIn("HttpOnly", r.headers["Set-Cookie"])
        self.assertEqual(c.post("/api/discovery/run", json={}).status_code, 403)                          # missing CSRF
        self.assertEqual(c.post("/api/discovery/run", json={}, headers={"X-CSRF-Token": csrf, "Origin": "http://evil.test"}).status_code, 403)
        self.assertEqual(self.post(c, csrf, "/api/discovery/run", json={}).status_code, 201)
        self.assertEqual(c.get("/api/users").status_code, 403)                                            # reviewer is not admin
        v, _, vc = self.login("view@x.test"); self.assertEqual(self.post(v, vc, "/api/discovery/run", json={}).status_code, 403)

    def test_discovery_review_tier_and_audit(self):
        c, _, csrf = self.login("rev@x.test"); self.post(c, csrf, "/api/discovery/run", json={})
        arts = c.get("/api/artists").json["artists"]; self.assertEqual(len(arts), 4); aid = arts[0]["id"]
        self.assertEqual(c.get(f"/api/artists/{aid}").json["assessment"]["tier"], "MORE EVIDENCE")       # no review yet
        old = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 40 * 86400))
        self.assertEqual(self.post(c, csrf, f"/api/artists/{aid}/observations", json={"metric": "deezer_fans", "value": 500, "date": old}).status_code, 201)
        sc = {k: 4 for k in engine.CRIT}; self.assertEqual(self.post(c, csrf, f"/api/artists/{aid}/reviews", json={"scores": sc, "note": "strong hook"}).status_code, 201)
        self.assertEqual(self.post(c, csrf, f"/api/artists/{aid}/reviews", json={"scores": {"Bogus": 9}}).status_code, 400)
        self.assertEqual(c.get(f"/api/artists/{aid}").json["assessment"]["tier"], "PURSUE")
        self.assertEqual(self.post(c, csrf, "/api/decisions", json={"artist_id": aid, "action": "Contact", "rationale": "great hook"}).status_code, 201)
        self.assertFalse(c.get("/api/models").json["trained"])
        a, _, ac = self.login("admin@x.test"); ev = a.get("/api/audit").json; self.assertIsNone(ev["chain_broken_at"])
        with self.app.app_context(): self.assertIsNone(verify_audit()); db().execute("UPDATE audit SET detail='{}' WHERE id=2"); db().commit(); self.assertEqual(verify_audit(), 2)

    def test_credentials_never_leak(self):
        a, _, ac = self.login("admin@x.test"); self.assertEqual(a.put("/api/providers/Last.fm/credentials", json={"api_key": "SECRETKEY123"}, headers={"X-CSRF-Token": ac}).status_code, 200)
        self.assertNotIn("SECRETKEY123", a.get("/api/providers").get_data(as_text=True)); self.assertNotIn("SECRETKEY123", a.get("/api/audit").get_data(as_text=True))
        with self.app.app_context(): blob = db().execute("SELECT ciphertext FROM credentials").fetchone()[0]; self.assertNotIn(b"SECRETKEY123", blob)
        r, _, rc = self.login("rev@x.test"); self.assertEqual(r.put("/api/providers/Last.fm/credentials", json={"api_key": "x" * 8}, headers={"X-CSRF-Token": rc}).status_code, 403)

    def test_headers_cors_injection_upload_mfa(self):
        c = self.app.test_client(); r = c.get("/api/health", headers={"Origin": "http://evil.test"}); self.assertNotIn("Access-Control-Allow-Origin", r.headers)
        r = c.get("/api/health", headers={"Origin": "http://ok.test"}); self.assertEqual(r.headers["Access-Control-Allow-Origin"], "http://ok.test"); self.assertEqual(r.headers["X-Frame-Options"], "DENY")
        c, _, csrf = self.login("rev@x.test"); self.post(c, csrf, "/api/discovery/run", json={}); aid = c.get("/api/artists").json["artists"][0]["id"]
        self.assertEqual(c.get("/api/artists", query_string={"q": "' OR 1=1 --"}).json["artists"], [])
        up = lambda data: self.post(c, csrf, f"/api/artists/{aid}/media", data={"file": (io.BytesIO(data), "x.wav"), "rights_cleared": "true", "title": "x"}, content_type="multipart/form-data")
        self.assertEqual(up(b"not audio at all").status_code, 400); self.assertEqual(up(b"RIFF\0\0\0\0WAVE" + b"\0" * 64).status_code, 201)
        sec = self.post(c, csrf, "/api/auth/mfa/setup").json["secret"]; self.assertEqual(self.post(c, csrf, "/api/auth/mfa/enable", json={"code": totp(sec)}).status_code, 200)
        self.assertEqual(self.login("rev@x.test")[1].status_code, 401); self.assertEqual(self.login("rev@x.test", code=totp(sec))[1].status_code, 200)

if __name__ == "__main__": unittest.main()
