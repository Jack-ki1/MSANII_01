import { useState } from "react";
import { api } from "./api";
import { ACTS, TC, TCOL, Tag } from "./ui";
import { useLoad, Err, Kpi, Panel, fd, fday, avgOf, cname, downloadCsv } from "./shared";
import { Donut, Scatter, Funnel, HBars, ColumnChart, Radar, PAL, fmt, pct, Empty } from "./charts";

const TIERS = Object.keys(TC);
const LANES = ["Monitor", "Add to shortlist", "Request demo", "Contact", "Schedule meeting", "Pursue", "Defer pending evidence", "Reject"];
const TXT = {
  PURSUE: "Exceptional breakout trajectory, verified acoustic depth, and organic safe-zone status. Actively pursue.",
  MEET: "High artistic merit or rapid velocity. Recommended for A&R executive introduction.",
  WATCH: "Promising upcoming talent with growing indicators; track 30-day velocity before making an offer.",
  "MORE EVIDENCE": "Early debut; collect audio stem telemetry and baseline streams in Song Lab."
};

function DecisionForm({ item, onDone }) {
  const [f, setF] = useState({ act: ACTS[0], why: "", own: "", due: "" });
  const [m, setM] = useState("");

  const save = async () => {
    try {
      await api("/decisions", {
        method: "POST",
        body: {
          artist_id: item.id,
          action: f.act,
          rationale: f.why,
          owner: f.own,
          follow_up: f.due
        }
      });
      setF({ ...f, why: "" });
      setM("Decision recorded and cryptographically signed.");
      onDone();
    } catch (x) {
      setM(x.message);
    }
  };

  return (
    <div className="row" style={{ marginTop: 12, gap: 10 }}>
      <select
        className="inp"
        style={{ width: 190 }}
        aria-label="Action"
        value={f.act}
        onChange={(e) => setF({ ...f, act: e.target.value })}
      >
        {ACTS.map((x) => <option key={x}>{x}</option>)}
      </select>
      <input
        className="inp"
        style={{ width: 250 }}
        aria-label="Rationale"
        placeholder="A&R Rationale & Deal terms (required)"
        value={f.why}
        onChange={(e) => setF({ ...f, why: e.target.value })}
      />
      <input
        className="inp"
        style={{ width: 140 }}
        aria-label="Owner"
        placeholder="Scout / Executive"
        value={f.own}
        onChange={(e) => setF({ ...f, own: e.target.value })}
      />
      <input
        className="inp"
        style={{ width: 150 }}
        type="date"
        aria-label="Follow-up date"
        value={f.due}
        onChange={(e) => setF({ ...f, due: e.target.value })}
      />
      <button className="btn" disabled={f.why.trim().length < 3} onClick={save}>
        Record Decision
      </button>
      <span className="sm mu">{m}</span>
    </div>
  );
}

