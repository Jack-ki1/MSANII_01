import os, io, sys, csv, json, time, uuid, shutil, hashlib
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, g, current_app, send_file
from .db import db, audit, verify_audit, is_pg
from .security import (ApiError, body, field, require, hash_pw, check_pw, pw_ok, tok, sha, start_session, limited, ip, enc, dec, totp_ok,
                       new_totp_secret, SID, SESSION_TTL, EMAIL, DUMMY, ROLES, safe_url)
from .providers import REGISTRY, CTRY, listing, build, creds, ProviderError
from .geo import REGIONS, GENRES, DEFAULT_REGION
from . import engine, mail, media, ml
from .engine import DEFAULTS, AUD, MANUAL, CRIT

bp = Blueprint("api", __name__)
ACTIONS = ["Pursue", "Contact", "Request demo", "Schedule meeting", "Add to shortlist", "Monitor", "Reject", "Defer pending evidence"]
TIERS = ["PURSUE", "MEET", "WATCH", "MORE EVIDENCE"]

def artist_or_404(aid):
    r = db().execute("SELECT * FROM artists WHERE id=?", (aid,)).fetchone()
    if not r: raise ApiError("artist not found", 404)
    return r

def day(s, name):
    try: return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
    except (ValueError, TypeError): raise ApiError(f"{name} must be YYYY-MM-DD")

def card(r):
    aid = r["id"]; d = db(); m = engine.main_metric(aid); gr = engine.growth(aid, m) if m else None
    lv = d.execute("SELECT value FROM observations WHERE artist_id=? AND metric=? ORDER BY ts DESC LIMIT 1", (aid, m)).fetchone() if m else None
    tr = d.execute("SELECT title,preview_url,cover_url FROM tracks WHERE artist_id=? ORDER BY (preview_url IS NULL), COALESCE(popularity,0) DESC LIMIT 1", (aid,)).fetchone()
    
    tenure = ml.calculate_tenure(r["begin_year"], r["first_seen"])      # None when the career start year is unknown
    is_up = None if tenure is None else tenure <= ml.UPCOMING_YEARS
    series = {}
    if m:
        rows = d.execute("SELECT ts,value FROM observations WHERE artist_id=? AND metric=? ORDER BY ts", (aid, m)).fetchall()
        series[m] = [[row["ts"], row["value"]] for row in rows]
    breakout = ml.predict_breakout_probability(dict(r), series, {"momentum": gr["pct"] if gr else None})
    
    return {"id": aid, "name": r["name"], "country": r["country"], "city": r["city"], "genres": json.loads(r["genres"]),
            "stage": r["stage"] or (None if tenure is None else "Early Debut" if tenure <= 2 else "Emerging Breakout" if tenure <= 4 else "Developing Talent"),
            "begin_year": r["begin_year"], "tenure_years": tenure, "is_upcoming": is_up, "career_start_known": tenure is not None,
            "breakout_prob": breakout["prob_pct"], "velocity_category": breakout["category"], "breakout_insufficient_data": breakout["insufficient_data"],
            "is_new": r["first_seen"] > time.time() - 7 * 86400, "first_seen": r["first_seen"], "last_signal": r["last_signal"],
            "momentum": gr["pct"] if gr else None, "evidence": engine.evidence(aid),
            "demo": bool(json.loads(r["ids"]).get("demo")), "image_url": r["image_url"], "bio": (r["bio"] or "")[:220],
            "audience": {"metric": m, "value": lv[0]} if lv else None,
            "tracks": d.execute("SELECT COUNT(*) FROM tracks WHERE artist_id=?", (aid,)).fetchone()[0],
            "top_track": dict(tr) if tr else None, "links": len(json.loads(r["links"] or "{}"))}

def media_row(r):
    return {"id": r["id"], "kind": r["kind"], "title": r["title"], "url": r["url"], "status": r["status"], "ts": r["ts"], "by": r["email"], "has_file": bool(r["path"]), "result": json.loads(r["result"])}

@bp.get("/health")
def health(): return jsonify(ok=True)

# ---------------- auth ----------------
@bp.post("/auth/login")
def login():
    b = body(); email = field(b, "email", mx=254).lower(); pw = field(b, "password", mx=128)
    if limited(("login", ip(), email), 5, 300) or limited(("loginip", ip()), 30, 300):
        audit("login_throttled", {"email": email}); raise ApiError("too many attempts, try again later", 429)
    d = db(); u = d.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    ok = check_pw(u["pw_hash"] if u else DUMMY, pw) and bool(u) and bool(u["active"])
    if ok and u["mfa_enabled"]:
        code = str(b.get("code") or "")
        if not code: return jsonify(error="mfa code required", mfa_required=True), 401
        ok = totp_ok(dec(u["totp_secret"])["s"], code)
    if not ok:
        audit("login_failed", {"email": email}, u["id"] if u else None); raise ApiError("invalid credentials", 401)
    d.execute("DELETE FROM sessions WHERE expires_at<?", (time.time(),)); d.commit()
    sid, csrf = start_session(u["id"]); audit("login", None, u["id"])
    r = jsonify(user={"id": u["id"], "email": u["email"], "role": u["role"]}, csrf=csrf)
    r.set_cookie(SID, sid, httponly=True, samesite="Lax", secure=current_app.config["SECURE_COOKIES"], max_age=SESSION_TTL, path="/")
    return r

@bp.post("/auth/logout")
@require()
def logout():
    db().execute("DELETE FROM sessions WHERE sid_hash=?", (g.user["sid_hash"],)); db().commit(); audit("logout", None, g.user["id"])
    r = jsonify(ok=True); r.delete_cookie(SID, path="/"); return r

