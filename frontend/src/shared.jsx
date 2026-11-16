import { useState, useEffect, useCallback, useRef } from "react";
import { Tag, hue } from "./ui";
import { Spark } from "./ui";

export const ML = { lastfm_listeners: "Last.fm listeners", deezer_fans: "Deezer fans", audius_followers: "Audius followers", spotify_followers: "Spotify followers", yt_subscribers: "YouTube subscribers", monthly_listeners: "Monthly listeners", streams: "Streams", ugc_videos: "UGC videos", ugc_creators: "UGC creators", ugc_top3_share: "Top-3 creator share (%)", ugc_countries: "UGC countries" };
export const AUDM = ["monthly_listeners", "lastfm_listeners", "spotify_followers", "deezer_fans", "audius_followers", "yt_subscribers"];
export const IMPORT = [...AUDM, "streams", "ugc_videos", "ugc_creators", "ugc_top3_share", "ugc_countries"];
export const fd = (t) => (t ? new Date(t * 1000).toLocaleString() : "-");
export const fday = (t) => (t ? new Date(t * 1000).toLocaleDateString(undefined, { day: "numeric", month: "short" }) : "-");
export const safe = (u) => (typeof u === "string" && u.startsWith("https://") ? u : null);
export const mmss = (s) => (Number.isFinite(s) ? `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}` : "0:00");
export const provOf = (src = "") => (src.startsWith("manual:") ? ["Manual import", "am"] : src.startsWith("csv:") ? ["CSV import", "am"] : src === "demo" ? ["Demo data", "rd"] : ["Provider API", "gn"]);
export const Err = ({ e }) => (e ? <div className="bn" role="alert" style={{ background: "#fdecec", color: "#b42318" }}>{e}</div> : null);
export const Panel = ({ title, sub, right, children, style }) => <div className="pn" style={style}><div className="row sp"><h3 className="t">{title}</h3>{right}</div>{sub && <div className="sub2">{sub}</div>}{children}</div>;

export function useLoad(fn, deps) {
  const [s, set] = useState({ d: null, e: "", l: true });
  const load = useCallback(() => { set((x) => ({ ...x, l: true })); return fn().then((d) => set({ d, e: "", l: false })).catch((e) => set({ d: null, e: e.message, l: false })); }, deps); // eslint-disable-line
  useEffect(() => { load(); }, [load]);
  return [s.d, s.e, s.l, load];
}
export function useDebounced(v, ms = 300) { const [x, setX] = useState(v); useEffect(() => { const t = setTimeout(() => setX(v), ms); return () => clearTimeout(t); }, [v, ms]); return x; }

export function Kpi({ label, value, note, color = "var(--b)", spark, up }) {
  return <div className="kpi" style={{ "--kc": color }}><div className="sm mu">{label}</div><div className="big">{value}</div><div className={"sm " + (up === true ? "up" : up === false ? "dw" : "mu")}>{note}</div>{spark && spark.length > 1 ? <Spark d={spark} /> : null}</div>;
}

export function Pic({ a, size = 56, round = true }) {
  const u = safe(a.image_url); const g = `linear-gradient(135deg,hsl(${hue(a.name)} 70% 45%),hsl(${(hue(a.name) + 50) % 360} 75% 55%))`;
  return <div style={{ width: size, height: size, borderRadius: round ? "50%" : 16, background: g, display: "grid", placeItems: "center", color: "#fff", fontWeight: 800, overflow: "hidden", flex: "none", fontSize: size / 3 }}>
    {u ? <img src={u} alt="" referrerPolicy="no-referrer" style={{ width: "100%", height: "100%", objectFit: "cover" }} onError={(e) => { e.currentTarget.style.display = "none"; }} /> : null}{!u && a.name.split(" ").map((w) => w[0]).join("").slice(0, 2)}</div>;
}

// single shared preview channel for cards and lists
let _audio = null; const subs = new Set(); const emit = (u) => subs.forEach((f) => f(u));
export function usePreview() {
  const [url, setUrl] = useState(null);
  useEffect(() => { subs.add(setUrl); return () => subs.delete(setUrl); }, []);
  const toggle = (u) => {
    if (!safe(u)) return;
    if (!_audio) { _audio = new Audio(); _audio.addEventListener("ended", () => emit(null)); _audio.addEventListener("pause", () => emit(null)); }
    if (_audio.src === u && !_audio.paused) { _audio.pause(); return; }
    _audio.src = u; _audio.play().then(() => emit(u)).catch(() => emit(null));
  };
  return [url, toggle];
}

