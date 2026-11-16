"""Song Lab: measurements for uploaded audio/video and metadata for links. Pure-stdlib for 16-bit WAV; ffmpeg (if installed) converts everything else.
Every value carries its method and a confidence. Tempo is an envelope-autocorrelation ESTIMATE and is labelled low confidence. Loudness is an RMS proxy, not LUFS."""
import os, sys, json, math, wave, array, shutil, tempfile, subprocess, requests
from urllib.parse import urlparse, parse_qs, quote

MIME = {"wav": "audio/wav", "mp3": "audio/mpeg", "flac": "audio/flac", "ogg": "audio/ogg", "mp4": "video/mp4", "webm": "video/webm"}

def sniff(h):
    if h[:4] == b"RIFF" and h[8:12] == b"WAVE": return "audio", "wav"
    if h[:4] == b"fLaC": return "audio", "flac"
    if h[:4] == b"OggS": return "audio", "ogg"
    if h[:3] == b"ID3" or (len(h) > 1 and h[0] == 0xFF and h[1] & 0xE0 == 0xE0): return "audio", "mp3"
    if h[4:8] == b"ftyp": return "video", "mp4"
    if h[:4] == b"\x1a\x45\xdf\xa3": return "video", "webm"
    return None

def probe(path):
    if not shutil.which("ffprobe"): return {}
    try:
        o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate,channels,codec_name,bits_per_sample:format=duration", "-of", "json", path], capture_output=True, timeout=30, check=True).stdout
        j = json.loads(o); s = (j.get("streams") or [{}])[0]
        return {"sample_rate": int(s.get("sample_rate") or 0) or None, "channels": s.get("channels"), "codec": s.get("codec_name"), "bits": int(s.get("bits_per_sample") or 0) or None, "duration": float((j.get("format") or {}).get("duration") or 0) or None}
    except Exception: return {}