@bp.get("/auth/me")
@require()
def me(): return jsonify(user={k: g.user[k] for k in ("id", "email", "role")}, csrf=g.user["csrf"])

@bp.post("/auth/accept-invite")
def accept_invite():
    if limited(("inv", ip()), 10, 600): raise ApiError("too many attempts", 429)
    b = body(); t = field(b, "token", mx=100); pw = field(b, "password", mx=128)
    if not pw_ok(pw): raise ApiError("password must be 10-128 characters with letters and numbers")
    d = db(); i = d.execute("SELECT * FROM invites WHERE token_hash=? AND used=0 AND expires_at>?", (sha(t), time.time())).fetchone()
    if not i: raise ApiError("invalid or expired invite")
    if d.execute("SELECT 1 FROM users WHERE email=?", (i["email"],)).fetchone(): raise ApiError("account already exists", 409)
    d.execute("INSERT INTO users(email,pw_hash,role,created_at) VALUES(?,?,?,?)", (i["email"], hash_pw(pw), i["role"], time.time()))
    d.execute("UPDATE invites SET used=1 WHERE id=?", (i["id"],)); d.commit(); audit("invite_accepted", {"email": i["email"]}); return jsonify(ok=True), 201

# ---------------- access request workflow ----------------
def _issue_invite(email, role, by):
    t = tok()
    db().execute("INSERT INTO invites(email,role,token_hash,expires_at,invited_by) VALUES(?,?,?,?,?)", (email, role, sha(t), time.time() + 72 * 3600, by))
    return t

@bp.post("/auth/request-access")
def request_access():
    if limited(("req_acc", ip()), 5, 300):
        raise ApiError("too many requests, please try again later", 429)
    b = body()
    name = field(b, "full_name", mx=150)
    email = field(b, "email", mx=254).lower()
    if not EMAIL.match(email): raise ApiError("invalid email")
    org = str(b.get("organization") or "").strip()[:150]
    role = str(b.get("role_title") or "").strip()[:100]
    region = str(b.get("region") or "").strip()[:100]
    notes = str(b.get("notes") or "").strip()[:2000]
    d = db()
    # Same answer whether or not the address is already registered or already pending, so the form cannot be used to probe for accounts.
    reply = jsonify(ok=True, message="Your access request has been sent to the administrators. If it is approved you will receive an e-mail with a link to set your password."), 201
    if d.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone(): return reply
    if d.execute("SELECT 1 FROM access_requests WHERE email=? AND status='pending'", (email,)).fetchone(): return reply
    d.execute("INSERT INTO access_requests(full_name, email, organization, role_title, region, notes, status, token, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
              (name, email, org, role, region, notes, "pending", sha(tok()), time.time()))      # `token` is kept for schema compatibility; it is random, hashed and never used for approval
    d.commit()
    mail.send_access_request_notification({"full_name": name, "email": email, "organization": org, "role_title": role, "region": region, "notes": notes})
    audit("access_requested", {"email": email, "name": name, "org": org})
    return reply

@bp.get("/auth/access-requests")
@require("admin")
def list_access_requests():
    rows = db().execute("SELECT id,full_name,email,organization,role_title,region,notes,status,created_at,reviewed_at,reviewed_by FROM access_requests ORDER BY created_at DESC LIMIT 100").fetchall()
    return jsonify(requests=[dict(r) for r in rows])

@bp.post("/auth/access-requests/<int:rid>/approve")
@require("admin")
def admin_approve_request(rid):
    d = db(); r = d.execute("SELECT * FROM access_requests WHERE id=?", (rid,)).fetchone()
    if not r: raise ApiError("request not found", 404)
    if r["status"] != "pending": raise ApiError(f"request is already {r['status']}", 400)
    if d.execute("SELECT 1 FROM users WHERE email=?", (r["email"],)).fetchone(): raise ApiError("an account with this email already exists", 409)
    t = _issue_invite(r["email"], "reviewer", g.user["id"])
    d.execute("UPDATE access_requests SET status='approved', reviewed_at=?, reviewed_by=? WHERE id=?", (time.time(), g.user["id"], rid)); d.commit()
    audit("access_approved", {"email": r["email"], "role": "reviewer"}, g.user["id"])
    if mail.configured() and mail.send_access_approved(r["email"], r["full_name"], t): return jsonify(ok=True, email=r["email"], emailed=True)
    return jsonify(ok=True, email=r["email"], emailed=False, invite_token=t, expires_in_hours=72, note="Shown once. E-mail is not configured or failed; send the link yourself.")

@bp.post("/auth/access-requests/<int:rid>/reject")
@require("admin")
def admin_reject_request(rid):
    d = db()
    d.execute("UPDATE access_requests SET status='rejected', reviewed_at=?, reviewed_by=? WHERE id=? AND status='pending'", (time.time(), g.user["id"], rid)); d.commit()
    audit("access_rejected", {"id": rid}, g.user["id"])
    return jsonify(ok=True)

@bp.post("/auth/mfa/setup")
@require()
def mfa_setup():
    s = new_totp_secret(); db().execute("UPDATE users SET totp_secret=?,mfa_enabled=0 WHERE id=?", (enc({"s": s}), g.user["id"])); db().commit()
    return jsonify(secret=s, uri=f"otpauth://totp/MSANII:{g.user['email']}?secret={s}&issuer=MSANII")

@bp.post("/auth/mfa/enable")
@require()
def mfa_enable():
    code = field(body(), "code", mx=8); u = db().execute("SELECT totp_secret FROM users WHERE id=?", (g.user["id"],)).fetchone()
    if not u["totp_secret"] or not totp_ok(dec(u["totp_secret"])["s"], code): raise ApiError("invalid code")
    db().execute("UPDATE users SET mfa_enabled=1 WHERE id=?", (g.user["id"],)); db().commit(); audit("mfa_enabled", None, g.user["id"]); return jsonify(ok=True)