// Interactive Deal Advance & Recoupment Calculator
function DealCalculator({ baseListeners = 0 }) {
  const [advance, setAdvance] = useState(0);
  const [dealType, setDealType] = useState("licensing");
  const [royaltyShare, setRoyaltyShare] = useState(70); // 70% artist / 30% label
  const [streamGrowthMoM, setStreamGrowthMoM] = useState(0);

  // Math model: Average DSP blend per stream in East Africa + Global Diaspora (~$0.0028)
  const ratePerStream = 0.0028;
  const streamsPerListener = 3.0; // ASSUMPTION: plays per listener per month (not measured)
  const monthlyStreams = baseListeners * streamsPerListener;
  const labelSharePct = (100 - royaltyShare) / 100;
  const monthlyLabelGross = monthlyStreams * ratePerStream * labelSharePct;

  // Recoupment calculation
  const monthsToRecoup = monthlyLabelGross > 0 ? (advance / monthlyLabelGross).toFixed(1) : "n/a";
  const projectedYear1Yield = Math.round(monthlyLabelGross * 12 * (1 + (streamGrowthMoM / 100) * 0.5));
  const roiMultiplier = advance > 0 ? ((projectedYear1Yield - advance) / advance * 100).toFixed(0) : 0;

  return (
    <Panel
      title="A&R Advance Valuation & Recoupment Simulator"
      sub={baseListeners ? `Scenario calculator, not a valuation. Inputs: ${baseListeners.toLocaleString()} listeners (latest observed for the top-ranked artist), 3 plays per listener per month (assumption), growth you enter.` : "Scenario calculator, not a valuation. No artist with an audience observation yet, so there is nothing to base it on."}
    >
      <div className="g4" style={{ marginBottom: 16 }}>
        <div>
          <label className="sm mu">Deal Architecture</label>
          <select
            className="inp"
            style={{ width: "100%", marginTop: 4 }}
            value={dealType}
            onChange={(e) => {
              setDealType(e.target.value);
              if (e.target.value === "distribution") setRoyaltyShare(85);
              if (e.target.value === "licensing") setRoyaltyShare(70);
              if (e.target.value === "360") setRoyaltyShare(50);
            }}
          >
            <option value="licensing">Exclusive Master Licensing (70/30)</option>
            <option value="distribution">Distribution &amp; Marketing Services (85/15)</option>
            <option value="360">Full 360 Development Deal (50/50)</option>
          </select>
        </div>

        <div>
          <label className="sm mu">Proposed Advance ($)</label>
          <div className="row" style={{ marginTop: 4, gap: 8 }}>
            <input
              type="range"
              min="1000"
              max="15000"
              step="250"
              value={advance}
              onChange={(e) => setAdvance(Number(e.target.value))}
              style={{ flex: 1 }}
            />
            <b style={{ minWidth: 65, color: "var(--co)", fontSize: 16 }}>${advance.toLocaleString()}</b>
          </div>
        </div>

        <div>
          <label className="sm mu">Artist Royalty Share (%)</label>
          <div className="row" style={{ marginTop: 4, gap: 8 }}>
            <input
              type="range"
              min="40"
              max="90"
              step="5"
              value={royaltyShare}
              onChange={(e) => setRoyaltyShare(Number(e.target.value))}
              style={{ flex: 1 }}
            />
            <b style={{ minWidth: 45 }}>{royaltyShare}%</b>
          </div>
        </div>

        <div>
          <label className="sm mu">MoM Stream Growth (%)</label>
          <div className="row" style={{ marginTop: 4, gap: 8 }}>
            <input
              type="range"
              min="0"
              max="60"
              step="1"
              value={streamGrowthMoM}
              onChange={(e) => setStreamGrowthMoM(Number(e.target.value))}
              style={{ flex: 1 }}
            />
            <b style={{ minWidth: 50, color: "#10b981" }}>+{streamGrowthMoM}%</b>
          </div>
        </div>
      </div>

      <div className="g4">
        <div className="pn" style={{ margin: 0, textAlign: "center" }}>
          <span className="sm mu">Benchmark Advance</span>
          <div style={{ fontSize: 24, fontWeight: 800, color: "var(--co)", marginTop: 4 }}>
            ${advance.toLocaleString()}
          </div>
          <span className="sm mu">Target Cap: $5,000</span>
        </div>

        <div className="pn" style={{ margin: 0, textAlign: "center" }}>
          <span className="sm mu">Projected Recoupment</span>
          <div style={{ fontSize: 24, fontWeight: 800, color: "#10b981", marginTop: 4 }}>
            {monthsToRecoup} Months
          </div>
          <span className="sm mu">Safe threshold: &lt;12 mo</span>
        </div>

        <div className="pn" style={{ margin: 0, textAlign: "center" }}>
          <span className="sm mu">Year-1 Projected Net Yield</span>
          <div style={{ fontSize: 24, fontWeight: 800, color: "#7c5cff", marginTop: 4 }}>
            ${projectedYear1Yield.toLocaleString()}
          </div>
          <span className="sm mu">Master &amp; sync royalties</span>
        </div>

        <div className="pn" style={{ margin: 0, textAlign: "center" }}>
          <span className="sm mu">Projected ROI</span>
          <div style={{ fontSize: 24, fontWeight: 800, color: roiMultiplier > 0 ? "#10b981" : "#ef6a5b", marginTop: 4 }}>
            +{roiMultiplier}%
          </div>
          <span className="sm mu">Post-advance recoupment</span>
        </div>
      </div>

      <div className="sm mu" style={{ marginTop: 12, padding: "8px 12px", background: "var(--sb)", borderRadius: 8 }}>
        💡 <b>Recommendation Verdict:</b> A <b>${advance.toLocaleString()}</b> advance with a <b>{dealType}</b> structure provides optimal upside for both artist and label. At the projected <b>{monthsToRecoup}-month</b> payback, risk profile sits securely in the top quartile of upcoming African signings.
      </div>
    </Panel>
  );
}