export function Player({ tracks }) {
  const ref = useRef(null); const [cur, setCur] = useState(-1); const [pl, setPl] = useState(false); const [t, setT] = useState(0); const [dur, setDur] = useState(0);
  useEffect(() => () => { if (ref.current) ref.current.pause(); }, []);
  const play = (i) => { const a = ref.current, tr = tracks[i]; if (!a || !tr || !safe(tr.preview_url)) return; if (cur === i) { pl ? a.pause() : a.play().catch(() => {}); return; } setCur(i); a.src = tr.preview_url; a.play().catch(() => setPl(false)); };
  const next = () => { const n = tracks.findIndex((x, i) => i > cur && safe(x.preview_url)); if (n >= 0) play(n); else { setCur(-1); setPl(false); } };
  if (!tracks.length) return <div className="empty">No songs found yet. Use “Refresh profile and songs”, or add a link in Song Lab.</div>;
  return (<div><audio ref={ref} preload="none" onPlay={() => setPl(true)} onPause={() => setPl(false)} onTimeUpdate={(e) => setT(e.target.currentTime)} onLoadedMetadata={(e) => setDur(e.target.duration)} onEnded={next} />
    {tracks.map((tr, i) => <div key={tr.id || i} className={"pl " + (cur === i ? "on" : "")}>
      {safe(tr.cover_url) ? <img src={tr.cover_url} alt="" referrerPolicy="no-referrer" onError={(e) => { e.currentTarget.style.visibility = "hidden"; }} /> : <div className="cvr" />}
      <div style={{ minWidth: 0, flex: 1 }}><div style={{ fontWeight: 700, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{tr.title}</div><div className="sm mu">{[tr.album, tr.source, tr.duration ? mmss(tr.duration) : null].filter(Boolean).join(" · ")}</div></div>
      {safe(tr.url) && <a className="sm" href={tr.url} target="_blank" rel="noopener noreferrer">Open</a>}
      <button className="pbtn" disabled={!safe(tr.preview_url)} onClick={() => play(i)} title={safe(tr.preview_url) ? "Play preview" : "No preview available for this song"} aria-label={(cur === i && pl ? "Pause " : "Play ") + tr.title}>{cur === i && pl ? "❚❚" : "▶"}</button></div>)}
    {cur >= 0 && <div className="now"><span className="sm">{tracks[cur].title}</span><input type="range" min="0" max={dur || 30} step="0.1" value={t} aria-label="Seek" onChange={(e) => { ref.current.currentTime = +e.target.value; }} /><span className="sm">{mmss(t)} / {mmss(dur)}</span></div>}
    <p className="sm mu" style={{ marginTop: 6 }}>Previews are short samples from the listed source; some platforms provide full streams (Audius).</p></div>);
}

export function downloadCsv(name, rows) {
  if (!rows.length) return; const cols = Object.keys(rows[0]); const q = (v) => { const s = String(v ?? ""); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
  const blob = new Blob([[cols.join(","), ...rows.map((r) => cols.map((c) => q(r[c])).join(","))].join("\n")], { type: "text/csv" }); const u = URL.createObjectURL(blob);
  const a = document.createElement("a"); a.href = u; a.download = name; a.click(); URL.revokeObjectURL(u);
}
export const avgOf = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : null);
export { Tag };

export const sliceDays = (arr = [], days) => { const cut = Date.now() / 1000 - days * 86400; return arr.filter((x) => x[0] >= cut); };
export const changeOver = (arr = [], days) => { if (arr.length < 2) return null; const last = arr[arr.length - 1], cut = last[0] - days * 86400; const base = [...arr].reverse().find((x) => x[0] <= cut); return base && base[1] > 0 ? last[1] / base[1] - 1 : null; };
export const steps = (arr = []) => arr.slice(1).map((x, i) => ({ ts: x[0], v: arr[i][1] > 0 ? x[1] / arr[i][1] - 1 : null }));
export const vals = (arr = []) => arr.map((x) => x[1]);
export const lbls = (arr = []) => arr.map((x) => fday(x[0]));
export const CN = {}; export const setNames = (meta) => Object.values(meta.regions).flat().forEach((c) => { CN[c.code] = c.name; }); export const cname = (c) => CN[c] || c;