def to_wav(path, out_dir):
    out = os.path.join(out_dir, "a.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "22050", "-acodec", "pcm_s16le", "-t", "240", out], capture_output=True, timeout=180, check=True)
    return out

def wav_stats(path, max_s=240):
    with wave.open(path, "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        if sw != 2: raise ValueError("only 16-bit PCM WAV can be read without ffmpeg")
        total = min(n, sr * max_s); hop = max(sr // 50, 1); read = 0; peak = 0; clip = 0; ss_all = 0.0; cnt_all = 0; env = []; sec_ss = 0.0; sec_cnt = 0; per_sec = []
        while read < total:
            fr = w.readframes(min(hop, total - read))
            if not fr: break
            a = array.array("h"); a.frombytes(fr[: len(fr) // 2 * 2])
            if sys.byteorder == "big": a.byteswap()
            if ch > 1: a = a[::ch]
            if not a: break
            read += len(a); ss = sum(x * x for x in a); m = max(max(a), -min(a))
            if m > peak: peak = m
            if m >= 32766: clip += sum(1 for x in a if x >= 32766 or x <= -32767)
            ss_all += ss; cnt_all += len(a); sec_ss += ss; sec_cnt += len(a); env.append(20 * math.log10(max(math.sqrt(ss / len(a)), 1) / 32768))
            if len(env) % 50 == 0: per_sec.append(20 * math.log10(max(math.sqrt(sec_ss / sec_cnt), 1) / 32768)); sec_ss = 0.0; sec_cnt = 0
    if cnt_all == 0: raise ValueError("no audio frames")
    rms = 20 * math.log10(max(math.sqrt(ss_all / cnt_all), 1) / 32768); pk = 20 * math.log10(max(peak, 1) / 32768)
    live = sorted(x for x in per_sec if x > -70); dr = (live[int(len(live) * .95) - 1] - live[int(len(live) * .10)]) if len(live) >= 10 else None
    o = [max(0.0, env[i] - env[i - 1]) for i in range(1, len(env))]; mu = sum(o) / len(o) if o else 0; o = [x - mu for x in o]; ac0 = sum(x * x for x in o); best = (0, 0)
    if len(o) > 400 and ac0 > 0:
        for lag in range(15, 51):
            v = sum(o[i] * o[i + lag] for i in range(len(o) - lag))
            if v > best[0]: best = (v, lag)
    tempo = (round(60 * 50 / best[1], 1), round(min(0.5, max(0.0, best[0] / ac0)), 2)) if best[1] else None
    return {"sr": sr, "ch": ch, "bits": sw * 8, "duration": round(n / sr, 1), "analysed_s": round(read / sr, 1), "rms": round(rms, 1), "peak": round(pk, 1), "crest": round(pk - rms, 1), "clip_pct": round(100 * clip / cnt_all, 4),
            "silence_pct": round(100 * sum(1 for x in per_sec if x < -60) / max(len(per_sec), 1), 1), "dyn_range": round(dr, 1) if dr is not None else None, "tempo": tempo, "envelope": [round(x, 1) for x in per_sec[:240]]}

def analyze_file(path, kind, ext):
    info = probe(path) if ext != "wav" or kind == "video" else {}; tmp = None; wav = path; notes = []
    try:
        if ext != "wav" or kind == "video":
            if not shutil.which("ffmpeg"): return {"status": "stored", "reason": "ffmpeg is not installed on the server, so only 16-bit PCM WAV audio can be analysed. Install ffmpeg (the Docker image includes it)."}
            tmp = tempfile.mkdtemp(); wav = to_wav(path, tmp); notes.append("converted to 22.05 kHz mono 16-bit for analysis (first 240 s)")
        try: st = wav_stats(wav)
        except (ValueError, wave.Error, EOFError):
            if ext == "wav" and shutil.which("ffmpeg") and tmp is None:
                tmp = tempfile.mkdtemp(); wav = to_wav(path, tmp); notes.append("WAV re-encoded to 16-bit for analysis"); st = wav_stats(wav)
            else: raise
    except (ValueError, wave.Error, EOFError, subprocess.SubprocessError, OSError) as e:
        return {"status": "failed", "reason": f"could not decode this file ({type(e).__name__})."}
    finally:
        if tmp: shutil.rmtree(tmp, ignore_errors=True)
    orig_sr = info.get("sample_rate") or (st["sr"] if ext == "wav" and kind == "audio" else None); orig_bits = info.get("bits") or (st["bits"] if ext == "wav" and kind == "audio" else None)
    M = lambda n, v, u, c, m, note="": {"name": n, "value": v, "unit": u, "confidence": c, "method": m, "note": note}
    ms = [M("duration", st["duration"], "s", 1.0, "container header"), M("rms_level", st["rms"], "dBFS", 0.9, "RMS over the analysed audio", "RMS proxy, not LUFS"), M("sample_peak", st["peak"], "dBFS", 0.95, "max absolute sample", "sample peak; true-peak needs oversampling"),
          M("crest_factor", st["crest"], "dB", 0.9, "peak minus RMS"), M("clipping", st["clip_pct"], "% samples", 0.95, "samples at digital full scale"), M("silence", st["silence_pct"], "% seconds", 0.9, "seconds below -60 dBFS")]
    if st["dyn_range"] is not None: ms.append(M("dynamic_range", st["dyn_range"], "dB", 0.6, "p95 minus p10 of per-second RMS", "loudness-range style proxy"))
    if st["tempo"]: ms.append(M("tempo_bpm_envelope", st["tempo"][0], "BPM", st["tempo"][1], "energy-envelope autocorrelation", "estimate; half/double-time errors are common"))
    comp = []
    if orig_sr: comp.append({"check": "Sample rate at least 44.1 kHz", "pass": orig_sr >= 44100, "detail": f"{orig_sr} Hz"})
    if orig_bits: comp.append({"check": "Bit depth at least 16", "pass": orig_bits >= 16, "detail": f"{orig_bits}-bit"})
    comp.append({"check": "Sample peak at or below -1.0 dBFS", "pass": st["peak"] <= -1.0, "detail": f"{st['peak']} dBFS (true-peak not measured)"})
    comp.append({"check": "No digital clipping", "pass": st["clip_pct"] < 0.01, "detail": f"{st['clip_pct']}% of samples at full scale"})
    ins = []
    if st["duration"] < 20: ins.append("Under 20 seconds: structure and energy conclusions are unreliable.")
    ins.append(f"RMS level {st['rms']} dBFS with {st['crest']} dB crest factor" + (" (very compressed)" if st["crest"] < 8 else " (dynamic)" if st["crest"] > 16 else "") + ". This is an RMS proxy, not integrated loudness (LUFS).")
    if st["clip_pct"] >= 0.01: ins.append("Clipping detected: the master may be over-limited or distorted.")
    if st["silence_pct"] > 15: ins.append(f"{st['silence_pct']}% of seconds are near-silent; check for long gaps or a quiet intro/outro.")
    if st["tempo"]: ins.append(f"Estimated tempo about {st['tempo'][0]} BPM (confidence {st['tempo'][1]:.0%}); verify by ear, half or double time is common.")
    if kind == "video": ins.append("Audio was extracted from the video track; visual content is not analysed.")
    return {"status": "done", "measurements": ms, "envelope": st["envelope"], "compliance": comp, "insights": ins, "technical": {k: st[k] for k in ("sr", "ch", "bits", "duration", "analysed_s")}, "notes": notes}

# ---------------- links: fixed endpoints only (no fetching of arbitrary user URLs) ----------------
HOSTS = {"youtube.com": "youtube", "www.youtube.com": "youtube", "m.youtube.com": "youtube", "youtu.be": "youtube", "open.spotify.com": "spotify", "soundcloud.com": "soundcloud", "audius.co": "audius", "www.tiktok.com": "tiktok", "tiktok.com": "tiktok"}

def classify_link(url):
    u = urlparse(url)
    if u.scheme != "https" or u.hostname not in HOSTS or len(url) > 400: return None
    return HOSTS[u.hostname], u

def _j(url, **kw):
    r = requests.get(url, headers={"User-Agent": "MSANII/0.4"}, timeout=12, **kw)
    if r.status_code >= 400: raise ValueError(f"HTTP {r.status_code}")
    return r.json()

def analyze_link(url, yt_key=None):
    c = classify_link(url)
    if not c: return {"status": "failed", "reason": "Unsupported link. Use https links from YouTube, Spotify, SoundCloud, Audius or TikTok."}
    plat, u = c; out = {"platform": plat, "stats": {}}
    try:
        if plat == "youtube":
            vid = u.path.lstrip("/") if u.hostname == "youtu.be" else (parse_qs(u.query).get("v", [""])[0] or u.path.rstrip("/").split("/")[-1])
            if not vid.replace("-", "").replace("_", "").isalnum() or len(vid) > 20: raise ValueError("could not read the video id")
            o = _j("https://www.youtube.com/oembed", params={"url": "https://www.youtube.com/watch?v=" + vid, "format": "json"})
            out.update(title=o.get("title"), author=o.get("author_name"), thumbnail=o.get("thumbnail_url"), embed="https://www.youtube-nocookie.com/embed/" + vid)
            if yt_key:
                v = (_j("https://www.googleapis.com/youtube/v3/videos", params={"part": "snippet,statistics,contentDetails", "id": vid, "key": yt_key}).get("items") or [{}])[0]
                st = v.get("statistics") or {}; out["stats"] = {k: int(st[k]) for k in ("viewCount", "likeCount", "commentCount") if k in st}; out["published"] = (v.get("snippet") or {}).get("publishedAt"); out["duration_iso"] = (v.get("contentDetails") or {}).get("duration")
        elif plat == "spotify":
            parts = [p for p in u.path.split("/") if p]; kind_, sid = (parts[-2], parts[-1]) if len(parts) >= 2 else ("", "")
            if kind_ not in ("track", "album", "artist", "playlist") or not sid.isalnum(): raise ValueError("not a Spotify track, album, artist or playlist link")
            o = _j("https://open.spotify.com/oembed", params={"url": f"https://open.spotify.com/{kind_}/{sid}"}); out.update(title=o.get("title"), thumbnail=o.get("thumbnail_url"), embed=f"https://open.spotify.com/embed/{kind_}/{sid}")
        elif plat == "soundcloud":
            o = _j("https://soundcloud.com/oembed", params={"format": "json", "url": url}); out.update(title=o.get("title"), author=o.get("author_name"), thumbnail=o.get("thumbnail_url"))
        elif plat == "audius":
            d = (_j("https://api.audius.co/v1/resolve", params={"url": url, "app_name": "MSANII"}).get("data") or {})
            out.update(title=d.get("title") or d.get("name"), author=(d.get("user") or {}).get("name"), thumbnail=(d.get("artwork") or {}).get("480x480"), genre=d.get("genre"), mood=d.get("mood"), duration_s=d.get("duration"))
            out["stats"] = {k: d[k] for k in ("play_count", "favorite_count", "repost_count", "follower_count") if isinstance(d.get(k), int)}
        elif plat == "tiktok":
            o = _j("https://www.tiktok.com/oembed", params={"url": url}); out.update(title=o.get("title"), author=o.get("author_name"), thumbnail=o.get("thumbnail_url"))
    except (ValueError, requests.RequestException) as e:
        return {"status": "failed", "reason": f"could not read link metadata ({type(e).__name__}: {e})"[:200]}
    ins = [f"Public metadata read from {plat}. Engagement numbers appear only where the platform provides them" + ("." if out["stats"] else (" (add a YouTube API key in Settings to include view, like and comment counts)." if plat == "youtube" else "; this platform exposes none for this link."))]
    return {"status": "done", "meta": out, "insights": ins, "measurements": []}
