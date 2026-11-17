"""Regression tests for the review findings: missing data must stay missing, and nothing may be fabricated for a real artist."""
import json, time, tempfile, unittest, random
from cryptography.fernet import Fernet
from msanii import create_app, engine, ml, demo
from msanii.db import db, verify_audit, Row, is_pg
from msanii.security import hash_pw
from . import pgsupport

NOW = time.time()

class MlHonesty(unittest.TestCase):
    def test_no_data_means_no_probability(self):
        p = ml.predict_breakout_probability({"begin_year": 2024}, {}, None)
        self.assertTrue(p["insufficient_data"]); self.assertIsNone(p["breakout_probability"]); self.assertEqual(p["category"], "Insufficient data")
        self.assertFalse(p["calibrated"])

    def test_score_responds_to_growth_in_the_right_direction(self):
        def prob(a, b): return ml.predict_breakout_probability({"begin_year": 2024}, {"monthly_listeners": [[NOW - 30 * 86400, a], [NOW, b]]}, None)["breakout_probability"]
        self.assertGreater(prob(1000, 1800), prob(1000, 1000)); self.assertGreater(prob(1000, 1000), prob(1000, 400))
        self.assertLess(prob(1000, 400), 0.35)                                     # a collapsing audience is not "likely to break out"

    def test_clean_record_adds_no_credit_and_flags_subtract(self):
        base = {"momentum": 0.1}; flagged = {"momentum": 0.1, "flags": [{}, {}]}
        s = {"monthly_listeners": [[NOW - 30 * 86400, 1000], [NOW, 1100]]}
        self.assertGreater(ml.predict_breakout_probability({"begin_year": 2024}, s, base)["breakout_probability"], ml.predict_breakout_probability({"begin_year": 2024}, s, flagged)["breakout_probability"])

    def test_unknown_career_start_is_unknown(self):
        self.assertIsNone(ml.calculate_tenure(None, first_seen=NOW)); self.assertIsNone(ml.is_upcoming({"begin_year": None, "first_seen": NOW}))
        self.assertEqual(ml.calculate_tenure(2023), round(time.localtime().tm_year - 2023 + 0.4, 1))

    def test_forecast_needs_history_and_band_tracks_noise(self):
        self.assertEqual(ml.forecast_trajectory([]), []); self.assertEqual(ml.forecast_trajectory([[NOW, 100], [NOW + 86400, 110]]), [])
        def series(noise, seed=1):
            r = random.Random(seed); return [[NOW - (12 - i) * 7 * 86400, 10000 * (1.01 ** (i * 7)) * (1 + r.gauss(0, noise))] for i in range(12)]
        width = lambda f: f[2]["upper"] / f[2]["lower"]
        self.assertGreater(width(ml.forecast_trajectory(series(0.4))), 2 * width(ml.forecast_trajectory(series(0.0))))   # noisy history => wider interval
        f = ml.forecast_trajectory(series(0.05)); self.assertTrue(f[0]["upper"] < f[1]["upper"] < f[2]["upper"])                # uncertainty grows with horizon
        self.assertTrue(all(x["lower"] < x["expected"] < x["upper"] for x in f))

    def test_forecast_line_passes_through_the_data_after_slope_clamp(self):
        pts = [[NOW - (11 - i) * 86400 * 7, 1000 * (1.05 ** (i * 7))] for i in range(12)]          # ~5%/day: far above the +2%/day clamp
        f = ml.forecast_trajectory(pts); self.assertTrue(f[0]["slope_clamped"])
        self.assertLess(f[0]["expected"], pts[-1][1] * 2)                                          # a mis-anchored intercept would explode this

    def test_organic_ratio_is_same_platform_and_missing_is_missing(self):
        none = ml.evaluate_organic_integrity({}, []); self.assertIsNone(none["ratio"]); self.assertEqual(none["status_label"], "Insufficient data"); self.assertEqual(none["peers"], [])
        mixed = ml.evaluate_organic_integrity({}, [{"metric": "deezer_fans", "value": 10}, {"metric": "streams", "value": 5000}])
        self.assertIsNone(mixed["ratio"])                                                          # no cross-platform ratio
        ok = ml.evaluate_organic_integrity({}, [{"metric": "streams", "value": 6000}, {"metric": "lastfm_listeners", "value": 2000}])
        self.assertEqual(ok["ratio"], 3.0); self.assertFalse(ok["safe_zone_certified"])

