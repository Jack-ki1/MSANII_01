import time, unittest
import tests.test_smoke as S
from msanii import demo, engine
from msanii.db import db

class T2(S.T):
    def test_demo_tasks_settings(self):
        with self.app.app_context(): self.assertEqual(demo.seed(), 6); self.assertEqual(demo.seed(), 0)
        c, _, csrf = self.login("rev@x.test"); arts = c.get("/api/artists").json["artists"]
        self.assertEqual(len(arts), 6)                                  # Established artist hidden by default
        self.assertTrue(all(a["demo"] for a in arts))
        baraka = next(a for a in arts if a["name"] == "Baraka Mshana"); d = c.get(f"/api/artists/{baraka['id']}").json
        self.assertTrue(any("Sudden" in f["title"] for f in d["assessment"]["flags"])); self.assertIn("deezer_fans", d["latest"])
        self.assertEqual(d["assessment"]["tier"], "MORE EVIDENCE")       # demo data has no human review
        self.assertEqual(self.post(c, csrf, "/api/decisions", json={"artist_id": baraka["id"], "action": "Monitor", "rationale": "watch spike"}).status_code, 201)
        t = c.get("/api/tasks").json["tasks"]; self.assertEqual({x["kind"] for x in t}, {"weekly", "bimonthly"})
        self.assertEqual(self.post(c, csrf, f"/api/tasks/{t[0]['id']}/done").status_code, 200); self.assertEqual(len(c.get("/api/tasks").json["tasks"]), 1)
        a, _, ac = self.login("admin@x.test"); H = {"X-CSRF-Token": ac}
        self.assertEqual(a.put("/api/settings/weights", json={"v": 50, "w": 50, "s": 10, "c": 10}, headers=H).status_code, 400)
        self.assertEqual(a.put("/api/settings/automation", json={"bimonthly_days": 14}, headers=H).status_code, 200)
        self.assertEqual(a.put("/api/settings/discovery", json={"auto_minutes": 45}, headers=H).status_code, 400)
        self.assertEqual(self.post(a, ac, "/api/users/invite", json={"email": "new@x.test", "role": "viewer"}).status_code, 201)
        with self.app.app_context(): self.assertEqual(demo.clear(), 6)

    def test_profile_media_meta_password(self):
        import io, wave, struct, math
        c, _, csrf = self.login("rev@x.test"); self.post(c, csrf, "/api/discovery/run", json={"country": "KE"}); aid = c.get("/api/artists").json["artists"][0]["id"]
        self.assertEqual(self.post(c, csrf, f"/api/artists/{aid}/enrich").status_code, 200)
        d = c.get(f"/api/artists/{aid}").json["artist"]; self.assertEqual(d["bio"], "A bio."); self.assertIsNone(d["image_url"]); self.assertEqual(list(d["links"]), ["Site"])   # unsafe URLs dropped
        self.assertEqual(len(c.get(f"/api/artists/{aid}").json["tracks"]), 1)
        self.assertEqual(c.patch(f"/api/artists/{aid}", json={"story": "Raised on taarab."}, headers={"X-CSRF-Token": csrf}).status_code, 200)
        self.assertEqual(c.patch(f"/api/artists/{aid}", json={"image_url": "javascript:x"}, headers={"X-CSRF-Token": csrf}).status_code, 400)
        self.assertEqual(self.post(c, csrf, f"/api/artists/{aid}/media/link", json={"url": "http://localhost/secret"}).status_code, 400)      # no arbitrary URLs
        self.assertEqual(self.post(c, csrf, f"/api/artists/{aid}/media/link", json={"url": "https://evil.test/x"}).status_code, 400)
        buf = io.BytesIO(); w = wave.open(buf, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100); w.writeframes(b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * i / 44100))) for i in range(44100 * 3))); w.close()
        r = self.post(c, csrf, f"/api/artists/{aid}/media", data={"file": (io.BytesIO(buf.getvalue()), "s.wav"), "rights_cleared": "true", "title": "Sine"}, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 201); m = r.json["media"]; self.assertEqual(m["status"], "done"); names = {x["name"] for x in m["result"]["measurements"]}; self.assertIn("rms_level", names)
        self.assertTrue(all(x["pass"] for x in m["result"]["compliance"] if x["check"].startswith("Sample rate")))
        self.assertEqual(c.get(f"/api/media/{m['id']}/file").status_code, 200); self.assertEqual(self.post(c, csrf, f"/api/artists/{aid}/media", data={"file": (io.BytesIO(buf.getvalue()), "s.wav")}, content_type="multipart/form-data").status_code, 400)
        self.assertGreater(len(c.get(f"/api/artists/{aid}").json["measurements"]), 3)
        self.assertEqual(self.post(c, csrf, f"/api/artists/{aid}/observations/bulk", json={"rows": [{"metric": "ugc_videos", "value": 5, "date": "2026-01-01"}, {"metric": "bad", "value": 1}]}).status_code, 400)
        self.assertEqual(c.get("/api/meta").json["default_region"], "East Africa"); self.assertGreater(len(c.get("/api/meta").json["genres"]), 50)
        self.assertEqual(self.post(c, csrf, "/api/auth/change-password", json={"current": "wrong-one-1", "new": "Another-pass-22"}).status_code, 400)
        self.assertEqual(self.post(c, csrf, "/api/auth/change-password", json={"current": "Passw0rd!xx", "new": "Another-pass-22"}).status_code, 200)
        self.assertEqual(self.login("rev@x.test")[1].status_code, 401)
        a, _, ac = self.login("admin@x.test"); self.assertTrue(a.get("/api/system").json["counts"]["media"] >= 1); self.assertGreater(len(a.get("/api/providers").json["providers"]), 70)
        self.assertEqual(a.put("/api/settings/workspace", json={"region": "West Africa", "default_country": "KE"}, headers={"X-CSRF-Token": ac}).status_code, 400)

if __name__ == "__main__": unittest.main()