@bp.get("/auth/sessions")
@require()
def my_sessions():
    rows = db().execute("SELECT sid_hash,created_at,expires_at,ua FROM sessions WHERE user_id=? ORDER BY created_at DESC", (g.user["id"],)).fetchall()
    return jsonify(sessions=[{"created_at": r["created_at"], "expires_at": r["expires_at"], "ua": r["ua"], "current": r["sid_hash"] == g.user["sid_hash"]} for r in rows])

@bp.delete("/auth/sessions")
@require()
def end_sessions():
    db().execute("DELETE FROM sessions WHERE user_id=?", (g.user["id"],)); db().commit(); audit("sessions_revoked", None, g.user["id"])
    r = jsonify(ok=True); r.delete_cookie(SID, path="/"); return r

# ---------------- team & access (admin) ----------------
@bp.get("/users")
@require("admin")
def users():
    return jsonify(users=[{k: r[k] for k in ("id", "email", "role", "active", "mfa_enabled", "created_at")} for r in db().execute("SELECT * FROM users ORDER BY id")])

@bp.post("/users/invite")
@require("admin")
def invite():
    b = body(); email = field(b, "email", mx=254).lower(); role = field(b, "role", choices=list(ROLES))
    if not EMAIL.match(email): raise ApiError("invalid email")
    if db().execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone(): raise ApiError("user already exists", 409)
    t = tok(); db().execute("INSERT INTO invites(email,role,token_hash,expires_at,invited_by) VALUES(?,?,?,?,?)", (email, role, sha(t), time.time() + 72 * 3600, g.user["id"])); db().commit()
    audit("user_invited", {"email": email, "role": role}, g.user["id"])
    if mail.configured():
        try: mail.send_invite(email, t, role); return jsonify(emailed=True, expires_in_hours=72), 201
        except Exception: current_app.logger.warning("invite e-mail failed")
    return jsonify(invite_token=t, emailed=False, expires_in_hours=72, note="Shown once. E-mail is not configured or failed; send the link yourself."), 201

@bp.patch("/users/<int:uid>")
@require("admin")
def patch_user(uid):
    b = body(); d = db(); u = d.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not u: raise ApiError("user not found", 404)
    role = field(b, "role", choices=list(ROLES), req=False) or u["role"]; active = field(b, "active", bool, req=False); active = u["active"] if active is None else int(active)
    if (u["role"] == "admin" and u["active"]) and (role != "admin" or not active):
        if d.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND active=1 AND id!=?", (uid,)).fetchone()[0] == 0: raise ApiError("cannot remove the last active admin", 409)
    d.execute("UPDATE users SET role=?,active=? WHERE id=?", (role, active, uid))
    if b.get("reset_mfa") is True: d.execute("UPDATE users SET mfa_enabled=0,totp_secret=NULL WHERE id=?", (uid,))
    if role != u["role"] or not active or b.get("reset_mfa") is True: d.execute("DELETE FROM sessions WHERE user_id=?", (uid,))
    d.commit(); audit("user_changed", {"user": uid, "role": role, "active": active, "reset_mfa": b.get("reset_mfa") is True}, g.user["id"]); return jsonify(ok=True)

# ---------------- discover ----------------
@bp.get("/artists")
@require()
def artists():
    a = request.args; sql = "SELECT * FROM artists WHERE 1=1"; p = []
    ccs = [c for c in a.get("country", "").split(",") if c in CTRY]
    if ccs: sql += " AND country IN (%s)" % ",".join("?" * len(ccs)); p += ccs
    if a.get("genre"): sql += " AND genres LIKE ? ESCAPE '\\'"; p.append('%"' + a["genre"][:50].replace("\\", "").replace("%", "").replace("_", "") + '"%')
    if a.get("q"): sql += " AND name LIKE ? ESCAPE '\\'"; p.append("%" + a["q"][:100].replace("\\", "").replace("%", "").replace("_", "") + "%")
    
    current_year = time.localtime().tm_year
    up_filter = a.get("upcoming_filter", "all")
    if up_filter == "early":
        sql += " AND (begin_year >= ? OR begin_year IS NULL)"; p.append(current_year - 2)
    elif up_filter == "breakthrough":
        sql += " AND (begin_year >= ? AND begin_year <= ?)"; p.append(current_year - 5); p.append(current_year - 3)
    else:
        # Strict Upcoming Artist Focus: <= 5 years career tenure
        sql += " AND (begin_year >= ? OR begin_year IS NULL)"; p.append(current_year - 5)

    try: lim = min(max(int(a.get("limit", 100)), 1), 200); off = max(int(a.get("offset", 0)), 0)
    except ValueError: raise ApiError("limit/offset must be integers")
    rows = db().execute(sql + " ORDER BY first_seen DESC LIMIT ? OFFSET ?", (*p, lim, off)).fetchall()
    cards = [card(r) for r in rows]
    
    if up_filter == "accelerator":
        cards = [c for c in cards if (c.get("momentum") or 0) >= 0.20 or (c.get("breakout_prob") or 0) >= 80]
    elif up_filter == "sparks":
        cards = [c for c in cards if c.get("velocity_category") == "Viral UGC Spark" or (c.get("breakout_prob") or 0) >= 70]
        
    return jsonify(artists=cards)

@bp.get("/meta")
@require()
def meta():
    return jsonify(regions={r: [{"code": c, "name": n} for c, n in cs.items()] for r, cs in REGIONS.items()}, genres=GENRES, default_region=DEFAULT_REGION, workspace=engine.get_setting("workspace"))