class EngineHonesty(unittest.TestCase):
    def setUp(self):
        pgsupport.prepare(); t = tempfile.mkdtemp()
        self.app = create_app({"DB": f"{t}/t.db", "UPLOAD_DIR": f"{t}/up", "FERNET_KEY": Fernet.generate_key(), "ORIGINS": ["http://x"], "RATE_GLOBAL": 10000})
        self.ctx = self.app.app_context(); self.ctx.push()
        db().execute("INSERT INTO users(email,pw_hash,role,created_at) VALUES(?,?,?,?)", ("v@x.t", hash_pw("Passw0rd!xx"), "reviewer", NOW)); db().commit()
    def tearDown(self): self.ctx.pop()

    def artist(self, name="Snapshot Only", year=2024):
        return db().execute("INSERT INTO artists(name,country,begin_year,first_seen) VALUES(?,'KE',?,?)", (name, year, NOW)).lastrowid

    def test_single_snapshot_metrics_are_not_evidence_and_cannot_pursue(self):
        aid = self.artist()
        for m in ("deezer_fans", "lastfm_listeners", "audius_followers"): db().execute("INSERT INTO observations(artist_id,ts,metric,value,source) VALUES(?,?,?,?,?)", (aid, NOW, m, 500, "t"))
        db().execute("INSERT INTO reviews(artist_id,user_id,scores,ts) VALUES(?,1,?,?)", (aid, json.dumps({k: 5 for k in engine.CRIT}), NOW)); db().commit()
        s = engine.assess(aid)
        self.assertLess(s["evidence"], 0.4); self.assertEqual(s["tier"], "MORE EVIDENCE"); self.assertIsNone(s["growth"])

    def test_heuristic_score_alone_never_promotes_to_pursue(self):
        aid = self.artist()
        for i, v in enumerate((1000, 1010, 1020)): db().execute("INSERT INTO observations(artist_id,ts,metric,value,source) VALUES(?,?,?,?,?)", (aid, NOW - (60 - i * 30) * 86400, "deezer_fans", v, "t"))
        db().execute("INSERT INTO reviews(artist_id,user_id,scores,ts) VALUES(?,1,?,?)", (aid, json.dumps({k: 5 for k in engine.CRIT}), NOW)); db().commit()
        s = engine.assess(aid); self.assertNotEqual(s["tier"], "PURSUE") if s["growth"]["pct"] <= engine.get_setting("thresholds")["pursue_growth"] else None

    def test_model_status_does_not_claim_accuracy(self):
        m = engine.model_status(); self.assertFalse(m["trained"]); self.assertIsNone(m["accuracy"]); self.assertIsNone(m["f1_score"]); self.assertEqual(m["labelled_windows"], 0)

    def test_real_artist_dossier_has_no_fabricated_values(self):
        aid = self.artist("Totally Unknown")
        c = self.app.test_client(); c.post("/api/auth/login", json={"email": "v@x.t", "password": "Passw0rd!xx"})
        d = c.get(f"/api/artists/{aid}").json; an = d["acoustic_analytics"]
        self.assertFalse(an["illustrative"]); self.assertEqual(an["observed"], [])
        for k in ("kpis", "crepe", "tessitura", "timbre", "stems", "collaborations"): self.assertNotIn(k, an)
        self.assertIsNone(d["artist"]["audience"]); self.assertIsNone(d["artist"]["breakout_prob"]); self.assertTrue(d["artist"]["breakout_insufficient_data"])
        self.assertIsNone(d["artist"]["momentum"]); self.assertEqual(d["assessment"]["tier"], "MORE EVIDENCE")

    def test_demo_artists_are_flagged_illustrative_and_fictional(self):
        demo.seed(); names = [r["name"] for r in db().execute("SELECT name FROM artists")]
        self.assertNotIn("Juliani", names)
        c = self.app.test_client(); c.post("/api/auth/login", json={"email": "v@x.t", "password": "Passw0rd!xx"})
        d = c.get("/api/artists/lab-default").json
        self.assertTrue(d["artist"]["demo"]); self.assertTrue(d["acoustic_analytics"]["illustrative"]); self.assertIn("crepe", d["acoustic_analytics"])

    def test_unknown_career_start_stays_unknown_on_the_card(self):
        aid = self.artist("No Start Year", year=None)
        c = self.app.test_client(); c.post("/api/auth/login", json={"email": "v@x.t", "password": "Passw0rd!xx"})
        a = [x for x in c.get("/api/artists").json["artists"] if x["id"] == aid][0]
        self.assertIsNone(a["tenure_years"]); self.assertIsNone(a["is_upcoming"]); self.assertFalse(a["career_start_known"])

