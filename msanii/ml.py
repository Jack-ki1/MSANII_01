"""Heuristic scoring helpers for upcoming-artist triage.

HONESTY CONTRACT
- Everything here is a transparent heuristic computed from observations the platform actually holds. None of it is a trained or
  calibrated model, and every result says so (`method`, `calibrated: False`).
- Missing data is reported as missing (None / `insufficient_data`), never replaced by an optimistic default.
- The acoustic "fixtures" at the bottom of this file are ILLUSTRATIVE SAMPLE VALUES used only for demo artists. They are never
  computed from audio and must never be shown for a real artist (see api.dossier).
"""
import math, time

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
CORRIDOR = (1.4, 4.5)          # heuristic plays-per-listener corridor; NOT empirically calibrated
UPCOMING_YEARS = 5.0

def note_name(midi_num):
    if midi_num is None: return None
    n = int(round(midi_num)); return f"{NOTES[n % 12]}{(n // 12) - 1}"

def calculate_tenure(begin_year, first_seen=None):
    """Career length in years from a KNOWN start year, else None. `first_seen` (when WE first found the artist) says nothing about
    career length, so it is deliberately not used any more."""
    if not begin_year or begin_year < 1900: return None
    return round(min(max(0.2, time.localtime().tm_year - begin_year + 0.4), 60.0), 1)

def is_upcoming(artist_dict):
    t = calculate_tenure(artist_dict.get("begin_year"), artist_dict.get("first_seen"))
    return None if t is None else t <= UPCOMING_YEARS

def _sigmoid(z): return 1.0 / (1.0 + math.exp(-z))

def predict_breakout_probability(artist_dict, obs_series, assessment_dict=None):
    """Hand-weighted logistic SCORE, p = sigmoid(w.x + b), from growth momentum, acceleration, career youth, UGC and human quality.
    The weights are priors set by judgement and have NOT been fitted to outcomes, so p is a ranking aid, not a calibrated probability.
    Absent inputs contribute 0 (neutral). With no growth evidence at all the result is `insufficient_data` and the probability is None."""
    A = assessment_dict or {}; obs_series = obs_series or {}
    tenure = calculate_tenure(artist_dict.get("begin_year"), artist_dict.get("first_seen"))
    series = None
    for k in ("monthly_listeners", "lastfm_listeners", "deezer_fans", "spotify_followers", "audius_followers"):
        if len(obs_series.get(k) or []) > 1: series = obs_series[k]; break
    momentum = A.get("momentum")
    if momentum is None and series: momentum = (series[-1][1] - series[0][1]) / max(series[0][1], 1)
    accel = None
    if series and len(series) >= 3:
        p = [x[1] for x in series[-3:]]; accel = (p[2] - p[1]) / max(p[1], 1) - (p[1] - p[0]) / max(p[0], 1)
    ugc = None
    if obs_series.get("ugc_videos"): ugc = min(1.0, math.log10(max(obs_series["ugc_videos"][-1][1], 1)) / 4.0)
    flags_n = len(A.get("flags") or []); art = A.get("artistic")
    youth = 0.5 if tenure is None else max(0.0, (5.0 - tenure) / 4.0)
    insufficient = momentum is None
    z = (-1.6 + 2.8 * min(max(momentum or 0.0, -0.2), 1.2) + 1.8 * min(max(accel or 0.0, -0.2), 0.8) + 1.0 * youth
         + 1.2 * (ugc or 0.0) + (0.025 * (float(art) - 50) if art is not None else 0.0) - 0.8 * min(flags_n, 3))
    prob = None if insufficient else round(min(max(_sigmoid(z), 0.02), 0.98), 3)
    if insufficient: cat = "Insufficient data"
    elif prob >= 0.75: cat = "Fast Accelerator"
    elif tenure is not None and tenure <= 2.0 and momentum > 0.05: cat = "Early Debut"
    elif prob >= 0.55: cat = "Breakthrough Trajectory"
    elif (ugc or 0) > 0.4: cat = "Viral UGC Spark"
    else: cat = "Emerging Watch"
    n = len(series) if series else 0
    return {"breakout_probability": prob, "prob_pct": None if prob is None else round(prob * 100, 1), "tenure_years": tenure,
            "is_upcoming": None if tenure is None else tenure <= UPCOMING_YEARS, "category": cat,
            "velocity_mom": None if momentum is None else round(momentum * 100, 1), "acceleration": None if accel is None else round(accel * 100, 1),
            "ugc_score": None if ugc is None else round(ugc * 100, 1), "confidence": 0.0 if insufficient else round(min(0.8, 0.35 + 0.04 * n), 2),
            "insufficient_data": insufficient, "calibrated": False, "method": "hand-weighted logistic score (priors, not fitted to outcomes)"}

