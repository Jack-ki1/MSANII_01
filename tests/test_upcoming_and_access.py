import unittest, json, time, tempfile
from cryptography.fernet import Fernet
from msanii import create_app
from msanii.db import db
from msanii import ml

class TestUpcomingAndAccess(unittest.TestCase):
    def setUp(self):
        t = tempfile.mkdtemp()
        self.app = create_app({
            "TESTING": True, "DB": f"{t}/t.db", "UPLOAD_DIR": f"{t}/up",
            "FERNET_KEY": Fernet.generate_key(), "ORIGINS": ["http://localhost:5173"],
            "SECURE_COOKIES": False, "RATE_GLOBAL": 10000, "SEED_OWNER": False
        })
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_upcoming_artist_tenure_and_breakout(self):
        # 1. Upcoming artist <= 5 years tenure
        tenure = ml.calculate_tenure(2023)
        self.assertLessEqual(tenure, 5.0)
        self.assertTrue(ml.is_upcoming({"begin_year": 2023}))

        # 2. Breakout probability calculation
        series = {"monthly_listeners": [[time.time() - 30 * 86400, 40000], [time.time(), 62000]]}
        pred = ml.predict_breakout_probability({"begin_year": 2023}, series, {"momentum": 0.55, "artistic": 80.0})
        self.assertIn("breakout_probability", pred)
        self.assertGreater(pred["breakout_probability"], 0.5)
        self.assertIn("category", pred)
        self.assertTrue(pred["is_upcoming"])

    def test_access_request_flow(self):
        client = self.app.test_client()
        # Request access
        req_payload = {
            "full_name": "Amina Mwangi",
            "email": "amina@eastafricamusic.com",
            "organization": "Rift Valley Records",
            "role_title": "Senior A&R Scout",
            "region": "East Africa",
            "notes": "Looking to evaluate upcoming drill and Afro-fusion artists."
        }
        res = client.post("/api/auth/request-access", json=req_payload)
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.json["ok"])

        # Check in database
        d = db()
        record = d.execute("SELECT * FROM access_requests WHERE email=?", (req_payload["email"],)).fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record["status"], "pending")

        # Approve via token link
        token = record["token"]
        approve_res = client.get(f"/api/auth/approve-access?token={token}&action=approve")
        self.assertEqual(approve_res.status_code, 200)

        # Verify user account created
        user = d.execute("SELECT * FROM users WHERE email=?", (req_payload["email"],)).fetchone()
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "reviewer")

        # Verify request updated
        updated_rec = d.execute("SELECT * FROM access_requests WHERE token=?", (token,)).fetchone()
        self.assertEqual(updated_rec["status"], "approved")

    def test_acoustic_forensic_models(self):
        crepe = ml.get_crepe_pitch_accuracy()
        self.assertEqual(crepe["in_key_pct"], 88.5)
        self.assertEqual(crepe["intonation_score"], 0.84)
        self.assertEqual(len(crepe["histogram"]), 11)

        tessitura = ml.get_vocal_tessitura()
        self.assertEqual(tessitura["lowest_note"], "C3")
        self.assertEqual(tessitura["highest_note"], "G5")
        self.assertEqual(tessitura["usable_span_semitones"], 31)
        self.assertEqual(tessitura["detected_key"], "E Minor")

        timbre = ml.get_vocal_timbre_audit()
        self.assertEqual(timbre["vibrato_rate_hz"], 5.4)
        self.assertEqual(timbre["hnr_db"], 22.8)

        stems = ml.get_stem_occupancy_and_vernacular()
        self.assertEqual(len(stems["stems"]), 4)
        self.assertEqual(stems["stems"][0]["occupancy"], 82)

        advance = ml.calculate_ar_advance_valuation(75109, 0.248)
        self.assertEqual(advance["recommended_advance"], 3750)

    def test_admin_access_requests_and_model_retrain(self):
        client = self.app.test_client()
        # Seed an admin user
        from msanii.security import hash_pw
        with self.app.app_context():
            d = db()
            d.execute("INSERT INTO users(email,pw_hash,role,created_at) VALUES(?,?,?,?)",
                      ("admin@test.com", hash_pw("AdminPass123!"), "admin", time.time()))
            # Seed an artist for lab-default
            d.execute("INSERT INTO artists(name,country,city,begin_year,stage,first_seen) VALUES(?,?,?,?,?,?)",
                      ("Juliani", "KE", "Nairobi", 2023, "Emerging Breakout", time.time()))
            d.commit()

        # Login as admin
        login_res = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "AdminPass123!"})
        self.assertEqual(login_res.status_code, 200)
        csrf = login_res.json["csrf"]

        # 1. Test /api/artists/lab-default
        lab_res = client.get("/api/artists/lab-default")
        self.assertEqual(lab_res.status_code, 200)
        self.assertEqual(lab_res.json["artist"]["name"], "Juliani")
        self.assertIn("acoustic_analytics", lab_res.json)
        self.assertEqual(lab_res.json["acoustic_analytics"]["kpis"]["recommended_advance"]["value"], 3750)

        # 2. Test /api/models/retrain
        retrain_res = client.post("/api/models/retrain", headers={"X-CSRF-Token": csrf})
        self.assertEqual(retrain_res.status_code, 200)
        self.assertTrue(retrain_res.json["ok"])
        self.assertIn("Breakout Probability", retrain_res.json["message"])

        # 3. Test /api/providers/<name>/tuning
        tune_res = client.put(
            "/api/providers/Spotify/tuning",
            headers={"X-CSRF-Token": csrf},
            json={"priority": 9, "rate_limit_rpm": 120, "enabled": True}
        )
        self.assertEqual(tune_res.status_code, 200)
        self.assertTrue(tune_res.json["ok"])
        self.assertEqual(tune_res.json["tuning"]["priority"], 9)

        # 4. Test admin approving access requests via REST
        # Create request first
        req_res = client.post("/api/auth/request-access", json={
            "full_name": "Kofi Mensah",
            "email": "kofi@accra.fm",
            "organization": "West Coast A&R",
            "role_title": "Scout",
            "region": "West Africa",
            "notes": "Fast rising drill artists"
        })
        self.assertEqual(req_res.status_code, 201)

        reqs_list = client.get("/api/auth/access-requests")
        self.assertEqual(reqs_list.status_code, 200)
        pending = [r for r in reqs_list.json["requests"] if r["email"] == "kofi@accra.fm"]
        self.assertEqual(len(pending), 1)
        req_id = pending[0]["id"]

        # Approve it via admin endpoint
        appr_res = client.post(f"/api/auth/access-requests/{req_id}/approve", headers={"X-CSRF-Token": csrf})
        self.assertEqual(appr_res.status_code, 200)
        self.assertTrue(appr_res.json["ok"])
        self.assertIn("temp_password", appr_res.json)
