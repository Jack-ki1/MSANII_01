"""Upcoming artist demo dataset focusing strictly on artists with <= 5 years industry tenure.
All names, numbers and tracks are FICTIONAL SAMPLE DATA for trying the interface. Demo artists are flagged and never mixed with real data.
"""
import json, time, random
from .db import db
from .engine import restage

# name, country, city, genres, begin_year, base_fans, monthly_growth, days_history, spike_multiplier, platforms, (ugc_videos, creators, top3_share, countries), tracks
DEMO = [
    ("Wanjiru Echo", "KE", "Nairobi", ["Hip-Hop / Sheng", "Spoken Word", "Conscious Afro"], 2022, 62000, 0.248, 365, 0,
     [("lastfm_listeners", 2.8, 1.2), ("spotify_followers", 1.9, 1.3), ("deezer_fans", 1.1, 1.0)],
     (2640, 940, 18, 5), ["Mtaa Kwa Mtaa", "Kesho Ni Yetu", "Sauti ya Pembe", "Mwanga Mpya"]),
     
    ("Baraka Mshana", "TZ", "Dar es Salaam", ["Singeli", "Bongo Flava"], 2022, 38000, 0.180, 240, 2.2,
     [("lastfm_listeners", 2.2, 0.8), ("yt_subscribers", 1.5, 1.1)],
     (2100, 720, 22, 3), ["Kasi Kasi", "Vumbi", "Mchongoano"]),
     
    ("Kemi Akello", "UG", "Kampala", ["Afro-soul", "Contemporary Folk"], 2025, 4200, 0.280, 90, 0,
     [("audius_followers", 0.35, 1.5)],
     (85, 45, 32, 2), ["Wiye", "Kigezi Dawn"]),
     
    ("Ishimwe Grace", "RW", "Kigali", ["Afropop", "R&B"], 2023, 14000, 0.140, 365, 0,
     [("lastfm_listeners", 1.9, 0.9), ("yt_subscribers", 2.6, 0.8)],
     (410, 160, 48, 2), ["Urukundo", "Amahoro", "Humura"]),
     
    ("Nuru Kassim", "KE", "Mombasa", ["Taarab-pop", "Swahili RnB"], 2025, 3100, 0.220, 75, 0,
     [("audius_followers", 0.18, 1.3)],
     (38, 22, 38, 1), ["Pwani Glow", "Bahari Sweet"]),
     
    ("Zuri Ndegwa", "KE", "Nairobi", ["Afro-fusion", "Alt-soul"], 2023, 24000, 0.195, 365, 0,
     [("lastfm_listeners", 2.6, 1.0), ("audius_followers", 0.12, 1.4)],
     (680, 310, 11, 3), ["Mji wa Nuru", "Slow Burn", "Kesho Yetu"])
]

def seed():
    d = db(); rnd = random.Random(42); now = time.time(); n = 0
    ins = "INSERT INTO observations(artist_id,ts,metric,value,source) VALUES(?,?,?,?,?)"
    
    for name, cc, city, genres, by, base, gr, cov, spike, plats, ugc, songs in DEMO:
        if d.execute("SELECT 1 FROM artists WHERE name=? AND country=?", (name, cc)).fetchone():
            continue
            
        bio = f"Upcoming East African recording artist active since {by}. Focus on authentic grassroots growth, dynamic intonation, and high streaming engagement."
        story = f"Discovered through regional showcases and organic UGC audio usage. Demonstrates exceptional vocal tessitura, high code-switching vernacular appeal, and verified organic corridor streams."
        
        aid = d.execute(
            "INSERT INTO artists(name,country,city,genres,begin_year,ids,first_seen,bio,story) VALUES(?,?,?,?,?,?,?,?,?)",
            (name, cc, city, json.dumps(genres), by, json.dumps({"demo": True, "upcoming": True}), now - cov * 86400, bio, story)
        ).lastrowid
        
        # Primary monthly listeners telemetry series (matching prompt's ~75,109 for top upcoming artist)
        scale_base = base
        series = [("monthly_listeners", 1.0, 1.0), ("deezer_fans", 0.65, 0.9)] + plats
        
        for metric, scale, gm in series:
            for i in range(cov, -1, -3):
                # rising exponential velocity curve
                progress = (cov - i) / max(cov, 1)
                curve = (1.0 + gr * gm) ** ((cov - i) / 30.0)
                jitter = 1.0 + (rnd.random() - 0.48) * 0.05
                v = scale_base * scale * curve * jitter
                if spike and i <= 15:
                    v *= spike
                d.execute(ins, (aid, now - i * 86400, metric, round(v), "verified_dsp"))
                
        # UGC series
        for k in range(8, -1, -1):
            f = (9 - k) / 9.0
            for m, v in zip(("ugc_videos", "ugc_creators"), ugc[:2]):
                d.execute(ins, (aid, now - k * 14 * 86400, m, max(1, round(v * f * f)), "tiktok_reels_ugc"))
        for m, v in zip(("ugc_top3_share", "ugc_countries"), ugc[2:]):
            d.execute(ins, (aid, now, m, v, "manual_import"))
            
        # Seed songs
        for idx, t in enumerate(songs):
            d.execute(
                "INSERT INTO tracks(artist_id,title,album,source,source_id,duration,popularity,url) VALUES(?,?,?,?,?,?,?,?)",
                (aid, t, f"{name} Debut EP", "Verified DSP", f"{aid}-{idx}", rnd.randint(170, 245), rnd.randint(55, 96), "https://open.spotify.com")
            )
            
        # Seed acoustic measurements (CREPE, pitch range, dynamic range)
        meas = [
            ("crepe_f0_accuracy", "88.5%", 0.88, {"method": "CREPE deep convolutional pitch tracker", "threshold": "±20 cents"}),
            ("key", "E Minor", 0.89, {"method": "Krumhansl-Schmuckler chroma analysis", "root": "E"}),
            ("pitch_span_semitones", "31", 0.92, {"method": "PyIN / CREPE vocal tracking", "span": "C3 - G5"}),
            ("vibrato_rate", "5.4 Hz", 0.85, {"method": "Spectral autocorrelation", "depth": "±38 cents"}),
            ("hnr_db", "22.8 dB", 0.87, {"method": "Harmonic-to-Noise Ratio", "evaluation": "Crisp vocal projection"}),
            ("dynamic_range", "14.2 dB", 0.90, {"method": "p95-p10 RMS per second envelope", "section_lift": "+6.2 dB RMS"})
        ]
        for mn, mv, mc, mp in meas:
            d.execute(
                "INSERT INTO measurements(artist_id,name,value,confidence,provenance,ts) VALUES(?,?,?,?,?,?)",
                (aid, mn, mv, mc, json.dumps(mp), now - 5 * 86400)
            )
            
        d.commit()
        restage(aid)
        n += 1
        
    return n

def clear():
    d = db(); ids = [r[0] for r in d.execute("SELECT id FROM artists WHERE ids LIKE '%\"demo\": true%'")]
    if not ids: return 0
    q = ",".join("?" * len(ids))
    for t in ("decisions", "tasks", "reviews", "observations", "measurements", "uploads", "tracks", "media"):
        d.execute(f"DELETE FROM {t} WHERE artist_id IN ({q})", ids)
    d.execute(f"DELETE FROM artists WHERE id IN ({q})", ids)
    d.commit()
    return len(ids)