class DbAdapter(unittest.TestCase):
    def setUp(self):
        pgsupport.prepare(); t = tempfile.mkdtemp()
        self.app = create_app({"DB": f"{t}/t.db", "UPLOAD_DIR": f"{t}/up", "FERNET_KEY": Fernet.generate_key(), "ORIGINS": ["http://x"]}); self.ctx = self.app.app_context(); self.ctx.push()
    def tearDown(self): self.ctx.pop()

    def test_rows_support_index_name_and_dict(self):
        d = db(); d.execute("INSERT INTO artists(name,country,first_seen) VALUES('A','KE',?)", (NOW,)); d.commit()
        r = d.execute("SELECT id,name,COUNT(*) OVER () n FROM artists").fetchone()
        self.assertEqual((r[1], r["name"], r[2]), ("A", "A", 1)); self.assertEqual(dict(r)["name"], "A"); self.assertEqual(d.execute("SELECT COUNT(*) FROM artists").fetchone()[0], 1)

    def test_lastrowid_only_where_there_is_an_id_and_text_keyed_tables_work(self):
        d = db(); self.assertIsInstance(d.execute("INSERT INTO artists(name,country,first_seen) VALUES('B','KE',?)", (NOW,)).lastrowid, int)
        d.execute("INSERT INTO settings(key,value,updated_at) VALUES('k','1',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (NOW,))
        from msanii.providers import track
        track("P", True); track("P", False, "boom"); track("P", True)                 # the real stats upsert (ambiguous-column error on PostgreSQL before the fix)
        s = d.execute("SELECT calls,errors,last_error FROM provider_stats WHERE provider='P'").fetchone()
        self.assertEqual((s["calls"], s["errors"], s["last_error"]), (3, 1, "boom"))
        self.assertEqual(d.execute("SELECT value FROM settings WHERE key='k'").fetchone()["value"], "1")

    def test_literal_percent_and_executemany(self):
        d = db(); d.executemany("INSERT INTO observations(artist_id,ts,metric,value,source) VALUES(?,?,?,?,?)", [])
        aid = d.execute("INSERT INTO artists(name,country,genres,first_seen) VALUES('C','KE','[\"x\"]',?)", (NOW,)).lastrowid
        d.executemany("INSERT INTO observations(artist_id,ts,metric,value,source) VALUES(?,?,?,?,?)", [(aid, NOW - i, "deezer_fans", 10 + i, "t") for i in range(3)]); d.commit()
        self.assertEqual(d.execute("SELECT COUNT(*) FROM artists WHERE genres LIKE '%\"x\"%'").fetchone()[0], 1)      # a literal % must survive the placeholder translation
        self.assertEqual(d.execute("SELECT COUNT(*) FROM observations WHERE artist_id=?", (aid,)).fetchone()[0], 3)

    def test_failed_statement_does_not_poison_the_transaction(self):
        d = db()
        with self.assertRaises(Exception): d.execute("INSERT INTO users(email,role,created_at) VALUES('x','nope',?)", (NOW,))
        self.assertEqual(d.execute("SELECT 1 AS one").fetchone()["one"], 1)

    def test_binary_columns_round_trip_as_bytes(self):
        from msanii.security import enc, dec
        d = db(); d.execute("INSERT INTO credentials(provider,ciphertext,updated_at) VALUES('p',?,?)", (enc({"k": "v"}), NOW)); d.commit()
        self.assertEqual(dec(d.execute("SELECT ciphertext FROM credentials WHERE provider='p'").fetchone()["ciphertext"]), {"k": "v"})

    def test_audit_chain_extends_and_verifies(self):
        from msanii.db import audit
        for i in range(3): audit("e%d" % i, {"i": i})
        self.assertIsNone(verify_audit())

class Startup(unittest.TestCase):
    def test_no_hardcoded_owner_account(self):
        pgsupport.prepare(); t = tempfile.mkdtemp()
        app = create_app({"DB": f"{t}/t.db", "UPLOAD_DIR": f"{t}/up", "FERNET_KEY": Fernet.generate_key(), "ORIGINS": ["http://x"]})
        with app.app_context(): self.assertIsNone(db().execute("SELECT 1 FROM users").fetchone())

    def test_serverless_without_postgres_fails_fast_with_a_clear_message(self):
        import os
        if pgsupport.PG_URL: self.skipTest("SQLite-only check")
        pgsupport.prepare(); os.environ.update(VERCEL="1", VERCEL_ENV="production")
        try:
            with self.assertRaises(RuntimeError) as cm: create_app({"FERNET_KEY": Fernet.generate_key()})
            self.assertIn("SUPABASE_DB_URL", str(cm.exception))
        finally:
            for k in ("VERCEL", "VERCEL_ENV"): os.environ.pop(k, None)

    def test_vercel_defaults_are_writable_tmp_paths_not_the_read_only_bundle(self):
        import os
        if pgsupport.PG_URL: self.skipTest("SQLite-only check")
        pgsupport.prepare(); os.environ.update(VERCEL="1", VERCEL_ENV="development")        # dev deployment: SQLite allowed, but only under /tmp
        try:
            app = create_app({"FERNET_KEY": Fernet.generate_key()})
            self.assertTrue(app.config["DB"].startswith("/tmp/")); self.assertTrue(app.config["UPLOAD_DIR"].startswith("/tmp/"))
        finally:
            for k in ("VERCEL", "VERCEL_ENV"): os.environ.pop(k, None)

    def test_postgres_url_gets_tls_unless_local(self):
        import os, importlib; m = importlib.import_module("msanii.db"); old = {k: os.environ.pop(k, None) for k in ("SUPABASE_DB_URL", "DATABASE_URL", "POSTGRES_URL")}
        try:
            os.environ["SUPABASE_DB_URL"] = "postgresql://u:p@db.example.supabase.co:6543/postgres"; self.assertTrue(m.get_pg_url().endswith("?sslmode=require"))
            os.environ["SUPABASE_DB_URL"] = "postgresql://u:p@localhost:5432/x"; self.assertNotIn("sslmode", m.get_pg_url())
            os.environ["SUPABASE_DB_URL"] = "sqlite:///x"; self.assertIsNone(m.get_pg_url())
        finally:
            for k, v in old.items():
                os.environ.pop(k, None)
                if v: os.environ[k] = v

if __name__ == "__main__": unittest.main()