@bp.post("/discovery/run")
@require("reviewer")
def discovery_run():
    b = request.get_json(silent=True) or {}; q = field(b, "q", mx=100, req=False); country = field(b, "country", mx=2, choices=list(CTRY), req=False); genre = field(b, "genre", mx=40, req=False)
    if limited(("run", g.user["id"]), 3, 600): raise ApiError("discovery runs are limited to 3 per 10 minutes", 429)
    rid = engine.run_discovery("manual", g.user["id"], q, country, genre); r = db().execute("SELECT * FROM runs WHERE id=?", (rid,)).fetchone()
    return jsonify(run={**{k: r[k] for k in r.keys()}, "errors": json.loads(r["errors"])}), 201

@bp.get("/discovery/runs")
@require()
def discovery_runs():
    return jsonify(runs=[{**{k: r[k] for k in r.keys()}, "errors": json.loads(r["errors"])} for r in db().execute("SELECT * FROM runs ORDER BY id DESC LIMIT 50")])

# ---------------- analyze ----------------
@bp.get("/artists/lab-default")
@require()
def lab_default():
    d = db()
    demo = d.execute("SELECT id FROM artists WHERE ids LIKE ? ORDER BY id LIMIT 1", ('%"demo"%',)).fetchone()
    if demo: return dossier(demo["id"])
    any_a = d.execute("SELECT id FROM artists ORDER BY id ASC LIMIT 1").fetchone()
    if any_a: return dossier(any_a["id"])
    raise ApiError("no artists available", 404)

@bp.get("/artists/<int:aid>")
@require()
def dossier(aid):
    a = artist_or_404(aid); d = db()
    try: days = int(request.args.get("days", 90))
    except ValueError: raise ApiError("days must be an integer")
    if days not in (7, 30, 90, 180, 365): raise ApiError("days must be 7, 30, 90, 180 or 365")
    s = engine.assess(aid); series = {}
    latest = {r["metric"]: {"value": r["value"], "ts": r["ts"], "source": r["source"]} for r in d.execute("SELECT o.metric,o.value,o.ts,o.source FROM observations o JOIN (SELECT metric,MAX(ts) m FROM observations WHERE artist_id=? GROUP BY metric) x ON x.metric=o.metric AND x.m=o.ts WHERE o.artist_id=?", (aid, aid))}
    for r in d.execute("SELECT metric,ts,value FROM observations WHERE artist_id=? AND ts>=? ORDER BY ts", (aid, time.time() - days * 86400)): series.setdefault(r["metric"], []).append([r["ts"], r["value"]])
    prof = {"bio": a["bio"], "story": a["story"], "image_url": a["image_url"], "links": json.loads(a["links"] or "{}"), "enriched_at": a["enriched_at"], "ids": json.loads(a["ids"])}
    tracks = [dict(r) for r in d.execute("SELECT id,title,album,source,preview_url,cover_url,duration,popularity,release_date,url FROM tracks WHERE artist_id=? ORDER BY (preview_url IS NULL), COALESCE(popularity,0) DESC LIMIT 30", (aid,))]
    mrows = [media_row(r) for r in d.execute("SELECT m.*,u.email FROM media m LEFT JOIN users u ON u.id=m.user_id WHERE m.artist_id=? ORDER BY m.ts DESC LIMIT 50", (aid,))]
    
    # Analytics are built only from data the platform holds. Missing inputs stay None; nothing is estimated to fill a gap.
    illustrative = bool(json.loads(a["ids"]).get("demo"))
    obs_list = [{"metric": k, "value": v["value"]} for k, v in latest.items()]
    organic = ml.evaluate_organic_integrity(dict(a), obs_list)
    mk = s.get("metric"); main = latest.get(mk) if mk else None
    listeners = (latest.get("monthly_listeners") or main or {}).get("value")
    val = ml.calculate_ar_advance_valuation(listeners, s.get("momentum"), organic["ratio"], len(tracks))
    stamp = lambda o: datetime.fromtimestamp(o["ts"], timezone.utc).strftime("%Y-%m-%d")
    observed = []
    if main: observed.append({"key": "audience", "label": f"Audience ({mk})", "value": f"{int(main['value']):,}", "note": f"{main['source']} on {stamp(main)}", "status": "Observed"})
    if s.get("momentum") is not None and s.get("growth"): observed.append({"key": "momentum", "label": "Momentum", "value": f"{s['momentum']:+.1%}", "note": f"over {s['growth']['span_days']} days", "status": "Observed"})
    if organic["ratio"] is not None: observed.append({"key": "organic", "label": "Last.fm plays per listener", "value": f"{organic['ratio']}", "note": organic["status_label"], "status": "Heuristic"})
    if s.get("artistic") is not None: observed.append({"key": "artistic", "label": "Artistic score (human)", "value": f"{s['artistic']}", "note": f"{s['avm']['reviews']} review(s)", "status": "Human"})
    bp = s["breakout_prediction"]
    if bp["prob_pct"] is not None: observed.append({"key": "breakout", "label": "Breakout score", "value": f"{bp['prob_pct']}%", "note": "heuristic, uncalibrated", "status": "Heuristic"})
    if val: observed.append({"key": "advance", "label": "Advance scenario", "value": val["formatted_advance"], "note": "assumption-driven, not a valuation", "status": "Scenario"})
    acoustic_analytics = {"illustrative": illustrative, "observed": observed, "organic": organic, "ar_valuation": val, "forecast": ml.forecast_trajectory(series.get(mk, [])) if mk else []}
    if illustrative: acoustic_analytics.update(ml.demo_fixtures())      # fictional sample visuals, only for demo artists

    return jsonify(artist={**card(a), **prof}, assessment=s, explanation=engine.explain(a, s), series=series, latest=latest, range_days=days, tracks=tracks, media=mrows,
                   acoustic_analytics=acoustic_analytics,
                   reviews=[{"id": r["id"], "reviewer": r["email"], "ts": r["ts"], "scores": json.loads(r["scores"]), "note": r["note"], "kind": "human"} for r in d.execute("SELECT r.*,u.email FROM reviews r JOIN users u ON u.id=r.user_id WHERE artist_id=? ORDER BY r.ts DESC", (aid,))],
                   measurements=[{"name": r["name"], "value": r["value"], "confidence": r["confidence"], "provenance": json.loads(r["provenance"]), "ts": r["ts"], "kind": "machine"} for r in d.execute("SELECT * FROM measurements WHERE artist_id=? ORDER BY ts DESC", (aid,))],
                   decisions=[{k: r[k] for k in ("action", "rationale", "owner", "follow_up", "tier", "ts", "email", "sig")} for r in d.execute("SELECT d.*,u.email FROM decisions d JOIN users u ON u.id=d.user_id WHERE artist_id=? ORDER BY d.ts DESC", (aid,))])

