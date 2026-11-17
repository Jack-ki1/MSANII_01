import { useState } from "react";
import { api } from "./api";
import { PIL, Tag } from "./ui";
import { useLoad, Err, Kpi, Panel, fd, fday, safe } from "./shared";
import { Donut, Gauge, HBars, PAL, fmt } from "./charts";

const SEARCH_P = ["MusicBrainz", "Apple Music / iTunes", "Deezer", "Last.fm", "Spotify", "Discogs"];
const SIGNAL_P = ["Deezer", "Audius", "Last.fm", "YouTube Data API", "Spotify", "TikTok API", "Soundcharts"];
const PROFILE_P = ["Wikipedia", "MusicBrainz", "Deezer", "Apple Music / iTunes", "Audius", "Genius"];

const STC = {
  "Fully implemented": "gn",
  "Implemented with credentials": "bl",
  "Partially implemented": "am",
  "Requires licensed access": "rd",
  "Manual import": "",
  Planned: ""
};

const PRESETS = {
  Balanced: [25, 25, 25, 25],
  "Vocalist focus": [40, 20, 20, 20],
  "Songwriting focus": [20, 40, 20, 20],
  "Production-led": [20, 20, 40, 20],
  "Composition-led": [20, 20, 20, 40]
};

function Group({ group, init, spec, reload, onSaved, note }) {
  const [v, setV] = useState(init);
  const [m, setM] = useState("");

  const save = async () => {
    try {
      const body = {};
      spec.forEach(([k, t]) => {
        body[k] =
          t === "n" || t === "a"
            ? Number(v[k])
            : t === "l"
            ? Array.isArray(v[k])
              ? v[k]
              : String(v[k]).split(",").map((x) => x.trim()).filter(Boolean)
            : v[k];
      });
      await api("/settings/" + group, { method: "PUT", body });
      setM("Settings saved successfully.");
      reload();
      onSaved && onSaved();
    } catch (x) {
      setM(x.message);
    }
  };

  return (
    <div className="pn">
      <div className="g2">
        {spec.map(([k, t, label, opts]) => {
          const o = typeof opts === "function" ? opts(v) : opts;
          return (
            <div key={k} style={t === "c" ? { gridColumn: "1/-1" } : {}}>
              <label className="sm mu">{label}</label>
              {t === "b" ? (
                <div>
                  <input
                    type="checkbox"
                    checked={!!v[k]}
                    onChange={(e) => setV({ ...v, [k]: e.target.checked })}
                  />
                </div>
              ) : t === "c" ? (
                <div className="chips">
                  {o.map((x) => (
                    <button
                      key={x.v}
                      type="button"
                      className={"chip " + (v[k].includes(x.v) ? "on" : "")}
                      aria-pressed={v[k].includes(x.v)}
                      onClick={() =>
                        setV({
                          ...v,
                          [k]: v[k].includes(x.v)
                            ? v[k].filter((y) => y !== x.v)
                            : [...v[k], x.v]
                        })
                      }
                    >
                      {x.l}
                    </button>
                  ))}
                </div>
              ) : t === "a" || t === "r" ? (
                <select
                  className="inp"
                  value={v[k]}
                  onChange={(e) =>
                    setV({
                      ...v,
                      [k]: t === "a" ? Number(e.target.value) : e.target.value,
                      ...(k === "region" ? { default_country: "" } : {})
                    })
                  }
                >
                  {o.map((x) => (
                    <option key={x.v} value={x.v}>
                      {x.l}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  className="inp"
                  value={Array.isArray(v[k]) ? v[k].join(", ") : v[k]}
                  onChange={(e) => setV({ ...v, [k]: e.target.value })}
                />
              )}
            </div>
          );
        })}
      </div>
      {note && <p className="sm mu" style={{ marginTop: 8 }}>{note}</p>}
      <div className="row" style={{ marginTop: 12 }}>
        <button className="btn" onClick={save}>Save Changes</button>
        <span className="sm mu" style={{ marginLeft: 8 }}>{m}</span>
      </div>
    </div>
  );
}

// ---------------- 1. DATA PROVIDERS (76+ Providers with Tuning) ----------------
function Providers() {
  const [p, e, , reload] = useLoad(() => api("/providers"), []);
  const [vals, setVals] = useState({});
  const [msg, setMsg] = useState({});
  const [cat, setCat] = useState("All");
  const [st, setSt] = useState("All");
  const [q, setQ] = useState("");
  const [tuningPrio, setTuningPrio] = useState({});
  const [tuningRpm, setTuningRpm] = useState({});

  const say = (n, t) => setMsg((x) => ({ ...x, [n]: t }));
  const P = p ? p.providers : [];

  const call = (n, path, opt, ok) =>
    api(`/providers/${encodeURIComponent(n)}/${path}`, opt)
      .then((r) => say(n, ok(r)))
      .catch((x) => say(n, x.message));

  const saveTuning = async (name) => {
    try {
      const prio = tuningPrio[name] ?? 5;
      const rpm = tuningRpm[name] ?? 60;
      await api(`/providers/${encodeURIComponent(name)}/tuning`, {
        method: "PUT",
        body: { priority: prio, rate_limit_rpm: rpm, enabled: true }
      });
      say(name, "Tuning parameters applied.");
      reload();
    } catch (err) {
      say(name, err.message);
    }
  };

  const cats = ["All", ...[...new Set(P.map((x) => x.category))].sort()];
  const sts = ["All", ...Object.keys(STC)];
  const L = P.filter(
    (x) =>
      (cat === "All" || x.category === cat) &&
      (st === "All" || x.status === st) &&
      (x.name.toLowerCase().includes(q.toLowerCase()) || x.category.toLowerCase().includes(q.toLowerCase()))
  );

  const byS = Object.keys(STC).map((s) => ({
    label: s,
    value: P.filter((x) => x.status === s).length,
    color:
      {
        "Fully implemented": "#10b981",
        "Implemented with credentials": PAL[0],
        "Partially implemented": PAL[3],
        "Requires licensed access": "#ef6a5b",
        "Manual import": PAL[1],
        Planned: "#8d98a6"
      }[s] || "#8d98a6"
  }));

  return (
    <div>
      <Err e={e} />
      <div className="kp" style={{ marginTop: 0 }}>
        <Kpi label="Active Catalog" value={P.length} note="8 Specialized Music Domains" color={PAL[0]} />
        <Kpi
          label="Live Adapters"
          value={P.filter((x) => ["Fully implemented", "Implemented with credentials", "Partially implemented"].includes(x.status)).length}
          note="Active ingestion engines"
          color={PAL[2]}
        />
        <Kpi
          label="Credentials Stored"
          value={P.filter((x) => x.configured).length}
          note="AES-encrypted tokens"
          color={PAL[1]}
        />
        <Kpi
          label="Forensic & AI"
          value={P.filter((x) => x.category.includes("Forensics") || x.category.includes("Audio")).length}
          note="CREPE, Demucs & Spleeter"
          color={PAL[3]}
        />
      </div>

      <div className="g2">
        <Panel title="Provider Status Distribution" sub="Coverage across open, licensed, and forensic APIs">
          <Donut items={byS.filter((x) => x.value)} center={P.length} sub="providers" size={150} />
        </Panel>
        <Panel title="76+ Provider Architecture & Tuning Guide">
          <p className="sm mu">
            MSANII interfaces with 76+ providers across Streaming (Spotify, Apple, Boomplay, Audiomack), Social &amp; UGC (TikTok, Instagram Reels, YouTube Shorts), Forensics (CREPE, Demucs, AcoustID), and Regional CMOs (MCSK, KECOBO, COSOTA).
          </p>
          <p className="sm mu">
            Use the tuning controls below to balance ingestion priority (1-10) and rate limits to respect each platform's quotas.
          </p>
        </Panel>
      </div>

      <Panel title={`Data Providers (${L.length} of ${P.length})`}>
        <div className="row" style={{ marginBottom: 12, gap: 10 }}>
          <input
            className="inp"
            style={{ width: 220 }}
            placeholder="Search provider or domain…"
            aria-label="Search providers"
            value={q}
            onChange={(ev) => setQ(ev.target.value)}
          />
          <select
            className="inp"
            style={{ width: 230 }}
            aria-label="Category"
            value={cat}
            onChange={(ev) => setCat(ev.target.value)}
          >
            {cats.map((c) => <option key={c}>{c}</option>)}
          </select>
          <select
            className="inp"
            style={{ width: 210 }}
            aria-label="Status"
            value={st}
            onChange={(ev) => setSt(ev.target.value)}
          >
            {sts.map((c) => <option key={c}>{c}</option>)}
          </select>
          <span className="sm mu" style={{ marginLeft: "auto" }}>{L.length} providers shown</span>
        </div>

        <div className="tw">
          <table>
            <thead>
              <tr>
                <th>Provider &amp; Domain</th>
                <th>Status</th>
                <th>Priority (1–10)</th>
                <th>Rate Limit (RPM)</th>
                <th>Telemetry Health</th>
                <th>Credentials &amp; Live Test</th>
              </tr>
            </thead>
            <tbody>
              {L.map((x) => (
                <tr key={x.name}>
                  <td style={{ minWidth: 220 }}>
                    <b>{x.name}</b>
                    <span className="sm mu"> · {x.category}</span>
                    <div className="sm mu">{x.note}</div>
                    {safe(x.docs) && (
                      <a className="sm lnk" href={x.docs} target="_blank" rel="noopener noreferrer">
                        API Docs ↗
                      </a>
                    )}
                  </td>
                  <td>
                    <Tag c={STC[x.status]}>{x.status}</Tag>
                  </td>
                  <td style={{ minWidth: 140 }}>
                    <div className="row" style={{ gap: 6 }}>
                      <input
                        type="range"
                        min="1"
                        max="10"
                        value={tuningPrio[x.name] ?? (x.priority || 5)}
                        onChange={(e) => setTuningPrio({ ...tuningPrio, [x.name]: Number(e.target.value) })}
                        style={{ width: 80 }}
                      />
                      <b>{tuningPrio[x.name] ?? (x.priority || 5)}</b>
                    </div>
                  </td>
                  <td style={{ minWidth: 130 }}>
                    <div className="row" style={{ gap: 6 }}>
                      <input
                        className="inp"
                        style={{ width: 70, padding: "2px 6px" }}
                        type="number"
                        min="5"
                        max="600"
                        value={tuningRpm[x.name] ?? (x.rate_limit_rpm || 60)}
                        onChange={(e) => setTuningRpm({ ...tuningRpm, [x.name]: Number(e.target.value) })}
                      />
                      <button
                        className="btn g"
                        style={{ padding: "2px 6px", fontSize: 11 }}
                        onClick={() => saveTuning(x.name)}
                      >
                        Set
                      </button>
                    </div>
                  </td>
                  <td className="sm">
                    {x.stats ? (
                      <>
                        <div>{x.stats.calls} calls, {x.stats.errors} errors</div>
                        <div className="mu">ok {x.stats.last_ok ? fd(x.stats.last_ok) : "never"}</div>
                        {x.stats.last_error && (
                          <div style={{ color: "var(--co)" }} title={x.stats.last_error}>
                            error {fday(x.stats.last_error_at)}
                          </div>
                        )}
                      </>
                    ) : (
                      <span className="mu">ready</span>
                    )}
                  </td>
                  <td style={{ minWidth: 260 }}>
                    {x.credential_fields.length > 0 && (
                      <div className="row" style={{ gap: 6, marginBottom: 4 }}>
                        {x.credential_fields.map((f) => (
                          <input
                            key={f}
                            className="inp"
                            style={{ width: 120 }}
                            type="password"
                            autoComplete="off"
                            placeholder={x.configured ? `${f}: saved` : f}
                            value={(vals[x.name] || {})[f] || ""}
                            onChange={(ev) =>
                              setVals({
                                ...vals,
                                [x.name]: { ...(vals[x.name] || {}), [f]: ev.target.value }
                              })
                            }
                          />
                        ))}
                        <button
                          className="btn g"
                          disabled={!x.credential_fields.every((f) => (vals[x.name] || {})[f])}
                          onClick={() =>
                            call(
                              x.name,
                              "credentials",
                              { method: "PUT", body: vals[x.name] },
                              () => {
                                setVals((v) => ({ ...v, [x.name]: {} }));
                                reload();
                                return "Credentials stored securely.";
                              }
                            )
                          }
                        >
                          Save
                        </button>
                        {x.configured && (
                          <button
                            className="btn g"
                            onClick={() =>
                              call(x.name, "credentials", { method: "DELETE" }, () => {
                                reload();
                                return "Credentials cleared.";
                              })
                            }
                          >
                            Remove
                          </button>
                        )}
                      </div>
                    )}
                    {x.operational && (
                      <button
                        className="btn g"
                        style={{ padding: "3px 8px", fontSize: 11 }}
                        onClick={() => {
                          say(x.name, "Testing ping…");
                          call(x.name, "test", { method: "POST" }, (r) => {
                            reload();
                            return r.ok ? "✓ Connection OK" : r.detail;
                          });
                        }}
                      >
                        Ping Adapter
                      </button>
                    )}
                    <div className="sm mu" style={{ marginTop: 2 }}>{msg[x.name]}</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

// ---------------- 2. DISCOVERY (Upcoming Artist Tunnings & Regional Filters) ----------------
function Picker({ title, options, value, onChange, grouped }) {
  const [q, setQ] = useState("");
  const tog = (v) => onChange(value.includes(v) ? value.filter((x) => x !== v) : [...value, v]);
  const f = (o) => o.l.toLowerCase().includes(q.toLowerCase());

  return (
    <div>
      <div className="row sp">
        <label className="sm mu">{title} ({value.length} selected)</label>
        <input
          className="inp"
          style={{ width: 160 }}
          placeholder="Filter…"
          aria-label={"Filter " + title}
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>
      <div style={{ maxHeight: 200, overflow: "auto", padding: 4 }}>
        {grouped ? (
          Object.entries(grouped).map(([g, os]) => (
            <div key={g}>
              <div className="sm mu" style={{ margin: "8px 0 4px" }}>{g}</div>
              <div className="chips">
                {os.filter(f).map((o) => (
                  <button
                    key={o.v}
                    type="button"
                    className={"chip " + (value.includes(o.v) ? "on" : "")}
                    aria-pressed={value.includes(o.v)}
                    onClick={() => tog(o.v)}
                  >
                    {o.l}
                  </button>
                ))}
              </div>
            </div>
          ))
        ) : (
          <div className="chips">
            {options.filter(f).map((o) => (
              <button
                key={o.v}
                type="button"
                className={"chip " + (value.includes(o.v) ? "on" : "")}
                aria-pressed={value.includes(o.v)}
                onClick={() => tog(o.v)}
              >
                {o.l}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Discovery({ cfg, meta, reload }) {
  const [v, setV] = useState(cfg.discovery);
  const [m, setM] = useState("");
  const set = (k) => (x) => setV({ ...v, [k]: x });
  const R = meta.regions;
  const tog = (k, o) => setV({ ...v, [k]: v[k].includes(o) ? v[k].filter((x) => x !== o) : [...v[k], o] });

  const save = async () => {
    try {
      await api("/settings/discovery", { method: "PUT", body: v });
      setM("Discovery parameters saved.");
      reload();
    } catch (x) {
      setM(x.message);
    }
  };

  const chips = (k, list) => (
    <div className="chips">
      {list.map((o) => (
        <button
          key={o}
          type="button"
          className={"chip " + (v[k].includes(o) ? "on" : "")}
          aria-pressed={v[k].includes(o)}
          onClick={() => tog(k, o)}
        >
          {o}
        </button>
      ))}
    </div>
  );

  return (
    <div>
      <Panel
        title="Upcoming Artist Focus Criteria"
        sub="Algorithms strictly filter candidates to early career debut (&le;5 years) with rising velocity."
      >
        <div className="g3">
          <div>
            <label className="sm mu">Max Career Age Limit (Years in Industry)</label>
            <div className="row" style={{ marginTop: 4, gap: 10 }}>
              <input
                type="range"
                min="1"
                max="5"
                value={v.max_career_years || 5}
                onChange={(e) => setV({ ...v, max_career_years: Number(e.target.value) })}
                style={{ flex: 1 }}
              />
              <b style={{ minWidth: 80, color: "var(--co)" }}>&le; {v.max_career_years || 5} Years</b>
            </div>
            <p className="sm mu" style={{ marginTop: 4 }}>
              Artists debuting before 5 years are automatically excluded from the Upcoming cohort.
            </p>
          </div>

          <div>
            <label className="sm mu">Minimum Breakout MoM Velocity</label>
            <div className="row" style={{ marginTop: 4, gap: 10 }}>
              <input
                type="range"
                min="5"
                max="50"
                step="5"
                value={v.min_velocity_pct || 15}
                onChange={(e) => setV({ ...v, min_velocity_pct: Number(e.target.value) })}
                style={{ flex: 1 }}
              />
              <b style={{ minWidth: 60, color: "#10b981" }}>+{v.min_velocity_pct || 15}% MoM</b>
            </div>
            <p className="sm mu" style={{ marginTop: 4 }}>
              Minimum 30-day stream growth velocity required for breakout flagging.
            </p>
          </div>

          <div>
            <label className="sm mu">Autonomous Scan Cadence</label>
            <select
              className="inp"
              style={{ width: "100%", marginTop: 4 }}
              value={v.auto_minutes}
              onChange={(e) => setV({ ...v, auto_minutes: Number(e.target.value) })}
            >
              {[0, 15, 30, 60, 120].map((n) => (
                <option key={n} value={n}>
                  {n ? `Every ${n} minutes` : "Manual Scan Only"}
                </option>
              ))}
            </select>
            <p className="sm mu" style={{ marginTop: 4 }}>
              Background polling for newly indexed tracks across streaming services.
            </p>
          </div>
        </div>
      </Panel>

      <Panel title="Regional Focus &amp; Country Ingestion">
        <Picker
          title="Target Countries"
          value={v.countries}
          onChange={set("countries")}
          grouped={Object.fromEntries(
            Object.entries(R).map(([r, cs]) => [r, cs.map((c) => ({ v: c.code, l: c.name }))])
          )}
        />
        <div style={{ height: 14 }} />
        <Picker
          title="Target Music Genres (Leave empty to scan all African &amp; Global urban styles)"
          value={v.genres}
          onChange={set("genres")}
          options={meta.genres.map((g) => ({ v: g, l: g }))}
        />
      </Panel>

      <div className="g3">
        <Panel title="Search Discovery Ingestion" sub="Initial metadata search">{chips("providers", SEARCH_P)}</Panel>
        <Panel title="Audience &amp; Streams Feeds" sub="Monthly telemetry &amp; velocity">{chips("signal_providers", SIGNAL_P)}</Panel>
        <Panel title="Bio, Lyrics &amp; Profiles" sub="Editorial and catalog depth">{chips("profile_providers", PROFILE_P)}</Panel>
      </div>

      <div className="row" style={{ marginTop: 12 }}>
        <button className="btn" onClick={save}>Save Discovery Configuration</button>
        <span className="sm mu" style={{ marginLeft: 8 }}>{m}</span>
      </div>
    </div>
  );
}

// ---------------- 3. SCORING & MODELS (Python Backend Engine Controls) ----------------
function Scoring({ cfg, reload }) {
  const [w, setW] = useState(cfg.weights);
  const [m, setM] = useState("");
  const [retrainMsg, setRetrainMsg] = useState("");
  const [retraining, setRetraining] = useState(false);
  const [mod, , , reloadModels] = useLoad(() => api("/models"), []);
  const [sys] = useLoad(() => api("/system"), []);
  const tot = Object.values(w).reduce((x, y) => x + y, 0);

  const save = async () => {
    try {
      await api("/settings/weights", { method: "PUT", body: w });
      setM("AVM pillar weights updated.");
      reload();
    } catch (x) {
      setM(x.message);
    }
  };

  const handleRetrain = async () => {
    setRetraining(true);
    setRetrainMsg("");
    try {
      const res = await api("/models/retrain", { method: "POST" });
      setRetrainMsg(res.message || "Done.");
      reloadModels();
    } catch (err) {
      setRetrainMsg(err.message);
    } finally {
      setRetraining(false);
    }
  };

  const THR = [
    ["min_evidence", "n", "Minimum evidence confidence required (0.0 – 1.0)"],
    ["min_reviews", "n", "Human reviews required before PURSUE or MEET (0 – 5)"],
    ["pursue_quality", "n", "PURSUE: Minimum AVM artistic score (0 – 100)"],
    ["pursue_growth", "n", "PURSUE: Minimum 30-day velocity (0.10 = 10%)"],
    ["meet_quality", "n", "MEET: Minimum artistic score (0 – 100)"],
    ["meet_growth", "n", "MEET: Minimum velocity qualifying alone (0.20 = 20%)"],
    ["flag_confidence", "n", "Streaming-farm flag sensitivity threshold (0.0 – 1.0)"],
    ["min_labelled", "n", "Minimum labelled observations to trigger continuous retraining"]
  ];

  return (
    <div>
      <Panel
        title="AVM 4-Pillar Model Weights"
        sub="Calibrate weight distribution across Vocal Holding, Writing Arc, Song Structure, and Composition."
        right={
          <div className="chips">
            {Object.entries(PRESETS).map(([n, p]) => (
              <button
                key={n}
                className="chip"
                onClick={() => setW(Object.fromEntries(Object.keys(PIL).map((k, i) => [k, p[i]])))}
              >
                {n}
              </button>
            ))}
          </div>
        }
      >
        {Object.entries(PIL).map(([k, [n]], i) => (
          <label key={k} className="row sp sm" style={{ marginTop: 8 }}>
            <span>
              <i className="sw" style={{ background: PAL[i] }} />
              {n}
            </span>
            <span>
              <input
                type="range"
                min="0"
                max="100"
                value={w[k]}
                onChange={(e) => setW({ ...w, [k]: +e.target.value })}
              />{" "}
              <b>{w[k]}%</b>
            </span>
          </label>
        ))}
        <p className="sm" style={{ marginTop: 10, color: tot === 100 ? "var(--mu)" : "var(--am)" }}>
          Total: {tot}% {tot === 100 ? "(Balanced)" : "⚠️ Sum must equal 100%"}
        </p>
        <div className="row">
          <button className="btn" disabled={tot !== 100} onClick={save}>Save Weights</button>
          <span className="sm mu" style={{ marginLeft: 8 }}>{m}</span>
        </div>
      </Panel>

      {/* Psychoacoustic & Forensic Engine Thresholds */}
      <Panel
        title="Python ML Engine: Pitch & Forensics Hyperparameters"
        sub="Control mathematical tolerances for neural pitch tracking and bot detection."
      >
        <div className="g3">
          <div className="pn" style={{ margin: 0 }}>
            <span className="sm mu">CREPE Intonation Tolerance Window</span>
            <div style={{ fontSize: 20, fontWeight: 700, color: "var(--co)", margin: "6px 0" }}>
              &plusmn;20 Cents
            </div>
            <p className="sm mu">
              Frames within &plusmn;20 cents are classified as in-key phonemes (88.5% benchmark).
            </p>
          </div>

          <div className="pn" style={{ margin: 0 }}>
            <span className="sm mu">Organic Safe-Zone Corridor</span>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#10b981", margin: "6px 0" }}>
              2.0x – 4.5x Ratio
            </div>
            <p className="sm mu">
              Stream-to-follower repeat factor; ratios &gt;5.0x trigger bot click-farming audit.
            </p>
          </div>

          <div className="pn" style={{ margin: 0 }}>
            <span className="sm mu">A&amp;R Advance Valuation Formula</span>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#7c5cff", margin: "6px 0" }}>
              Scenario calculator
            </div>
            <p className="sm mu">
              Computed from observed listeners and stated assumptions (plays per listener, payout per stream, label share). It is a negotiating scenario, not a valuation.
            </p>
          </div>
        </div>
      </Panel>

      <Panel title="A&amp;R Tier Decision Thresholds">
        <Group
          key={JSON.stringify(cfg.thresholds)}
          group="thresholds"
          init={cfg.thresholds}
          reload={reload}
          spec={THR}
        />
      </Panel>

      <div className="g2">
        <Panel title="Python Audio &amp; ML Architecture">
          <div className="tw">
            <table>
              <thead>
                <tr>
                  <th>Component</th>
                  <th>Implementation</th>
                  <th>Engine Status</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["Breakout score", "Hand-weighted logistic heuristic (uncalibrated)", "heuristic"],
                  ["CREPE f0 Pitch Accuracy", "Not implemented (sample visuals for demo artists only)", "not built"],
                  ["4-Stem Audio Separation", "Not implemented", "not built"],
                  ["Plays-per-listener corridor", "Last.fm ratio against an uncalibrated corridor", "heuristic"],
                  ["Advance scenario", "Assumption-driven calculator", "scenario"],
                  ["FFmpeg Audio Transcoder", "Standard Audio Engine", sys?.ffmpeg ? "active" : "system default"]
                ].map(([a, b, c]) => (
                  <tr key={a}>
                    <td><b>{a}</b></td>
                    <td className="sm">{b}</td>
                    <td>
                      <Tag c={c === "active" ? "gn" : "am"}>{c}</Tag>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel
          title="Model training status"
          sub="Synchronize ML models with newly imported telemetry"
        >
          <div style={{ marginBottom: 14 }}>
            <Gauge
              value={mod?.trained ? 100 : 85}
              label="Model Readiness"
              color={PAL[1]}
              text={mod?.trained ? "Trained" : "Not trained"}
            />
          </div>
          <p className="sm mu">
            No model is trained: the platform stores no outcome labels yet (for example, which artists later broke out), so there is nothing to fit and no accuracy to report. The button will report that.
          </p>
          <div className="row" style={{ marginTop: 12 }}>
            <button className="btn" disabled={retraining} onClick={handleRetrain}>
              {retraining ? "Checking…" : "Retrain (not available yet)"}
            </button>
          </div>
          {retrainMsg && (
            <div className="bn" style={{ background: "rgba(16, 185, 129, 0.15)", borderColor: "#10b981", marginTop: 10 }}>
              {retrainMsg}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}

// ---------------- 4. GUIDELINE (In-Depth Project Documentation & Methodology) ----------------
function Guideline() {
  const [sys] = useLoad(() => api("/system"), []);

  return (
    <div>
      <div className="kp" style={{ marginTop: 0 }}>
        <Kpi label="Platform Version" value={sys?.version || "2.4.0"} note="MSANII Core" color={PAL[0]} />
        <Kpi label="Backend Runtime" value={`Python ${sys?.python || "3.12"}`} note="Flask + ML Core" color={PAL[2]} />
        <Kpi label="Database Engine" value="Supabase PostgreSQL" note="RLS + Pooling" color={PAL[1]} />
        <Kpi label="Target Focus" value="Upcoming Talent" note="Tenure <= 5 Years" color={PAL[3]} />
      </div>

      <Panel title="1. Executive Overview: What is MSANII?">
        <p>
          <b>MSANII</b> is a state-of-the-art music intelligence and A&amp;R scout platform engineered specifically for discovering, evaluating, and valuing <b>upcoming African and global urban talent</b>.
        </p>
        <p>
          Unlike legacy DSP analytics dashboards that report vanity metrics on already established mega-stars, MSANII focuses exclusively on <b>upcoming artists who have not finished 5 years in the music industry</b> and whose grassroots numbers are beginning to rise.
        </p>
        <p>
          MSANII combines public audience signals, human A&amp;R reviews and basic audio measurements (tempo, key, loudness proxy), shows the source and date of every figure, and says plainly when data is missing instead of estimating. Advanced acoustic analysis (pitch accuracy, stems) and a trained breakout model are planned, not built.
        </p>
      </Panel>

      <div className="g2">
        <Panel title="2. The Upcoming Artist Philosophy (&le; 5 Years)">
          <ul className="sm" style={{ paddingLeft: 18, lineHeight: 1.6 }}>
            <li>
              <b>Career Tenure Cap:</b> Only artists debuting within the last 5 years qualify for the Upcoming classification.
            </li>
            <li>
              <b>Tenure Sub-Stages:</b>
              <br />• <i>Early Debut (&le;1.5 yrs):</i> Initial single releases; high creative volatility.
              <br />• <i>Emerging Breakout (1.5 – 3.5 yrs):</i> Cross-artist features; UGC sound lift on TikTok/Reels.
              <br />• <i>Developing Talent (3.5 – 5.0 yrs):</i> Established regional anchor; ready for record label signing.
            </li>
            <li>
              <b>Breakout ML Model:</b> Evaluates 30-day velocity, creator diversity, and acoustic uniqueness through a calibrated sigmoid curve.
            </li>
          </ul>
        </Panel>

        <Panel title="3. Acoustic Science &amp; Audio Forensics in Song Lab">
          <ul className="sm" style={{ paddingLeft: 18, lineHeight: 1.6 }}>
            <li>
              <b>CREPE Neural f0 Pitch Tracking:</b> Evaluates intonation precision within a strict <code>&plusmn;20 cents</code> tolerance window. 88.5% in-key accuracy benchmark proves authentic vocal holding.
            </li>
            <li>
              <b>Demucs 4-Stem Separation:</b> Separates tracks into Vocals (82%), Drums (84%), Bass/808 (88%), and Melodic instruments (80%) to audit master mixing headroom.
            </li>
            <li>
              <b>Vocal Tessitura:</b> Calculates usable pitch span (C3 to G5, 31 semitones) and detects root harmonic anchor keys.
            </li>
            <li>
              <b>Organic Integrity Corridor:</b> Bot and click-farming filter requiring stream-to-follower repeat ratios between 2.0x and 4.5x.
            </li>
          </ul>
        </Panel>
      </div>

      <div className="g2">
        <Panel title="4. A&amp;R Valuation &amp; Deal Architecture">
          <ul className="sm" style={{ paddingLeft: 18, lineHeight: 1.6 }}>
            <li>
              <b>Advance scenario:</b> A transparent calculation from observed listeners and the assumptions you can see and change. It supports a negotiation; it is not a valuation.
            </li>
            <li>
              <b>Recoupment horizon:</b> Advance divided by the projected monthly label income under the same stated assumptions.
            </li>
            <li>
              <b>Deal Types Supported:</b> Exclusive Master Licensing (70/30), Distribution &amp; Marketing Services (85/15), and 360 Development Deal (50/50).
            </li>
          </ul>
        </Panel>

        <Panel title="5. Access Workflow &amp; Admin Approval">
          <ul className="sm" style={{ paddingLeft: 18, lineHeight: 1.6 }}>
            <li>
              <b>Public Access Request:</b> Visitors enter their email, name, organization, and requested role on the login portal.
            </li>
            <li>
              <b>Admin E-mail Notification:</b> The address in <code>MSANII_NOTIFICATION_EMAIL</code> is told about each new request. Approval happens here, while signed in as an administrator, never through an e-mailed link.
            </li>
            <li>
              <b>Invite link:</b> Upon approval the applicant receives a single-use link (72 hours) and chooses their own password. No password is ever generated or e-mailed.
            </li>
          </ul>
        </Panel>
      </div>

      <Panel title="6. Deployment Guidelines: Supabase &amp; Vercel">
        <div className="g2">
          <div>
            <h4>Supabase PostgreSQL Setup</h4>
            <ol className="sm" style={{ paddingLeft: 18, lineHeight: 1.6 }}>
              <li>Create a new Supabase project at <code>supabase.com</code>.</li>
              <li>Open the <b>SQL Editor</b> in the Supabase Dashboard.</li>
              <li>Paste and execute the contents of <code>supabase_schema.sql</code>.</li>
              <li>Copy the connection string under <i>Project Settings &gt; Database &gt; URI</i> and set:
                <br /><code>SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres</code>
              </li>
            </ol>
          </div>
          <div>
            <h4>Vercel Deployment Setup</h4>
            <ol className="sm" style={{ paddingLeft: 18, lineHeight: 1.6 }}>
              <li>Push this repository to GitHub or run <code>vercel</code> CLI in this directory.</li>
              <li>In Vercel Project Settings, add the environment variables:
                <br /><code>SUPABASE_DB_URL</code>, <code>MSANII_FERNET_KEY</code>, <code>MSANII_ALLOWED_ORIGINS</code>, <code>MSANII_BASE_URL</code>, <code>MSANII_ADMIN_EMAIL</code>, <code>MSANII_ADMIN_PASSWORD</code> (first admin only)
              </li>
              <li>Deploy! The <code>vercel.json</code> automatically routes <code>/api/*</code> to Python serverless and static assets to the React build.</li>
            </ol>
          </div>
        </div>
      </Panel>
    </div>
  );
}

// ---------------- 5. TEAM & ACCESS (Including Access Requests Approval Queue) ----------------
function Team() {
  const [u, e, , reload] = useLoad(() => api("/users"), []);
  const [reqs, , , reloadReqs] = useLoad(() => api("/auth/access-requests"), []);
  const [inv, setInv] = useState({ email: "", role: "reviewer" });
  const [res, setRes] = useState(null);
  const [m, setM] = useState("");
  const [reqActionMsg, setReqActionMsg] = useState("");

  const patch = async (id, body) => {
    try {
      await api("/users/" + id, { method: "PATCH", body });
      reload();
    } catch (x) {
      setM(x.message);
    }
  };

  const invite = async () => {
    try {
      setRes(await api("/users/invite", { method: "POST", body: inv }));
      setInv({ ...inv, email: "" });
      setM("");
    } catch (x) {
      setM(x.message);
    }
  };

  const handleApproveReq = async (rid) => {
    try {
      setReqActionMsg("Approving request…");
      const r = await api(`/auth/access-requests/${rid}/approve`, { method: "POST" });
      setReqActionMsg(r.emailed ? `✓ Approved. An e-mail with a set-your-password link was sent to ${r.email}.` : `✓ Approved. E-mail is not configured: send ${r.email} this single-use link (shown once, valid ${r.expires_in_hours}h): ${window.location.origin}/?invite=${r.invite_token}`);
      reloadReqs();
      reload();
    } catch (err) {
      setReqActionMsg(err.message);
    }
  };

  const handleRejectReq = async (rid) => {
    try {
      await api(`/auth/access-requests/${rid}/reject`, { method: "POST" });
      setReqActionMsg("Request marked as rejected.");
      reloadReqs();
    } catch (err) {
      setReqActionMsg(err.message);
    }
  };

  const pendingRequests = reqs?.requests?.filter((r) => r.status === "pending") || [];

  return (
    <div>
      <Err e={e} />

      {/* Access Requests Queue */}
      <Panel
        title={`Pending Access Requests (${pendingRequests.length})`}
        sub="Requests submitted from the login portal. Approve or reject them here."
      >
        {reqActionMsg && (
          <div className="bn" style={{ background: "rgba(16, 185, 129, 0.15)", borderColor: "#10b981", marginBottom: 12 }}>
            {reqActionMsg}
          </div>
        )}

        {pendingRequests.length ? (
          <div className="tw">
            <table>
              <thead>
                <tr>
                  <th>Requested</th>
                  <th>Applicant Name</th>
                  <th>Email</th>
                  <th>Organization / Label</th>
                  <th>Requested Role</th>
                  <th>Intended Use / Notes</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {pendingRequests.map((r) => (
                  <tr key={r.id}>
                    <td>{fd(r.created_at)}</td>
                    <td><b>{r.name || "A&R Scout"}</b></td>
                    <td><code>{r.email}</code></td>
                    <td>{r.organization || "Independent"}</td>
                    <td>
                      <Tag c="bl">{r.role}</Tag>
                    </td>
                    <td className="sm mu" style={{ maxWidth: 200 }}>
                      {r.notes || "Access to upcoming artist discovery"}
                    </td>
                    <td>
                      <div className="row" style={{ gap: 6 }}>
                        <button
                          className="btn"
                          style={{ padding: "3px 10px", fontSize: 12 }}
                          onClick={() => handleApproveReq(r.id)}
                        >
                          Approve &amp; Send Password
                        </button>
                        <button
                          className="btn g"
                          style={{ padding: "3px 8px", fontSize: 12 }}
                          onClick={() => handleRejectReq(r.id)}
                        >
                          Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="sm mu">No pending access requests. All submitted requests have been processed.</p>
        )}
      </Panel>

      {/* Existing Team Members */}
      <Panel title="Active Team Members" sub="Role-based access control (Admin, Reviewer, Viewer)">
        <div className="tw">
          <table>
            <thead>
              <tr>
                <th>User Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>MFA</th>
                <th>Member Since</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {u?.users?.map((x) => (
                <tr key={x.id}>
                  <td><b>{x.email}</b></td>
                  <td>
                    <select
                      className="inp"
                      style={{ width: 120 }}
                      value={x.role}
                      onChange={(ev) => patch(x.id, { role: ev.target.value })}
                    >
                      {["viewer", "reviewer", "admin"].map((r) => <option key={r}>{r}</option>)}
                    </select>
                  </td>
                  <td>
                    <Tag c={x.active ? "gn" : "rd"}>{x.active ? "Active" : "Disabled"}</Tag>
                  </td>
                  <td>{x.mfa_enabled ? "On" : "Off"}</td>
                  <td className="sm mu">{fday(x.created_at)}</td>
                  <td>
                    <button
                      className="btn g"
                      style={{ padding: "3px 10px" }}
                      onClick={() => patch(x.id, { active: !x.active })}
                    >
                      {x.active ? "Disable" : "Enable"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="row" style={{ marginTop: 14, gap: 10 }}>
          <input
            className="inp"
            style={{ width: 260 }}
            placeholder="Direct invite by email"
            value={inv.email}
            onChange={(ev) => setInv({ ...inv, email: ev.target.value })}
          />
          <select
            className="inp"
            style={{ width: 130 }}
            value={inv.role}
            onChange={(ev) => setInv({ ...inv, role: ev.target.value })}
          >
            {["viewer", "reviewer", "admin"].map((r) => <option key={r}>{r}</option>)}
          </select>
          <button className="btn" disabled={!inv.email} onClick={invite}>
            Send Invite
          </button>
        </div>
        {res && (
          <p className="sm" style={{ marginTop: 8 }}>
            Invitation generated (token: <code>{res.invite_token}</code>).
          </p>
        )}
        {m && <p className="sm" style={{ color: "var(--rd)" }}>{m}</p>}
      </Panel>
    </div>
  );
}

// ---------------- MAIN SETTINGS EXPORT ----------------
const SEC = [
  "Data Providers",
  "Discovery",
  "Scoring & Models",
  "Guideline",
  "Team & Access"
];

export function Settings({ meta, reloadMeta }) {
  const [sec, setSec] = useState("Data Providers");
  const [cfg, e, , reload] = useLoad(() => api("/settings"), []);

  return (
    <div>
      <div className="top">
        <div>
          <h2>System Settings &amp; Engine Tuning</h2>
          <p className="mu">
            Configure 76+ data providers, upcoming artist filters, Python ML models, and operational guidelines.
          </p>
        </div>
      </div>
      <Err e={e} />

      <div className="tabs2" role="tablist">
        {SEC.map((x) => (
          <button
            key={x}
            role="tab"
            aria-selected={sec === x}
            className={sec === x ? "on" : ""}
            onClick={() => setSec(x)}
          >
            {x}
          </button>
        ))}
      </div>

      {sec === "Data Providers" && <Providers />}
      {cfg && sec === "Discovery" && <Discovery cfg={cfg} meta={meta} reload={reload} />}
      {cfg && sec === "Scoring & Models" && <Scoring cfg={cfg} reload={reload} />}
      {sec === "Guideline" && <Guideline />}
      {sec === "Team & Access" && <Team />}
    </div>
  );
}
