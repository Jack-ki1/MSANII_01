// Views for REAL artists: only measured / recorded data, with its source. Where data is missing the view says so.
// Demo artists keep the illustrative sample dashboards (see SampleBanner in analyze2.jsx).
import { Tag } from "./ui";
import { Panel, Kpi, fd, fday } from "./shared";
import { LineChart, fmt, PAL } from "./charts";

const statusTag = (s) => (s === "Observed" || s === "Human" ? "gn" : "am");

function ObservedKpis({ items }) {
  if (!items?.length) return <p className="mu">No observations yet. Run discovery or import audience data, then add a human review. Nothing is estimated in the meantime.</p>;
  return (
    <div className="kp">
      {items.map((k) => (
        <Kpi key={k.key} label={k.label} value={k.value} note={<>{k.note} <Tag c={statusTag(k.status)}>{k.status}</Tag></>} color={PAL[0]} />
      ))}
    </div>
  );
}

function Forecast({ rows }) {
  if (!rows?.length) return <p className="mu">No forecast: it needs at least 4 observations spanning 7+ days of the same audience metric.</p>;
  return (
    <table className="tb">
      <thead><tr><th>Horizon</th><th>Expected</th><th>95% prediction interval</th></tr></thead>
      <tbody>{rows.map((r) => <tr key={r.days}><td>{r.days} days</td><td>{fmt(r.expected)}</td><td>{fmt(r.lower)} to {fmt(r.upper)}</td></tr>)}</tbody>
    </table>
  );
}

function Valuation({ v }) {
  if (!v) return <p className="mu">Needs an observed audience size.</p>;
  return (
    <div>
      <div className="row" style={{ gap: 24 }}>
        <div><div className="sm mu">Advance scenario</div><div className="big">{v.formatted_advance}</div></div>
        <div><div className="sm mu">Months to recoup</div><div className="big">{v.recoupment_months}</div></div>
      </div>
      <p className="sm mu" style={{ marginTop: 8 }}>A scenario calculator, not a valuation. Change the assumptions before relying on it:</p>
      <ul className="sm" style={{ paddingLeft: 18 }}>
        <li>Plays per listener per month: {v.assumptions.plays_per_listener_month} (assumed)</li>
        <li>Payout per stream: ${v.assumptions.payout_per_stream_usd} (assumed)</li>
        <li>Label share of 12-month gross: {Math.round(v.assumptions.label_share * 100)}% (assumed)</li>
        <li>Catalog factor {v.assumptions.catalog_factor}, growth factor {v.assumptions.growth_factor}, risk factor {v.assumptions.risk_factor}</li>
      </ul>
    </div>
  );
}

export function RealDossier({ d, openSongLab }) {
  const an = d.acoustic_analytics || {}, A = d.assessment, ex = d.explanation || {};
  return (
    <div>
      <div className="bn">Every figure below comes from a recorded observation or a human review. Heuristic and scenario outputs are labelled as such.</div>
      <Panel title="What we know" sub="Latest observed values, with their source">
        <ObservedKpis items={an.observed} />
      </Panel>
      <div className="g2">
        <Panel title={`Recommendation: ${A.tier}`} sub={`Evidence confidence ${Math.round(A.evidence * 100)}%`}>
          <p>{ex.why}</p>
          {ex.missing?.length ? <><b className="sm">Still missing</b><ul className="sm">{ex.missing.map((m) => <li key={m}>{m}</li>)}</ul></> : null}
          <b className="sm">Risks and flags</b><ul className="sm">{(ex.risks || []).map((m) => <li key={m}>{m}</li>)}</ul>
          {ex.next ? <p className="sm"><b>Next step:</b> {ex.next}</p> : null}
        </Panel>
        <Panel title="Audience trajectory" sub="Log-linear trend with a 95% prediction interval"><Forecast rows={an.forecast} /></Panel>
      </div>
      <div className="g2">
        <Panel title="Advance scenario"><Valuation v={an.ar_valuation} /></Panel>
        <Panel title="Audio">
          {d.measurements?.length
            ? <ul className="sm">{d.measurements.slice(0, 6).map((m, i) => <li key={i}>{m.name}: <b>{m.value}</b> (confidence {Math.round(m.confidence * 100)}%, {m.provenance?.method})</li>)}</ul>
            : <p className="mu">No audio analysed yet.</p>}
          {openSongLab && <button className="btn" onClick={openSongLab}>Open Song Lab</button>}
        </Panel>
      </div>
    </div>
  );
}

export function RealAnalytics({ d }) {
  const an = d.acoustic_analytics || {}, org = an.organic || {}, main = d.assessment?.metric, ser = (d.series?.[main] || []);
  return (
    <div>
      <div className="bn">Advanced acoustic views (pitch accuracy, vocal range, stem occupancy, collaboration network) are not computed for real artists yet, and are never filled in with sample values. What follows is measured or recorded.</div>
      <Panel title="Audience history" sub={main ? `${main}, observed` : "no audience metric observed yet"}>
        {ser.length > 1 ? <LineChart series={[{ name: main, data: ser.map((p) => p[1]) }]} labels={ser.map((p) => fday(p[0]))} /> : <p className="mu">Needs at least two observations.</p>}
      </Panel>
      <div className="g2">
        <Panel title="Plays per listener (Last.fm)" sub="Heuristic corridor, a prompt to look closer, never a verdict">
          {org.ratio == null ? <p className="mu">{org.note || "Insufficient data."}</p> : <p><span className="big">{org.ratio}</span> <Tag c={org.is_safe ? "gn" : "am"}>{org.status_label}</Tag></p>}
        </Panel>
        <Panel title="Measured audio" sub="From uploaded, rights-cleared audio">
          {d.measurements?.length
            ? <table className="tb"><thead><tr><th>Measure</th><th>Value</th><th>Confidence</th><th>When</th></tr></thead><tbody>{d.measurements.map((m, i) => <tr key={i}><td>{m.name}</td><td>{m.value}</td><td>{Math.round(m.confidence * 100)}%</td><td>{fd(m.ts)}</td></tr>)}</tbody></table>
            : <p className="mu">Nothing measured yet. Upload audio in Song Lab.</p>}
        </Panel>
      </div>
    </div>
  );
}