@bp.post("/artists/<int:aid>/reviews")
@require("reviewer")
def add_review(aid):
    artist_or_404(aid); b = body(); sc = b.get("scores")
    if not isinstance(sc, dict) or not sc or set(sc) - set(CRIT): raise ApiError("scores must be an object keyed by: " + ", ".join(CRIT))
    for k, v in sc.items():
        if isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= 5: raise ApiError(f"{k} must be an integer from 1 to 5")
    note = field(b, "note", mx=2000, req=False) or ""
    db().execute("INSERT INTO reviews(artist_id,user_id,scores,note,ts) VALUES(?,?,?,?,?)", (aid, g.user["id"], json.dumps(sc), note, time.time())); db().commit()
    audit("review_added", {"artist": aid}, g.user["id"]); return jsonify(ok=True), 201

@bp.post("/artists/<int:aid>/observations")
@require("reviewer")
def add_obs(aid):
    artist_or_404(aid); b = body(); m = field(b, "metric", choices=MANUAL); v = field(b, "value", float, 0, 1e12)
    ts = day(b["date"], "date") if b.get("date") else time.time()
    if ts > time.time() + 86400: raise ApiError("date cannot be in the future")
    db().execute("INSERT INTO observations(artist_id,ts,metric,value,source) VALUES(?,?,?,?,?)", (aid, ts, m, v, "manual:" + g.user["email"])); db().commit()
    audit("observation_imported", {"artist": aid, "metric": m}, g.user["id"]); return jsonify(ok=True), 201

@bp.patch("/artists/<int:aid>")
@require("reviewer")
def patch_artist(aid):
    artist_or_404(aid); b = body(); sets = {}
    if "story" in b: sets["story"] = field(b, "story", mx=4000, req=False) or ""
    if "city" in b: sets["city"] = field(b, "city", mx=100, req=False) or ""
    if "genres" in b:
        gl = b["genres"]
        if not isinstance(gl, list) or len(gl) > 8 or not all(isinstance(x, str) and 0 < len(x) <= 40 for x in gl): raise ApiError("genres must be up to 8 short names")
        sets["genres"] = json.dumps(gl)
    if "image_url" in b:
        u = b["image_url"] or None
        if u and not safe_url(u): raise ApiError("image_url must be an https link")
        sets["image_url"] = u
    if not sets: raise ApiError("nothing to update")
    db().execute("UPDATE artists SET " + ", ".join(f"{k}=?" for k in sets) + " WHERE id=?", (*sets.values(), aid)); db().commit()      # column names come from the fixed set above
    audit("artist_edited", {"artist": aid, "fields": list(sets)}, g.user["id"]); return jsonify(ok=True)

@bp.post("/artists/<int:aid>/enrich")
@require("reviewer")
def enrich_artist(aid):
    artist_or_404(aid)
    if limited(("enrich", g.user["id"]), 10, 300): raise ApiError("too many refreshes", 429)
    r = engine.enrich(aid); audit("artist_enriched", {"artist": aid, "tracks": r["tracks"]}, g.user["id"]); return jsonify(r)

@bp.post("/artists/<int:aid>/observations/bulk")
@require("reviewer")
def bulk_obs(aid):
    artist_or_404(aid); rows = body().get("rows")
    if not isinstance(rows, list) or not 0 < len(rows) <= 500: raise ApiError("rows must be a list of 1-500 items")
    ins = []
    for i, r in enumerate(rows):
        if not isinstance(r, dict): raise ApiError(f"row {i + 1} is invalid")
        try: m = field(r, "metric", choices=MANUAL); v = field(r, "value", float, 0, 1e12); ts = day(r["date"], "date") if r.get("date") else time.time()
        except ApiError as e: raise ApiError(f"row {i + 1}: {e.msg}")
        if ts > time.time() + 86400: raise ApiError(f"row {i + 1}: date cannot be in the future")
        ins.append((aid, ts, m, v, "csv:" + g.user["email"]))
    db().executemany("INSERT INTO observations(artist_id,ts,metric,value,source) VALUES(?,?,?,?,?)", ins); db().commit()
    audit("observations_bulk_import", {"artist": aid, "rows": len(ins)}, g.user["id"]); return jsonify(imported=len(ins)), 201

