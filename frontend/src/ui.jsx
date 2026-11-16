export const mk = (b, g, v, s) => { let x = s; const o = []; for (let i = 0; i < 365; i++) { x = (x * 9301 + 49297) % 233280; o.push(Math.round(b * Math.pow(1 + g, i / 30) * (1 + (x / 233280 - 0.5) * v))); } return o; };
export const avg = (a) => a.reduce((x, y) => x + y, 0) / a.length;
export const K = (n) => (n >= 1e5 ? Math.round(n / 1e3) + "K" : n >= 1e3 ? (n / 1e3).toFixed(1) + "K" : String(n));
export const P = (g) => (g >= 0 ? "+" : "") + Math.round(g * 100) + "%";
export const PIL = { v: ["Vocal ability", "Pitch accuracy, stability, tone, range, expression, dynamics, timing, phrasing, identity, authenticity, processing"], w: ["Songwriting", "Lyric coherence, storytelling, originality, imagery, hook, rhyme, language, emotion, cultural relevance"], s: ["Song as a whole", "Structure, energy progression, cohesion, arrangement, production quality, song identity"], c: ["Composition & arrangement", "Melody, harmony, key, chords, rhythm, groove, syncopation, instrumentation, genre mastery"] };
export const CRIT = ["Songwriting", "Vocal identity", "Originality", "Melody", "Musicality", "Artistic direction", "Performance ability", "Emotional connection", "Production", "Cultural relevance", "Long-term potential"];
export const CTRY = { KE: "Kenya", TZ: "Tanzania", UG: "Uganda", RW: "Rwanda", ET: "Ethiopia", NG: "Nigeria", GH: "Ghana", ZA: "South Africa" };
export const ACTS = ["Pursue", "Contact", "Request demo", "Schedule meeting", "Add to shortlist", "Monitor", "Reject", "Defer pending evidence"];
export const NEXT = { PURSUE: "Contact the artist and request a demo or meeting.", MEET: "Schedule an introductory meeting and request unreleased material.", WATCH: "Keep monitoring; re-review at the next weekly cycle.", "MORE EVIDENCE": "Obtain licensed audio and a human review before any decision." };
export const TC = { PURSUE: "gn", MEET: "bl", WATCH: "am", "MORE EVIDENCE": "" };
export const TCOL = { PURSUE: "#1f9d73", MEET: "#087fe5", WATCH: "#e39a21", "MORE EVIDENCE": "#8d98a6" };
export const RG = [[7, "7d"], [30, "30d"], [90, "90d"], [180, "180d"], [365, "12m"]];

export const conf = (e) => (e >= 0.7 ? ["High confidence", "gn"] : e >= 0.5 ? ["Medium confidence", "am"] : ["Low confidence", "rd"]);
export const hue = (s) => [...s].reduce((x, c) => x + c.charCodeAt(0), 0) % 360;
export const Av = ({ n, s = 44 }) => <div className="av" style={{ width: s, height: s, background: `linear-gradient(135deg,hsl(${hue(n)} 70% 45%),hsl(${(hue(n) + 40) % 360} 75% 55%))` }}>{n.split(" ").map((w) => w[0]).join("").slice(0, 2)}</div>;
export const Tag = ({ c, children }) => <span className={"tag " + (c || "")}>{children}</span>;
export const Logo = ({ light }) => <span className="lg" style={{ color: light ? "#fff" : "var(--b)" }}><svg width="30" height="24" viewBox="0 0 32 24" fill="currentColor" aria-hidden="true"><path d="M1 23L12 1l5 10-5 12z" /><path d="M15 23l7-14 9 14z" opacity=".75" /></svg>MSANII</span>;
export const pts = (d, w, h, p = 4) => { const mx = Math.max(...d), mn = Math.min(...d); return d.map((v, i) => `${(i / (d.length - 1)) * w},${h - p - ((v - mn) / (mx - mn || 1)) * (h - 2 * p)}`).join(" "); };
export const Spark = ({ d }) => (d.length < 2 ? <div className="sp2" /> : <svg viewBox="0 0 100 32" preserveAspectRatio="none" className="sp2" aria-hidden="true"><polyline points={pts(d, 100, 32)} fill="none" stroke="#27b9f5" strokeWidth="2" vectorEffect="non-scaling-stroke" /></svg>);
export const Area = ({ d }) => {
  if (d.length < 2) return <p className="mu sm">Not enough points for this range.</p>;
  const p = pts(d, 600, 170, 10);
  return <svg viewBox="0 0 600 170" preserveAspectRatio="none" className="ch" role="img" aria-label="Monthly listeners over time"><defs><linearGradient id="ag" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#087fe5" stopOpacity=".28" /><stop offset="1" stopColor="#087fe5" stopOpacity="0" /></linearGradient></defs><polygon points={`0,170 ${p} 600,170`} fill="url(#ag)" /><polyline points={p} fill="none" stroke="#087fe5" strokeWidth="2.5" vectorEffect="non-scaling-stroke" /></svg>;
};
export const DEMO = mk(18000, 0.09, 0.1, 7).slice(-60);