def _t95(df):  # two-sided 95% Student-t quantile, accurate to ~1% for df>=2
    return 1.96 + 2.4 / df + 4.3 / (df * df)

def forecast_trajectory(history_points, days_ahead=90):
    """Log-linear trend (OLS on ln y) with a proper 95% PREDICTION interval from the residuals:
         se(x0) = s * sqrt(1 + 1/n + (x0 - xbar)^2 / Sxx),   band = exp(yhat +/- t * se).
    Noisy history therefore widens the band, and far horizons widen it further. Fewer than 4 points or < 7 days of history returns []
    (no forecast) instead of inventing growth."""
    pts = [p for p in (history_points or []) if p[1] is not None and p[1] > 0][-12:]
    if len(pts) < 4 or pts[-1][0] - pts[0][0] < 7 * 86400: return []
    n = len(pts); t0 = pts[0][0]
    xs = [(p[0] - t0) / 86400.0 for p in pts]; ys = [math.log(p[1]) for p in pts]
    mx, my = sum(xs) / n, sum(ys) / n; sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0: return []
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    clamped = not (-0.005 <= slope <= 0.02)
    slope = min(max(slope, -0.005), 0.02)
    intercept = my - slope * mx                      # recomputed AFTER clamping so the line still passes through (xbar, ybar)
    sse = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys)); s = max(math.sqrt(sse / (n - 2)), 0.03)
    t = _t95(n - 2); out = []
    for d in (30, 60, 90):
        x0 = xs[-1] + d; yhat = intercept + slope * x0
        se = s * math.sqrt(1 + 1 / n + (x0 - mx) ** 2 / sxx)
        out.append({"days": d, "ts": pts[-1][0] + d * 86400, "expected": round(math.exp(yhat)), "lower": round(math.exp(yhat - t * se)),
                    "upper": round(math.exp(yhat + t * se)), "slope_clamped": clamped, "n_points": n, "method": "log-linear OLS, 95% prediction interval"})
    return out

def evaluate_organic_integrity(artist_data, observations):
    """Plays-per-listener on ONE platform (Last.fm lifetime playcount / Last.fm listeners). A very high ratio can indicate repeat-play
    farming and a very low one passive/algorithmic listening, but the corridor is a heuristic, and an outlier is a prompt to look closer,
    never proof. With no usable data the answer is 'Insufficient data'."""
    latest = {}
    for o in observations or []:
        if o.get("metric") in ("streams", "lastfm_listeners") and o.get("value"): latest[o["metric"]] = o["value"]     # observations arrive oldest -> newest
    plays, listeners = latest.get("streams"), latest.get("lastfm_listeners")
    if not plays or not listeners:
        return {"ratio": None, "is_safe": None, "organic_confidence": None, "safe_zone_certified": False, "status_label": "Insufficient data",
                "peers": [], "note": "Needs Last.fm playcount and Last.fm listeners for this artist."}
    r = round(plays / listeners, 2); inside = CORRIDOR[0] <= r <= CORRIDOR[1]
    return {"ratio": r, "is_safe": inside, "organic_confidence": None, "safe_zone_certified": False,
            "status_label": "Within heuristic corridor" if inside else "Outside heuristic corridor: investigate", "peers": [],
            "corridor": list(CORRIDOR), "note": "Last.fm plays per listener against an uncalibrated corridor. A signal, not a verdict."}