# ---------------- Song Lab: uploads and links ----------------
def _store_media(aid, kind, title, url, path, digest, res):
    d = db(); mid = d.execute("INSERT INTO media(artist_id,kind,title,url,path,sha256,status,result,user_id,ts) VALUES(?,?,?,?,?,?,?,?,?,?)", (aid, kind, title, url, path, digest, res["status"], json.dumps(res), g.user["id"], time.time())).lastrowid
    for m in res.get("measurements", []):
        d.execute("INSERT INTO measurements(artist_id,name,value,confidence,provenance,ts,media_id) VALUES(?,?,?,?,?,?,?)", (aid, m["name"], f"{m['value']} {m['unit']}".strip(), m["confidence"], json.dumps({"media_id": mid, "method": m["method"], "note": m["note"]}), time.time(), mid))
    d.commit(); return mid

@bp.post("/artists/<int:aid>/media")
@require("reviewer")
def upload_media(aid):
    artist_or_404(aid); f = request.files.get("file")
    if not f: raise ApiError("file is required")
    if request.form.get("rights_cleared") != "true": raise ApiError("confirm rights_cleared=true: only upload audio or video you are licensed to analyse")
    if limited(("media", g.user["id"]), 10, 600): raise ApiError("too many uploads, try again later", 429)
    data = f.read(); k = media.sniff(data[:16])
    if not k: raise ApiError("unsupported file: wav, mp3, flac, ogg, mp4 or webm only")
    kind, ext = k; digest = hashlib.sha256(data).hexdigest(); path = os.path.join(current_app.config["UPLOAD_DIR"], uuid.uuid4().hex + "." + ext)
    with open(path, "wb") as fh: fh.write(data)
    title = (request.form.get("title") or os.path.splitext(f.filename or "")[0] or "Untitled")[:200]
    res = media.analyze_file(path, kind, ext)
    res["rights"] = {"master_holder": (request.form.get("master_holder") or "")[:200], "splits_documented": request.form.get("splits_documented") == "true", "samples_cleared": request.form.get("samples_cleared") == "true"}
    if res["status"] == "done" and kind == "audio":
        try:
            for n, v, c, p in (engine.analyze_audio(path, digest) or []): res["measurements"].append({"name": n, "value": v, "unit": "", "confidence": c, "method": p["method"], "note": p["note"]})
        except Exception: current_app.logger.warning("librosa analysis failed")
    mid = _store_media(aid, kind, title, None, path, digest, res); audit("media_uploaded", {"artist": aid, "media": mid, "kind": kind, "status": res["status"]}, g.user["id"])
    r = db().execute("SELECT m.*,u.email FROM media m LEFT JOIN users u ON u.id=m.user_id WHERE m.id=?", (mid,)).fetchone(); return jsonify(media=media_row(r)), 201

@bp.post("/artists/<int:aid>/media/link")
@require("reviewer")
def add_link(aid):
    artist_or_404(aid); b = body(); url = field(b, "url", mx=400)
    if not media.classify_link(url): raise ApiError("unsupported link: use https links from YouTube, Spotify, SoundCloud, Audius or TikTok")
    if limited(("media", g.user["id"]), 10, 600): raise ApiError("too many requests, try again later", 429)
    res = media.analyze_link(url, creds("YouTube Data API").get("api_key")); title = (field(b, "title", mx=200, req=False) or (res.get("meta") or {}).get("title") or url)[:200]
    mid = _store_media(aid, "link", title, url, None, None, res); audit("media_link_added", {"artist": aid, "media": mid, "status": res["status"]}, g.user["id"])
    r = db().execute("SELECT m.*,u.email FROM media m LEFT JOIN users u ON u.id=m.user_id WHERE m.id=?", (mid,)).fetchone(); return jsonify(media=media_row(r)), 201

@bp.get("/media/<int:mid>/file")
@require()
def media_file(mid):
    r = db().execute("SELECT path FROM media WHERE id=?", (mid,)).fetchone()
    if not r or not r["path"]: raise ApiError("not found", 404)
    root = os.path.realpath(current_app.config["UPLOAD_DIR"]); p = os.path.realpath(r["path"])
    if not p.startswith(root + os.sep) or not os.path.exists(p): raise ApiError("not found", 404)
    return send_file(p, mimetype=media.MIME.get(p.rsplit(".", 1)[-1], "application/octet-stream"), conditional=True)

@bp.delete("/media/<int:mid>")
@require("reviewer")
def media_delete(mid):
    r = db().execute("SELECT path FROM media WHERE id=?", (mid,)).fetchone()
    if not r: raise ApiError("not found", 404)
    root = os.path.realpath(current_app.config["UPLOAD_DIR"])
    if r["path"] and os.path.realpath(r["path"]).startswith(root + os.sep) and os.path.exists(r["path"]): os.remove(r["path"])
    db().execute("DELETE FROM measurements WHERE media_id=?", (mid,)); db().execute("DELETE FROM media WHERE id=?", (mid,)); db().commit()
    audit("media_deleted", {"media": mid}, g.user["id"]); return jsonify(ok=True)

# ---------------- recommend ----------------
@bp.get("/recommendations")
@require()
def recommendations():
    out = []
    for r in db().execute("SELECT * FROM artists WHERE COALESCE(stage,'')!='Established'").fetchall():
        s = engine.assess(r["id"]); out.append({"artist": card(r), "tier": s["tier"], "artistic": s["artistic"], "momentum": s["momentum"], "integrity_flags": len(s["flags"]), "evidence": s["evidence"], "explanation": engine.explain(r, s)})
    out.sort(key=lambda x: (TIERS.index(x["tier"]), -(x["artistic"] or 0)))
    return jsonify(recommendations=out, counts={t: sum(1 for o in out if o["tier"] == t) for t in TIERS}, models=engine.model_status())

@bp.get("/models")
@require()
def models(): return jsonify(engine.model_status())

