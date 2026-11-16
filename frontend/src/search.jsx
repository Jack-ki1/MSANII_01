import { useState, useEffect, useRef } from "react";
import { api } from "./api";
import { Pic, useDebounced, cname } from "./shared";

// Ctrl/Cmd+K command palette: find any artist by name
export function Search({ onPick, onClose }) {
  const [q, setQ] = useState(""); const [r, setR] = useState([]); const [i, setI] = useState(0); const dq = useDebounced(q, 200); const ref = useRef(null);
  useEffect(() => { ref.current && ref.current.focus(); }, []);
  useEffect(() => { let on = true; api("/artists?limit=8&q=" + encodeURIComponent(dq)).then((j) => { if (on) { setR(j.artists); setI(0); } }).catch(() => {}); return () => { on = false; }; }, [dq]);
  const key = (e) => { if (e.key === "Escape") onClose(); else if (e.key === "ArrowDown") setI((x) => Math.min(x + 1, r.length - 1)); else if (e.key === "ArrowUp") setI((x) => Math.max(x - 1, 0)); else if (e.key === "Enter" && r[i]) onPick(r[i].id); };
  return (<div className="ov" onClick={onClose} role="dialog" aria-modal="true" aria-label="Search artists"><div className="md" onClick={(e) => e.stopPropagation()}>
    <input ref={ref} className="inp" placeholder="Search artists by name…" aria-label="Search artists" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={key} />
    <div style={{ marginTop: 8 }}>{r.map((a, k) => <button key={a.id} className={"sr " + (k === i ? "on" : "")} onClick={() => onPick(a.id)}><Pic a={a} size={36} /><div><b>{a.name}</b><div className="sm mu">{[a.city, cname(a.country)].filter(Boolean).join(", ")} · {a.genres.slice(0, 2).join(", ")}</div></div></button>)}{!r.length && <p className="sm mu" style={{ padding: 10 }}>No artists found.</p>}</div>
    <p className="sm mu" style={{ margin: "8px 4px 0" }}>↑ ↓ to move, Enter to open, Esc to close</p></div></div>);
}