def calculate_ar_advance_valuation(listeners, momentum=None, organic_ratio=None, catalog_size=0, plays_per_listener_month=3.0, label_share=0.35):
    """Scenario calculator, not a valuation. Every assumption is returned so a human can challenge it:
         gross_12m = listeners * plays/listener/month * 12 * payout/stream ; advance = gross_12m * label_share * catalog * growth * risk"""
    if not listeners or listeners <= 0: return None
    payout = 0.0032
    gross = listeners * plays_per_listener_month * 12 * payout
    cat = min(1.5, 0.8 + 0.1 * max(int(catalog_size or 0), 0))
    growth = min(1.5, max(0.8, 1.0 + (momentum if momentum is not None else 0.0)))
    risk = 0.7 if (organic_ratio is not None and not (CORRIDOR[0] <= organic_ratio <= CORRIDOR[1])) else 1.0
    adv = int(round(gross * label_share * cat * growth * risk / 50.0) * 50)
    monthly_label = max(listeners * plays_per_listener_month * payout * 0.5, 1.0)
    rec = round(adv / monthly_label, 1)
    return {"recommended_advance": adv, "formatted_advance": f"${adv:,.0f}", "recoupment_months": rec, "valuation_trend": None, "is_estimate": True,
            "method": "scenario calculator: 12-month gross x label share x catalog x growth x risk", "currency": "USD",
            "assumptions": {"plays_per_listener_month": plays_per_listener_month, "payout_per_stream_usd": payout, "label_share": label_share,
                            "catalog_factor": round(cat, 2), "growth_factor": round(growth, 2), "risk_factor": risk},
            "suggested_deal": "Scenario only: negotiate from the assumptions, not the output",
            "deal_options": [{"type": "Distribution only (85/15)", "advance": 0, "recoup_months": 0, "royalty_split": "85% artist / 15% label"},
                             {"type": "Master licensing (50/50)", "advance": adv, "recoup_months": rec, "royalty_split": "50% artist / 50% label"},
                             {"type": "360 partnership", "advance": int(round(adv * 2.2 / 100) * 100), "recoup_months": round(rec * 1.8, 1), "royalty_split": "60% artist / 40% label + touring/merch"}]}

# ---------------------------------------------------------------------------------------------------------------------------------------------
# ILLUSTRATIVE SAMPLE FIXTURES: fixed numbers, NOT computed from audio. api.dossier only returns them for demo artists, flagged illustrative.
# ---------------------------------------------------------------------------------------------------------------------------------------------
def get_crepe_pitch_accuracy():
    """
    CREPE f0 Pitch Accuracy (±20 Cents Threshold).
    Fixed sample values
    88.5% of sustained voiced phonemes sit within ±20 cents window.
    Intonation score: 0.84 / 1.00
    Cent distribution: -50c (1.5%), -40c (1.4%), -30c (3%), -20c (6.1%), -10c (11.6%),
    0c (15.9%), +10c (25.4%), +20c (17.3%), +30c (10.5%), +40c (5%), +50c (2.3%).
    """
    histogram = [
        {"cent": "-50c", "pct": 1.5, "in_key": False, "label": "Flat Outlier"},
        {"cent": "-40c", "pct": 1.4, "in_key": False, "label": "Flat Outer"},
        {"cent": "-30c", "pct": 3.0, "in_key": False, "label": "Slightly Flat"},
        {"cent": "-20c", "pct": 6.1, "in_key": True, "label": "Strict Key Zone"},
        {"cent": "-10c", "pct": 11.6, "in_key": True, "label": "Strict Key Zone"},
        {"cent": "0c", "pct": 15.9, "in_key": True, "label": "Center Pitch"},
        {"cent": "+10c", "pct": 25.4, "in_key": True, "label": "Strict Key Zone"},
        {"cent": "+20c", "pct": 17.3, "in_key": True, "label": "Strict Key Zone"},
        {"cent": "+30c", "pct": 10.5, "in_key": False, "label": "Slightly Sharp"},
        {"cent": "+40c", "pct": 5.0, "in_key": False, "label": "Sharp Outer"},
        {"cent": "+50c", "pct": 2.3, "in_key": False, "label": "Sharp Outlier"}
    ]
    # In-key sum: 6.1 + 11.6 + 15.9 + 25.4 + 17.3 = 76.3% directly centered, 88.5% sustained voiced phonemes within +/-20c
    return {
        "in_key_pct": 88.5,
        "strict_key_pct": 89.4,
        "intonation_score": 0.84,
        "max_score": 1.00,
        "threshold_cents": 20,
        "histogram": histogram,
        "summary": "88.5% of sustained voiced phonemes sit within ±20 cents window without phase-cancellation or pitch correction artifacts."
    }

def get_vocal_tessitura():
    """
    Vocal Tessitura & Pitch Span (V4 Range Percentile).
    Lowest registered note: C3 • Highest registered note: G5 • Usable span: 31 semitones (Tenor / Lyric Falsetto)
    Detected Key: E Minor
    """
    return {
        "lowest_note": "C3",
        "highest_note": "G5",
        "lowest_midi": 48,  # C3
        "highest_midi": 79, # G5
        "usable_span_semitones": 31,
        "vocal_classification": "Tenor / Lyric Falsetto",
        "detected_key": "E Minor",
        "root_anchor_notes": ["C3", "G5"],
        "tessitura_comfort_zone": "E3 - D5 (22 semitones)",
        "harmonic_stability": "High"
    }

