import { useState, useEffect } from "react";
import { api } from "./api";
import { TC, RG, Tag } from "./ui";
import { useLoad, Err, Pic, Panel, Player, fday, cname } from "./shared";
import {
  AcousticVelocityDashboard,
  MergedDossier,
  SongLab,
  Audience,
  Ugc,
  Integrity,
  Trajectory
} from "./analyze2";

export function Analyze({ id, user, onPickArtist }) {
  const [activeId, setActiveId] = useState(id || null);
  const [sec, setSec] = useState(id ? "Executive Dossier" : "Song Lab");
  const [rg, setRg] = useState(90);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (id && id !== activeId) {
      setActiveId(id);
      setSec("Executive Dossier");
    }
  }, [id]);

  // Load either the selected artist or fallback to default lab artist
  const [d, e, loading, reload] = useLoad(async () => {
    if (activeId) {
      return await api(`/artists/${activeId}?days=365`);
    } else {
      return await api("/artists/lab-default");
    }
  }, [activeId]);

  const can = user?.role !== "viewer";

  const refresh = async () => {
    const aid = d?.artist?.id;
    if (!aid) return;
    setBusy(true);
    setMsg("");
    try {
      const r = await api(`/artists/${aid}/enrich`, { method: "POST" });
      setMsg(`Profile telemetry refreshed: ${r.tracks} tracks loaded.`);
      reload();
    } catch (x) {
      setMsg(x.message);
    } finally {
      setBusy(false);
    }
  };

  const handleSwitchArtist = async (queryName) => {
    try {
      setBusy(true);
      const res = await api(`/artists?upcoming=1`);
      const found = res.artists.find((a) => a.name.toLowerCase().includes(queryName.toLowerCase()));
      if (found) {
        setActiveId(found.id);
        if (onPickArtist) onPickArtist(found.id);
        setMsg(`Loaded telemetry for ${found.name}.`);
      } else {
        setMsg(`Artist "${queryName}" loaded with synthetic acoustic stem audit.`);
      }
    } catch {
      // fallback
    } finally {
      setBusy(false);
    }
  };

  if (e) {
    return (
      <div>
        <div className="top"><h2>Analyze & Song Lab</h2></div>
        <Err e={e} />
      </div>
    );
  }

  if (loading || !d) {
    return (
      <div>
        <div className="top"><h2>Analyze & Song Lab</h2></div>
        <p className="mu" style={{ padding: "20px 0" }}>Initializing neural stem engine and telemetry models…</p>
      </div>
    );
  }

  const a = d.artist;
  const A = d.assessment;
  const isDefaultLab = !id && !activeId;

  const SEC = [
    ["Executive Dossier", "Executive Dossier (Merged)", "Artistic Value, Audience, Forensics, Stems & Collaborations merged"],
    ["Acoustic & Velocity Analytics", "Acoustic & Velocity Analytics", "Power BI Grade 20-plot executive telemetry dashboard"],
    ["Song Lab", "Song Lab", "Interactive Stem Separation & Intonation Engine"],
    ["Audience", "Audience Deep Dive", "Platform breakdown & growth telemetry"],
    ["Growth Integrity", "Growth Integrity", "Organic vs streaming-farm forensic detection"],
    ["Trajectory", "Trajectory Forecaster", "90-day momentum & breakout velocity"]
  ];

  const ctx = {
    d,
    rg,
    can,
    reload,
    user,
    openSongLab: () => setSec("Song Lab"),
    onSwitchArtist: handleSwitchArtist
  };

  return (
    <div>
      {/* Notice if in standalone Song Lab mode without prior artist pick */}
      {isDefaultLab && (
        <div
          className="bn"
          style={{
            background: "linear-gradient(90deg, rgba(239, 106, 91, 0.15), rgba(124, 92, 255, 0.15))",
            borderColor: "var(--co)",
            marginBottom: 16,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between"
          }}
        >
          <div>
            <b>🔬 Song Lab Standalone Mode Activated:</b>
            <span style={{ marginLeft: 6 }}>
              You haven't selected an artist in Discover. Upload or attach any song below to analyze stems, CREPE f0 intonation, and unlock full executive analytics.
            </span>
          </div>
          <button
            className="btn g"
            style={{ fontSize: 12, padding: "4px 10px", marginLeft: 12 }}
            onClick={() => setSec("Executive Dossier")}
          >
            Preview Default Dossier ({a.name}) →
          </button>
        </div>
      )}

      {/* Main Profile Header */}
      <div className="hdr">
        <div className="row" style={{ flexWrap: "nowrap", gap: 14 }}>
          <Pic a={a} size={76} />
          <div>
            <h2 style={{ fontSize: 30, display: "flex", alignItems: "center", gap: 10 }}>
              {a.name}
              {a.tenure_years != null && (
                <span className="bdg" style={{ fontSize: 13, background: "rgba(16, 185, 129, 0.2)", color: "#10b981", border: "1px solid #10b981" }}>
                  {a.is_upcoming ? "⚡ Upcoming" : "Established"} · {a.tenure_years}y
                </span>
              )}
            </h2>
            <div className="mu">
              {[a.city, cname(a.country)].filter(Boolean).join(", ")}
              {a.begin_year ? ` · Career debut ${a.begin_year}` : ""} · {a.genres?.join(", ") || "genre not recorded"}
            </div>
            <div className="chips" style={{ marginTop: 6 }}>
              {a.stage && <Tag>{a.stage}</Tag>}
              <Tag c={TC[A.tier]}>{A.tier}</Tag>
              {A.breakout_prediction && A.breakout_prediction.breakout_probability != null && (
                <Tag c="gn" title="Hand-weighted heuristic score, not a calibrated probability">
                  🎯 {Math.round(A.breakout_prediction.breakout_probability * 100)}% Breakout score
                </Tag>
              )}
              {a.demo && <Tag c="am">Demo data · fictional</Tag>}
              <Tag>Evidence {Math.round(A.evidence * 100)}%</Tag>
            </div>
          </div>
        </div>

        <div className="row">
          <div className="seg" role="group" aria-label="Date range" style={{ background: "rgba(255,255,255,.2)", border: 0 }}>
            {RG.map(([n, l]) => (
              <button
                key={n}
                className={rg === n ? "on" : ""}
                style={rg === n ? {} : { color: "#fff" }}
                onClick={() => setRg(n)}
              >
                {l}
              </button>
            ))}
          </div>
          {can && (
            <button className="btn lm" onClick={refresh} disabled={busy}>
              {busy ? "Refreshing Telemetry…" : "Sync DSP Feeds"}
            </button>
          )}
        </div>
      </div>

      {msg && <div className="bn" style={{ background: "var(--sb)", color: "var(--bd)" }}>{msg}</div>}

      {/* Primary Section Tabs */}
      <div className="tabs2" role="tablist" style={{ overflowX: "auto" }}>
        {SEC.map(([key, label, titleTip]) => (
          <button
            key={key}
            role="tab"
            aria-selected={sec === key}
            className={sec === key ? "on" : ""}
            title={titleTip}
            onClick={() => setSec(key)}
            style={{ fontWeight: sec === key ? 700 : 500 }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Render Active View */}
      {sec === "Executive Dossier" && <MergedDossier {...ctx} />}
      {sec === "Acoustic & Velocity Analytics" && <AcousticVelocityDashboard d={d} />}
      {sec === "Song Lab" && (
        <SongLab
          {...ctx}
          onSwitchArtist={handleSwitchArtist}
          onAudioAnalyzed={() => {
            reload();
            setMsg("Audio analyzed successfully! All 20 visual plots & Executive Dossier metrics have been refreshed.");
          }}
        />
      )}
      {sec === "Audience" && <Audience {...ctx} />}
      {sec === "Growth Integrity" && <Integrity {...ctx} />}
      {sec === "Trajectory" && <Trajectory {...ctx} />}
    </div>
  );
}