@bp.post("/models/retrain")
@require("admin")
def retrain_models():
    # There is nothing to retrain: no outcome labels are stored, so no model can be fitted. Say so instead of reporting a fake success.
    return jsonify(ok=False, trained=False, error="Retraining is not available: the platform has no outcome labels yet, so no model is fitted.", status=engine.model_status()), 501

@bp.post("/decisions")
@require("reviewer")
def add_decision():
    b = body(); aid = field(b, "artist_id", int, 1, 10 ** 9); artist_or_404(aid); act = field(b, "action", choices=ACTIONS)
    why = field(b, "rationale", mx=2000, mn=3); owner = field(b, "owner", mx=100, req=False); fu = field(b, "follow_up", req=False)
    if fu: day(fu, "follow_up")
    tier = engine.assess(aid)["tier"]; ts = time.time()
    sig = hashlib.sha256(json.dumps({"artist_id": aid, "action": act, "rationale": why, "owner": owner, "follow_up": fu, "tier": tier, "by": g.user["email"], "ts": ts}, sort_keys=True).encode()).hexdigest()
    db().execute("INSERT INTO decisions(artist_id,user_id,action,rationale,owner,follow_up,tier,ts,sig) VALUES(?,?,?,?,?,?,?,?,?)", (aid, g.user["id"], act, why, owner, fu, tier, ts, sig)); db().commit()
    audit("decision", {"artist": aid, "action": act, "tier": tier, "sig": sig[:16]}, g.user["id"]); return jsonify(ok=True, sig=sig), 201

@bp.get("/decisions")
@require()
def decisions():
    rows = db().execute("SELECT d.*,u.email,a.name FROM decisions d JOIN users u ON u.id=d.user_id JOIN artists a ON a.id=d.artist_id ORDER BY d.ts DESC LIMIT 200").fetchall()
    return jsonify(decisions=[{**{k: r[k] for k in ("id", "artist_id", "name", "action", "rationale", "owner", "follow_up", "tier", "ts", "email", "sig")}, "since_pct": engine.since_decision(r["artist_id"], r["ts"])} for r in rows])

# ---------------- settings ----------------
def check_setting(key, v):
    if key not in DEFAULTS: raise ApiError("unknown settings group", 404)
    if not isinstance(v, dict): raise ApiError("object required")
    base = DEFAULTS[key]; bad = set(v) - set(base)
    if bad: raise ApiError("unknown fields: " + ", ".join(sorted(bad)))
    out = {**engine.get_setting(key), **v}
    for k, dv in base.items():
        x = out[k]
        if isinstance(dv, bool) != isinstance(x, bool) or (isinstance(dv, (int, float)) and not isinstance(dv, bool) and (isinstance(x, bool) or not isinstance(x, (int, float)))) \
           or (isinstance(dv, str) and not isinstance(x, str)) or (isinstance(dv, list) and not isinstance(x, list)): raise ApiError(f"{k} has the wrong type")
    if key == "discovery":
        if not all(c in CTRY for c in out["countries"]): raise ApiError("countries must be supported ISO codes: " + ", ".join(CTRY))
        if not all(isinstance(x, str) and 0 < len(x) <= 40 for x in out["genres"]): raise ApiError("genres must be short strings")
        if not all(p in REGISTRY for p in out["providers"] + out["signal_providers"] + out["profile_providers"]): raise ApiError("unknown provider in list")
        if out["auto_minutes"] not in (0, 30, 60, 90): raise ApiError("auto_minutes must be 0, 30, 60 or 90")
        if not 1 <= out["limit"] <= 50: raise ApiError("limit out of range")
    if key == "weights" and (any(not isinstance(x, int) or not 0 <= x <= 100 for x in out.values()) or sum(out.values()) != 100): raise ApiError("weights must be integers 0-100 summing to 100")
    if key == "thresholds" and not (all(0 <= out[k] <= 1 for k in ("min_evidence", "flag_confidence")) and all(0 <= out[k] <= 100 for k in ("pursue_quality", "meet_quality")) and -1 <= out["pursue_growth"] <= 10 and -1 <= out["meet_growth"] <= 10 and 10 <= out["min_labelled"] <= 10 ** 6 and 0 <= out["min_reviews"] <= 10): raise ApiError("threshold out of range")
    if key == "automation" and not 7 <= out["bimonthly_days"] <= 90: raise ApiError("bimonthly_days must be 7-90")
    if key == "workspace" and (out["region"] not in REGIONS or (out["default_country"] and out["default_country"] not in REGIONS[out["region"]])): raise ApiError("region or default country invalid")
    if key == "workspace" and (any(len(out[k]) > 100 for k in ("company", "timezone", "currency")) or not 30 <= out["retention_days"] <= 3650): raise ApiError("workspace value out of range")
    return out

@bp.get("/settings")
@require("reviewer")
def get_settings(): return jsonify({k: engine.get_setting(k) for k in DEFAULTS})

@bp.put("/settings/<key>")
@require("admin")
def put_settings(key):
    v = check_setting(key, body()); db().execute("INSERT INTO settings VALUES(?,?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_by=excluded.updated_by,updated_at=excluded.updated_at", (key, json.dumps(v), g.user["id"], time.time())); db().commit()
    audit("settings_changed", {"group": key, "value": v}, g.user["id"]); return jsonify(v)

# ---------------- data providers ----------------
@bp.get("/providers")
@require("reviewer")
def providers(): return jsonify(providers=listing())          # never includes credential values