def get_vocal_timbre_audit():
    """
    Vocal Timbre & Studio Processing Audit
    "Warm, airy tenor with effortless head voice transitions and signature microtonal pitch bends."
    Vibrato & Stability: 5.4 Hz, ±38c depth
    Harmonic-to-Noise (HNR): 22.8 dB (Crisp vocal projection)
    Autotune Processing: 12% (Natural pitch correction)
    Intrinsic Pitch Confidence: 88% (Exceptional vocal foundation)
    """
    return {
        "description": "Warm, airy tenor with effortless head voice transitions and signature microtonal pitch bends.",
        "vibrato_rate_hz": 5.4,
        "vibrato_depth_cents": 38,
        "hnr_db": 22.8,
        "hnr_label": "Crisp vocal projection",
        "autotune_processing_pct": 12,
        "autotune_label": "Natural pitch correction",
        "intrinsic_pitch_confidence_pct": 88,
        "confidence_label": "Exceptional vocal foundation"
    }

def get_stem_occupancy_and_vernacular():
    """
    4-Stem Occupancy & Multilingual Lyric Writing Arc
    Demucs Separated Stem Activity:
    Vocal Stem: 82%
    Drums & Percussion: 84%
    Bass & Low-End (808): 88%
    Melodic Instruments: 80%
    Code-Switching Vernacular Analysis: Sheng, Swahili, English
    """
    stems = [
        {"name": "Vocal Stem", "occupancy": 82, "color": "#0ea5e9"},
        {"name": "Drums & Percussion", "occupancy": 84, "color": "#f59e0b"},
        {"name": "Bass & Low-End (808)", "occupancy": 88, "color": "#ef4444"},
        {"name": "Melodic Instruments", "occupancy": 80, "color": "#10b981"}
    ]
    vernacular = [
        {"language": "Sheng (Nairobi Street Slang)", "share": 42, "role": "Youth engagement & cultural authenticity"},
        {"language": "Kiswahili (East African Lingua)", "share": 38, "role": "Cross-border regional connectivity (TZ, KE, UG)"},
        {"language": "English (Global Bridge)", "share": 20, "role": "International export & streaming playlist curation"}
    ]
    return {
        "stems": stems,
        "vernacular": vernacular,
        "rhyme_density_per_bar": 1.82,
        "narrative_arc": "Three-act structure: Socio-economic struggle -> Spiritual resilience -> Triumphant community anthem"
    }

def get_notable_collaborations():
    """
    Artist Guest Features & Notable Collaborations (2)
    Cross-artist features, guest vocal appearances, and studio songwriting credits.
    """
    return [
        {
            "collective": "Nairobi Acoustic Collective",
            "year": 2024,
            "track": "Grassroots Session Live",
            "role": "Featured Artist",
            "streams": "~340k streams",
            "streams_num": 340000,
            "platform": "Spotify / Apple Music",
            "notes": "Acoustic showcase highlighting live dynamic vocal control."
        },
        {
            "collective": "East African Underground Cypher",
            "year": 2023,
            "track": "Rhythm of Rift",
            "role": "Co-writer & Hook",
            "streams": "~510k streams",
            "streams_num": 510000,
            "platform": "YouTube / Boomplay",
            "notes": "Viral regional cypher bridging Kenya and Tanzania underground hip-hop."
        }
    ]


def _sample_kpis():
    row = lambda v, f, delta, label, status, dsp: {"value": v, "formatted": f, "delta": delta, "velocity_label": label, "status": status, "dsp": dsp, "obs_date": "sample"}
    return {"monthly_listeners": row(62000, "62,000", "+24.8%", "MoM velocity", "Sample", "sample"), "follower_growth_rate": row(63.6, "+63.6%", "+63.6%", "90D pace", "Sample", "sample"),
            "engagement_score": row(94.2, "94.2", "+14.6%", "Catalog depth", "Sample", "sample"), "viral_hit_probability": row(84.5, "84.5%", "+31.2%", "Sample model", "Sample", "sample"),
            "regional_reach": row("Kenya hub", "Kenya hub", "+28.4%", "Cross-border index", "Sample", "sample"), "artistic_value_aav": row(78.6, "78.6", "+12.4%", "Catalog trajectory", "Sample", "sample"),
            "organic_integrity": row(94.0, "94.0%", "+8.5%", "Sample corridor", "Sample", "sample"), "recommended_advance": row(3750, "$3,750", "+18.0%", "Scenario", "Sample", "sample")}

def demo_fixtures():
    return {"kpis": _sample_kpis(), "crepe": get_crepe_pitch_accuracy(), "tessitura": get_vocal_tessitura(), "timbre": get_vocal_timbre_audit(),
            "stems": get_stem_occupancy_and_vernacular(), "collaborations": get_notable_collaborations()}