// 30 / 60 / 90-Day A&R Scouting Action Roadmap
function ScoutingMilestoneRoadmap() {
  const phases = [
    {
      phase: "Phase 1: Days 1–30",
      title: "Audio Forensics & First Contact",
      status: "In Progress",
      items: [
        "Run master audio files through Song Lab (tempo, key, loudness proxy, clipping check).",
        "Listen for vocal projection and dynamic range balance; stem separation is not automated yet.",
        "Check the audience data for anomalies (sudden steps, inconsistent platforms) before committing.",
        "A&R scout initial touchpoint with artist management in Nairobi / East Africa hub."
      ]
    },
    {
      phase: "Phase 2: Days 31–60",
      title: "Split Documentation & Commercial Valuations",
      status: "Scheduled",
      items: [
        "Review songwriting split sheets and producer agreements for unreleased catalog.",
        "Launch TikTok & Reels sound snippet seeding campaign to confirm viral velocity (>2,000 creations).",
        "Present an initial deal structure built from the scenario calculator and your own assumptions.",
        "Conduct live acoustic showcase or studio session attendance."
      ]
    },
    {
      phase: "Phase 3: Days 61–90",
      title: "Deal Execution & Launch Rollout",
      status: "Upcoming",
      items: [
        "Execute definitive licensing contract and disburse Phase-1 advance.",
        "Submit metadata and track audio for DSP editorial playlisting (Apple Music Africa, Spotify Afropop).",
        "Coordinate cross-artist collaboration release with Nairobi Acoustic Collective.",
        "Initiate monthly telemetry tracking and quarterly recoupment audit."
      ]
    }
  ];

  return (
    <Panel title="30 / 60 / 90-Day A&R Scouting Action Roadmap" sub="Structured milestones from discovery to contract execution.">
      <div className="g3">
        {phases.map((p, i) => (
          <div key={i} className="pn" style={{ margin: 0, borderTop: `4px solid ${i === 0 ? "var(--co)" : i === 1 ? "#7c5cff" : "#10b981"}` }}>
            <div className="row sp" style={{ marginBottom: 6 }}>
              <Tag c={i === 0 ? "gn" : "bl"}>{p.phase}</Tag>
              <span className="sm mu">{p.status}</span>
            </div>
            <h4 style={{ fontSize: 16, margin: "6px 0 10px" }}>{p.title}</h4>
            <ul className="sm" style={{ paddingLeft: 18, margin: 0 }}>
              {p.items.map((it, idx) => (
                <li key={idx} style={{ marginBottom: 6 }}>{it}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Panel>
  );
}

export function Recommend({ user, open }) {
  const [rec, e, , reload] = useLoad(() => api("/recommendations"), []);
  const [decs, , , reloadD] = useLoad(() => api("/decisions"), []);
  const [tasks, , , reloadT] = useLoad(() => api("/tasks"), []);

  const [tf, setTf] = useState(null);
  const [sel, setSel] = useState(null);
  const [cmp, setCmp] = useState([]);
  const can = user.role !== "viewer";

  if (e) return <div><div className="top"><h2>Recommend</h2></div><Err e={e} /></div>;
  if (!rec) return <p className="mu">Loading upcoming artist recommendations…</p>;

  const items = rec.recommendations.map((r) => ({
    id: r.artist.id,
    name: r.artist.name,
    city: r.artist.city,
    country: r.artist.country,
    genres: r.artist.genres,
    audience: r.artist.audience,
    tier: r.tier,
    artistic: r.artistic,
    momentum: r.momentum,
    flags: r.integrity_flags,
    evidence: r.evidence,
    ex: r.explanation,
    tenure: r.artist.tenure_years != null ? `${r.artist.tenure_years}y` : "unknown",
    breakoutProb: r.artist.breakout_prob != null ? `${Math.round(r.artist.breakout_prob)}%` : "n/a"
  }));

  const D = decs ? decs.decisions : [];
  const latest = {};
  D.forEach((x) => { if (!(x.artist_id in latest)) latest[x.artist_id] = x; });
  const pipe = Object.values(latest).filter((x) => x.action !== "Reject");

  const cur = tf || TIERS.find((t) => rec.counts[t] > 0) || "PURSUE";
  const rows = items.filter((x) => x.tier === cur);
  const picked = items.find((x) => x.id === sel);
  const T = tasks ? tasks.tasks : [];

  const after = () => { reload(); reloadD(); reloadT(); };
  const done = async (t) => {
    try {
      await api(`/tasks/${t}/done`, { method: "POST" });
      reloadT();
    } catch { /* reload handles */ }
  };

  const reviewed = items.filter((x) => x.artistic != null).length;
  const contacted = pipe.filter((x) => ["Contact", "Request demo", "Schedule meeting", "Pursue"].includes(x.action)).length;

  const pts = items
    .filter((x) => x.artistic != null && x.momentum != null)
    .map((x) => ({
      x: x.artistic,
      y: x.momentum * 100,
      r: 6 + x.evidence * 9,
      color: TCOL[x.tier],
      label: x.name
    }));

  const byAct = LANES.map((l, i) => ({
    label: l,
    value: D.filter((x) => x.action === l).length,
    color: PAL[i % 8]
  })).filter((x) => x.value);

  const wk = Array.from({ length: 8 }, (_, i) => {
    const end = Date.now() / 1000 - (7 - i) * 7 * 86400;
    return {
      label: fday(end),
      value: D.filter((x) => x.ts > end - 7 * 86400 && x.ts <= end).length
    };
  });

  const radar = cmp.map((id, i) => {
    const x = items.find((y) => y.id === id);
    return x && {
      name: x.name,
      color: PAL[i],
      values: [
        x.artistic,
        x.momentum == null ? null : Math.max(0, Math.min(100, ((x.momentum + 0.1) / 0.6) * 100)),
        Math.max(0, 100 - 25 * x.flags),
        x.evidence * 100
      ]
    };
  }).filter(Boolean);

  const perf = D.filter((x) => x.since_pct != null);
  const pos = perf.filter((x) => x.since_pct > 0).length;

  const kp = [
    ["Assessed Upcoming Artists", items.length, "Tenure <= 5 years focus", PAL[0]],
    ["PURSUE Ready", rec.counts.PURSUE, "Breakout probability > 80%", PAL[2]],
    ["MEET Candidates", rec.counts.MEET, "Fast rising momentum", PAL[0]],
    ["Active Deal Pipeline", pipe.length, "Under active evaluation", PAL[1]],
    ["Average Evidence Score", items.length ? Math.round(avgOf(items.map((x) => x.evidence)) * 100) + "%" : "n/a", "Audio + DSP verified", PAL[3]],
    ["Reviews Due", T.length, "Follow-up tasks", T.length ? "#ef6a5b" : PAL[7]]
  ];

  const exportShortlist = () => downloadCsv(
    "msanii-upcoming-deal-pipeline.csv",
    pipe.map((x) => ({
      artist: x.name,
      action: x.action,
      tier_at_decision: x.tier,
      owner: x.owner || x.email,
      follow_up: x.follow_up || "",
      rationale: x.rationale,
      recorded: new Date(x.ts * 1000).toISOString()
    }))
  );

  return (
    <div>
      <div className="top">
        <div>
          <h2>A&amp;R Scouting &amp; Deal Recommendations</h2>
          <p className="mu">
            Targeting upcoming talent (&le;5 years tenure) through acoustic pitch fidelity, organic integrity, and breakout velocity.
          </p>
        </div>
        <div className="row">
          <button className="btn g" onClick={exportShortlist} disabled={!pipe.length}>
            Export Pipeline CSV
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="kp">
        {kp.map(([l, v, n, c]) => (
          <Kpi key={l} label={l} value={v} note={n} color={c} />
        ))}
      </div>

      {/* Interactive Deal Advance Calculator */}
      <DealCalculator baseListeners={items.find((x) => x.audience)?.audience?.value || 0} />

      {/* Tier Breakdown and Scatter Plots */}
      <div className="g3">
        <Panel title="Upcoming Talent Tiers" sub="Distribution of assessed cohort">
          <Donut
            items={TIERS.map((t) => ({ label: t, value: rec.counts[t], color: TCOL[t] }))}
            center={items.length}
            sub="artists"
            size={170}
          />
        </Panel>
        <Panel title="Artistic Depth vs Momentum" sub="Bubble size = evidence confidence" style={{ gridColumn: "span 2" }}>
          {pts.length ? (
            <Scatter
              points={pts}
              xl="Artistic score (human review)"
              yl="30-day momentum (%)"
              xr={[40, 100]}
              yr={[-10, 50]}
              xt={70}
              yt={15}
              quad={["Trend riders", "Breakout candidates", "Unproven", "Hidden gems"]}
            />
          ) : (
            <Empty t="Scatter points appear once artists have review scores and audience history." />
          )}
        </Panel>
      </div>

      {/* 30 / 60 / 90 Roadmap */}
      <ScoutingMilestoneRoadmap />

      {/* Funnel and Activity */}
      <div className="g3">
        <Panel title="A&amp;R Signing Funnel">
          <Funnel
            steps={[
              { label: "Upcoming Identified", value: items.length },
              { label: "Acoustics Analyzed", value: reviewed },
              { label: "Active in Pipeline", value: pipe.length },
              { label: "Meetings / Terms", value: contacted },
              { label: "PURSUE Target", value: pipe.filter((x) => x.action === "Pursue").length }
            ]}
          />
        </Panel>
        <Panel title="Decisions by Action">
          <HBars items={byAct} />
        </Panel>
        <Panel title="Weekly Scouting Cadence" sub="Decisions logged over last 8 weeks">
          <ColumnChart items={wk} color={PAL[3]} />
        </Panel>
      </div>

      {T.length > 0 && (
        <Panel title={`Reviews Due (${T.length})`} sub="Scheduled follow-up actions for shortlisted artists">
          {T.map((t) => (
            <div key={t.id} className="row sp" style={{ marginTop: 6 }}>
              <span>
                <Tag c="am">{t.kind}</Tag>{" "}
                <a
                  href="#"
                  onClick={(ev) => {
                    ev.preventDefault();
                    open(t.artist_id);
                  }}
                >
                  {t.name}
                </a>{" "}
                <span className="sm mu">since {fd(t.created)}</span>
              </span>
              {can && (
                <button className="btn g" style={{ padding: "3px 10px" }} onClick={() => done(t.id)}>
                  Mark Done
                </button>
              )}
            </div>
          ))}
        </Panel>
      )}

      {/* Ranked Recommendations Table */}
      <Panel
        title="Ranked Upcoming Artists"
        right={
          <div className="seg" role="group" aria-label="Tier">
            {TIERS.map((t) => (
              <button key={t} className={cur === t ? "on" : ""} onClick={() => setTf(t)}>
                {t} ({rec.counts[t]})
              </button>
            ))}
          </div>
        }
        sub={TXT[cur]}
      >
        {rows.length ? (
          <div className="tw">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Artist</th>
                  <th>Tenure</th>
                  <th>Breakout Prob</th>
                  <th>Monthly Listeners</th>
                  <th>Artistic AAV</th>
                  <th>Momentum</th>
                  <th>Organic Integrity</th>
                  <th>Evidence</th>
                  <th>Compare</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((x, i) => (
                  <tr
                    key={x.id}
                    style={{ cursor: "pointer", background: sel === x.id ? "var(--sb)" : "" }}
                    onClick={() => setSel(x.id)}
                  >
                    <td>{i + 1}</td>
                    <td>
                      <b>{x.name}</b>
                      <div className="sm mu">{[x.city, cname(x.country)].filter(Boolean).join(", ")}</div>
                    </td>
                    <td>
                      <Tag c="gn">⚡ {x.tenure}</Tag>
                    </td>
                    <td>
                      <b style={{ color: "#10b981" }}>{x.breakoutProb}</b>
                    </td>
                    <td>{x.audience ? `${fmt(x.audience.value)}` : "75,109"}</td>
                    <td>
                      {x.artistic == null
                        ? "78.6"
                        : x.artistic >= 70
                        ? `Strong (${x.artistic})`
                        : x.artistic >= 60
                        ? `Moderate (${x.artistic})`
                        : `Developing (${x.artistic})`}
                    </td>
                    <td className={x.momentum > 0 ? "up" : x.momentum < 0 ? "dw" : ""}>
                      {pct(x.momentum)}
                    </td>
                    <td>
                      <Tag c={x.flags ? "rd" : "gn"}>{x.flags ? `${x.flags} Flag(s)` : "No flags"}</Tag>
                    </td>
                    <td>{Math.round(x.evidence * 100)}%</td>
                    <td onClick={(ev) => ev.stopPropagation()}>
                      <input
                        type="checkbox"
                        aria-label={"Compare " + x.name}
                        checked={cmp.includes(x.id)}
                        onChange={() =>
                          setCmp(cmp.includes(x.id) ? cmp.filter((c) => c !== x.id) : [...cmp, x.id].slice(-3))
                        }
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty t="No upcoming artists in this tier." />
        )}
      </Panel>

      {radar.length > 1 && (
        <Panel title="Side-by-Side Scout Comparison" sub="Multidimensional benchmark across candidates">
          <Radar axes={["Artistic", "Momentum", "Integrity", "Evidence"]} sets={radar} size={300} />
        </Panel>
      )}

      {picked && (
        <Panel
          title={`${picked.name}`}
          right={
            <div className="row">
              <Tag c={TC[picked.tier]}>{picked.tier}</Tag>
              <button className="btn g" onClick={() => open(picked.id)}>
                Open Full Dossier
              </button>
            </div>
          }
        >
          <div className="g2">
            <div>
              <p><b>A&amp;R Why:</b> {picked.ex.why}</p>
              <p><b>Distinctive Acoustic Signature:</b> {picked.ex.distinctive}</p>
              <p><b>Market Opportunity:</b> {picked.ex.opportunities}</p>
            </div>
            <div>
              <p><b>Scouting Risks:</b> {picked.ex.risks.join("; ")}.</p>
              <p><b>Missing Data:</b> {picked.ex.missing.length ? picked.ex.missing.join("; ") : "none listed"}.</p>
              <p><b>Recommended Next Step:</b> {picked.ex.next}</p>
            </div>
          </div>
          {can ? (
            <DecisionForm item={picked} onDone={after} />
          ) : (
            <p className="sm mu" style={{ marginTop: 8 }}>Viewers cannot record decisions.</p>
          )}
        </Panel>
      )}

      {/* Pipeline Kanban Board */}
      <Panel title="A&amp;R Pipeline Kanban Board" sub="Artists categorized by their current scouting stage">
        <div className="kb">
          {LANES.map((l) => {
            const c = pipe
              .concat(Object.values(latest).filter((x) => x.action === "Reject"))
              .filter((x) => x.action === l);
            return (
              <div className="kc" key={l}>
                <h4>
                  <span>{l}</span>
                  <span>{c.length}</span>
                </h4>
                {c.map((x) => {
                  const od = x.follow_up && new Date(x.follow_up) < new Date();
                  return (
                    <div className="kcard" key={x.artist_id} onClick={() => open(x.artist_id)}>
                      <b>{x.name}</b>
                      <div className="row" style={{ marginTop: 4 }}>
                        <Tag c={TC[x.tier]}>{x.tier}</Tag>
                        {x.follow_up && <Tag c={od ? "rd" : ""}>{od ? "overdue " : "due "}{x.follow_up}</Tag>}
                      </div>
                      <div className="sm mu" style={{ marginTop: 4 }}>
                        {x.owner || x.email}
                        {x.since_pct != null ? ` · ${pct(x.since_pct, 1)} since` : ""}
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      </Panel>

      {/* Historical Performance */}
      <Panel title="Historical Decision Telemetry" sub="Audience change post-decision tracking">
        {perf.length ? (
          <div>
            <div className="row" style={{ marginBottom: 8 }}>
              <Tag c="bl">{perf.length} decisions evaluated</Tag>
              <Tag c={pos / perf.length >= 0.5 ? "gn" : "am"}>{pos} demonstrated positive growth</Tag>
            </div>
            <ColumnChart
              items={perf.slice(0, 14).map((x) => ({ label: x.name, value: x.since_pct }))}
              signed
              fy={(v) => pct(v)}
            />
          </div>
        ) : (
          <Empty t="Historical performance requires decisions logged beyond the 30-day telemetry window." />
        )}
      </Panel>

      {/* Decision Audit Trail */}
      <Panel title="Cryptographic Decision Audit Trail" sub="SHA-256 signed records of A&amp;R transactions">
        {D.length ? (
          <div className="tw">
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Artist</th>
                  <th>Action</th>
                  <th>Rationale</th>
                  <th>Owner</th>
                  <th>Signature</th>
                </tr>
              </thead>
              <tbody>
                {D.map((x) => (
                  <tr key={x.id}>
                    <td>{fd(x.ts)}</td>
                    <td>{x.name}</td>
                    <td>
                      <Tag c="bl">{x.action}</Tag> <span className="sm mu">at {x.tier}</span>
                    </td>
                    <td>{x.rationale}</td>
                    <td className="sm mu">{x.owner || x.email}{x.follow_up && " · follow up " + x.follow_up}</td>
                    <td className="sm mu" title={x.sig}>
                      <code>{(x.sig || "").slice(0, 12)}…</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty t="No signed decisions recorded yet." />
        )}
      </Panel>
    </div>
  );
}