@bp.put("/providers/<name>/credentials")
@require("admin")
def set_creds(name):
    cls = REGISTRY.get(name)
    if not cls: raise ApiError("unknown provider", 404)
    if not cls.fields: raise ApiError("this provider takes no credentials")
    b = body(); extra = set(b) - set(cls.fields)
    if extra: raise ApiError("unexpected fields: " + ", ".join(sorted(extra)))
    vals = {f: field(b, f, mx=256, mn=4) for f in cls.fields}
    db().execute("INSERT INTO credentials VALUES(?,?,?,?) ON CONFLICT(provider) DO UPDATE SET ciphertext=excluded.ciphertext,updated_by=excluded.updated_by,updated_at=excluded.updated_at", (name, enc(vals), g.user["id"], time.time())); db().commit()
    audit("credential_update", {"provider": name}, g.user["id"]); return jsonify(ok=True, configured=True)

@bp.delete("/providers/<name>/credentials")
@require("admin")
def del_creds(name):
    db().execute("DELETE FROM credentials WHERE provider=?", (name,)); db().commit(); audit("credential_removed", {"provider": name}, g.user["id"]); return jsonify(ok=True)

@bp.put("/providers/<name>/tuning")
@require("admin")
def tune_provider(name):
    if name not in REGISTRY: raise ApiError("unknown provider", 404)
    b = body()
    prio = int(b.get("priority", 5))
    limit = int(b.get("rate_limit_per_min", 60))
    enabled = bool(b.get("enabled", True))
    tuning = {"priority": min(max(prio, 1), 10), "rate_limit_per_min": limit, "enabled": enabled}
    db().execute("INSERT INTO settings(key, value, updated_by, updated_at) VALUES(?,?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_by=excluded.updated_by, updated_at=excluded.updated_at",
                 (f"provider_tuning:{name}", json.dumps(tuning), g.user["id"], time.time()))
    db().commit()
    audit("provider_tuned", {"provider": name, "tuning": tuning}, g.user["id"])
    return jsonify(ok=True, tuning=tuning)

@bp.post("/providers/<name>/test")
@require("admin")
def test_provider(name):
    if name not in REGISTRY: raise ApiError("unknown provider", 404)
    if limited(("ptest", g.user["id"]), 10, 300): raise ApiError("too many tests", 429)
    try: build(name).test(); res = {"ok": True, "detail": "connection ok"}
    except ProviderError as e: res = {"ok": False, "detail": str(e)}
    audit("provider_test", {"provider": name, "ok": res["ok"]}, g.user["id"]); return jsonify(res)

# ---------------- security & audit ----------------
@bp.get("/audit")
@require("admin")
def audit_log():
    rows = db().execute("SELECT a.id,a.ts,a.ip,a.event,a.detail,u.email FROM audit a LEFT JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT 200").fetchall()
    return jsonify(events=[{**{k: r[k] for k in ("id", "ts", "ip", "event", "email")}, "detail": json.loads(r["detail"])} for r in rows], chain_broken_at=verify_audit())

@bp.get("/export/artists")
@require("admin")
def export_artists():
    rows = [card(r) for r in db().execute("SELECT * FROM artists")]; audit("data_export", {"what": "artists", "rows": len(rows)}, g.user["id"]); return jsonify(artists=rows)

# ---------------- review tasks (in-app notifications) ----------------
@bp.get("/tasks")
@require()
def tasks():
    engine.generate_reviews()
    rows = db().execute("SELECT t.id,t.kind,t.created,t.artist_id,a.name FROM tasks t JOIN artists a ON a.id=t.artist_id WHERE t.done=0 ORDER BY t.created DESC LIMIT 100").fetchall()
    return jsonify(tasks=[{k: r[k] for k in ("id", "kind", "created", "artist_id", "name")} for r in rows])

@bp.post("/tasks/<int:tid>/done")
@require("reviewer")
def task_done(tid):
    c = db().execute("UPDATE tasks SET done=1,done_by=?,done_at=? WHERE id=? AND done=0", (g.user["id"], time.time(), tid)); db().commit()
    if not c.rowcount: raise ApiError("task not found", 404)
    audit("task_done", {"task": tid}, g.user["id"]); return jsonify(ok=True)

@bp.post("/auth/change-password")
@require()
def change_password():
    b = body(); cur = field(b, "current", mx=128); new = field(b, "new", mx=128)
    if limited(("pw", g.user["id"]), 5, 300): raise ApiError("too many attempts", 429)
    u = db().execute("SELECT pw_hash FROM users WHERE id=?", (g.user["id"],)).fetchone()
    if not check_pw(u["pw_hash"], cur): audit("password_change_failed", None, g.user["id"]); raise ApiError("current password is incorrect")
    if not pw_ok(new) or new == cur: raise ApiError("new password must be 10-128 characters with letters and numbers, and differ from the current one")
    db().execute("UPDATE users SET pw_hash=? WHERE id=?", (hash_pw(new), g.user["id"])); db().execute("DELETE FROM sessions WHERE user_id=? AND sid_hash!=?", (g.user["id"], g.user["sid_hash"])); db().commit()
    audit("password_changed", None, g.user["id"]); return jsonify(ok=True)

@bp.get("/system")
@require("admin")
def system():
    d = db(); counts = {t: d.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("users", "artists", "observations", "reviews", "decisions", "tracks", "media", "runs", "tasks", "audit")}
    hb = d.execute("SELECT value FROM settings WHERE key='_heartbeat'").fetchone()
    try: import librosa; lib = True
    except ImportError: lib = False
    return jsonify(version="0.4.0", python=sys.version.split()[0], database="postgresql" if is_pg() else "sqlite", db_bytes=(None if is_pg() or not os.path.exists(current_app.config["DB"]) else os.path.getsize(current_app.config["DB"])), counts=counts, ffmpeg=bool(shutil.which("ffmpeg")), librosa=lib,
                   scheduler_heartbeat=float(hb["value"]) if hb else None, production=bool(current_app.config["SECURE_COOKIES"]), smtp=mail.configured(), region=engine.get_setting("workspace")["region"])
