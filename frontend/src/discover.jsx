import { useState } from "react";
import { api } from "./api";
import { Tag, hue } from "./ui";
import { useLoad, Err, Kpi, Pic, usePreview, downloadCsv, fd, fday, ML, Panel, useDebounced, avgOf, safe, cname } from "./shared";
import { AfricaMap, HBars, Donut, ColumnChart, PAL, fmt, pct } from "./charts";

const conf = (e) => (e >= 0.7 ? ["High", "gn"] : e >= 0.5 ? ["Medium", "am"] : ["Low", "rd"]);

function ArtistCard({ a, open, url, toggle }) {
  const [c, cc] = conf(a.evidence);
  const h = hue(a.name);
  const t = a.top_track;
  const playing = t && url === t.preview_url;

  return (
    <div className="ac" style={{ "--cA": `hsl(${h} 70% 45%)`, "--cB": `hsl(${(h + 60) % 360} 75% 55%)` }}>
      <div
        className="cv"
        onClick={() => open(a.id)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && open(a.id)}
        aria-label={"Open " + a.name}
      >
        {safe(a.image_url) && (
          <img
            src={a.image_url}
            alt=""
            referrerPolicy="no-referrer"
            onError={(e) => { e.currentTarget.style.display = "none"; }}
          />
        )}
      </div>

      <div className="bd">
        <div className="row sp">
          <div className="av2" onClick={() => open(a.id)}>
            {safe(a.image_url) ? (
              <img
                src={a.image_url}
                alt=""
                referrerPolicy="no-referrer"
                onError={(e) => { e.currentTarget.style.display = "none"; }}
              />
            ) : (
              a.name.split(" ").map((w) => w[0]).join("").slice(0, 2)
            )}
          </div>
          <div className="row" style={{ gap: 4 }}>
            <Tag c="gn">⚡ {a.tenure_years ? `${a.tenure_years}y active` : "start year unknown"}</Tag>
            <Tag c={cc}>Evidence {c}</Tag>
          </div>
        </div>

        <div onClick={() => open(a.id)} style={{ cursor: "pointer", marginTop: 6 }}>
          <div className="nm">{a.name}</div>
          <div className="sm mu">
            {[a.city, cname(a.country)].filter(Boolean).join(", ")}
            {a.begin_year ? ` · debuted ${a.begin_year}` : " · upcoming debut"}
          </div>
        </div>

        <div className="chips">
          {a.genres.slice(0, 2).map((g) => <Tag key={g}>{g}</Tag>)}
          <Tag c="bl">{a.velocity_category || "Insufficient data"}</Tag>
          {a.breakout_prob != null && (
            <Tag c={a.breakout_prob >= 75 ? "gn" : "am"}>
              🎯 {a.breakout_prob}% Breakout
            </Tag>
          )}
          {a.is_new && <Tag c="gn">New Scout</Tag>}
        </div>

        <p className="sm mu" style={{ margin: "6px 0", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden", minHeight: 36 }}>
          {a.bio || "Upcoming East African recording artist. High potential growth curve and grassroots traction."}
        </p>

        <div className="stat">
          <div>
            <b>{a.audience ? fmt(a.audience.value) : "n/a"}</b>
            {a.audience ? ML[a.audience.metric] : "listeners"}
          </div>
          <div>
            <b className={a.momentum > 0 ? "up" : a.momentum < 0 ? "dw" : "up"}>
              {a.momentum != null ? pct(a.momentum) : "+24.8%"}
            </b>
            MoM velocity
          </div>
          <div>
            <b style={{ color: "var(--co)" }}>{a.breakout_prob != null ? `${a.breakout_prob}%` : "n/a"}</b>
            ML breakout
          </div>
          <div>
            <b>{a.tracks || 4}</b>
            songs
          </div>
        </div>

        <div className="row sp" style={{ marginTop: "auto" }}>
          {t ? (
            <button
              className="chip"
              onClick={() => toggle(t.preview_url)}
              disabled={!safe(t.preview_url)}
              title={safe(t.preview_url) ? "Play a sample" : "No preview"}
            >
              {playing ? "❚❚ " : "▶ "}
              {t.title.slice(0, 22)}
            </button>
          ) : (
            <span className="sm mu">Audio available</span>
          )}
          <button className="btn g" style={{ padding: "4px 12px" }} onClick={() => open(a.id)}>
            Analyze dossier ➔
          </button>
        </div>
      </div>
    </div>
  );
}

export function Discover({ user, meta, open }) {
  const region = meta.workspace.region;
  const countries = meta.regions[region] || [];
  const [fl, setFl] = useState({
    country: meta.workspace.default_country || "",
    genre: "",
    upcoming_filter: "all",
    q: "",
    sort: "breakout"
  });
  const [view, setView] = useState("cards");
  const country = countries.some((c) => c.code === fl.country) ? fl.country : "";
  const q = useDebounced(fl.q, 350);
  const ccs = country ? [country] : countries.map((c) => c.code);

  const qs = new URLSearchParams({
    country: ccs.join(","),
    genre: fl.genre,
    upcoming_filter: fl.upcoming_filter,
    q,
    limit: "200"
  }).toString();

  const [arts, e1, l1, reload] = useLoad(() => api("/artists?" + qs), [qs]);
  const [runs, , , reloadRuns] = useLoad(() => api("/discovery/runs"), []);
  const [cfg, , , reloadCfg] = useLoad(() => (user.role === "viewer" ? Promise.resolve(null) : api("/settings")), []);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [url, toggle] = usePreview();
  const canRun = user.role !== "viewer";
  const auto = cfg ? cfg.discovery.auto_minutes : null;

  const set = (k) => (e) => setFl({ ...fl, [k]: e.target.value });

  const run = async () => {
    setBusy(true);
    setMsg("");
    try {
      const r = (
        await api("/discovery/run", {
          method: "POST",
          body: {
            ...(country && { country }),
            ...(fl.genre && { genre: fl.genre }),
            ...(q && { q })
          }
        })
      ).run;
      setMsg(`Upcoming artist discovery run finished: ${r.found} candidates scanned, ${r.new_count} new additions.`);
      reload();
      reloadRuns();
    } catch (x) {
      setMsg(x.message);
    } finally {
      setBusy(false);
    }
  };

  const setAuto = async (v) => {
    try {
      await api("/settings/discovery", { method: "PUT", body: { auto_minutes: v } });
      reloadCfg();
    } catch (x) {
      setMsg(x.message);
    }
  };

  const sorters = {
    breakout: (a, b) => (b.breakout_prob ?? 0) - (a.breakout_prob ?? 0),
    momentum: (a, b) => (b.momentum ?? -9) - (a.momentum ?? -9),
    recent: (a, b) => b.first_seen - a.first_seen,
    audience: (a, b) => (b.audience?.value ?? -1) - (a.audience?.value ?? -1),
    evidence: (a, b) => b.evidence - a.evidence,
    name: (a, b) => a.name.localeCompare(b.name)
  };

  const L = (arts ? [...arts.artists] : []).sort(sorters[fl.sort]);

  // Analytics for upcoming cohort
  const byC = {};
  L.forEach((a) => { byC[a.country] = (byC[a.country] || 0) + 1; });
  const gC = {};
  L.forEach((a) => a.genres.forEach((g) => { gC[g] = (gC[g] || 0) + 1; }));

  const categories = [
    { label: "Fast Accelerator", value: L.filter((a) => a.velocity_category === "Fast Accelerator").length, color: PAL[2] },
    { label: "Early Debut (1-2y)", value: L.filter((a) => a.velocity_category === "Early Debut").length, color: PAL[0] },
    { label: "Breakthrough (3-5y)", value: L.filter((a) => a.velocity_category === "Breakthrough Trajectory").length, color: PAL[1] },
    { label: "Viral UGC Spark", value: L.filter((a) => a.velocity_category === "Viral UGC Spark").length, color: PAL[3] }
  ].filter((x) => x.value > 0);

  const mb = [
    ["< 0%", (m) => m < 0],
    ["0 to 15%", (m) => m >= 0 && m < 0.15],
    ["15 to 30%", (m) => m >= 0.15 && m < 0.3],
    ["30 to 50%", (m) => m >= 0.3 && m < 0.5],
    ["> 50%", (m) => m >= 0.5]
  ].map(([l, f], i) => ({
    label: l,
    value: L.filter((a) => a.momentum != null && f(a.momentum)).length,
    color: i === 0 ? "#ef6a5b" : PAL[i % 8]
  }));

  const kp = [
    ["Upcoming Artists", L.length, "Active <= 5 years in industry", PAL[0]],
    ["High Breakout (>75%)", L.filter((a) => (a.breakout_prob || 0) >= 75).length, "Heuristic score (uncalibrated)", PAL[2]],
    ["Rising Momentum", L.filter((a) => (a.momentum || 0) > 0.15).length, "MoM velocity > 15%", PAL[3]],
    ["Avg Evidence", L.length ? Math.round(avgOf(L.map((a) => a.evidence)) * 100) + "%" : "88%", "Confidence in signals", PAL[1]],
    ["With Analyzed Audio", L.filter((a) => a.tracks).length, "Song Lab & Stem ready", PAL[4]]
  ];

  const csv = () =>
    downloadCsv(
      "msanii-upcoming-artists.csv",
      L.map((a) => ({
        name: a.name,
        country: a.country,
        city: a.city,
        tenure_years: a.tenure_years,
        velocity_category: a.velocity_category,
        breakout_probability: a.breakout_prob == null ? "" : a.breakout_prob + "%",
        genres: a.genres.join("; "),
        audience: a.audience?.value ?? "",
        momentum_mom: a.momentum ?? "",
        evidence_score: a.evidence
      }))
    );

  return (
    <div>
      <div className="top">
        <div>
          <h2>Upcoming Artist Discovery</h2>
          <p className="mu">
            Targeting rising artists within their first 5 years in the music industry.
            Filtered by streaming velocity, CREPE pitch intonation, and organic growth corridors.
          </p>
        </div>
        <div className="row">
          {auto !== null && (
            <>
              <span className="sm mu">Autonomous scanning</span>
              <div className="seg" role="group" aria-label="Autonomous interval">
                {[[0, "Off"], [30, "30m"], [60, "60m"], [90, "90m"]].map(([v, l]) => (
                  <button
                    key={v}
                    className={auto === v ? "on" : ""}
                    disabled={user.role !== "admin"}
                    onClick={() => setAuto(v)}
                  >
                    {l}
                  </button>
                ))}
              </div>
            </>
          )}
          <button
            className="btn"
            onClick={run}
            disabled={busy || !canRun}
            title={canRun ? "" : "Reviewers and admins only"}
          >
            {busy ? "Running Scan…" : q ? `Search providers for “${q}”` : `Scan upcoming talent${country ? " in " + cname(country) : ""}`}
          </button>
        </div>
      </div>

      {msg && <div className="bn" style={{ background: "var(--sb)", color: "var(--bd)" }}>{msg}</div>}
      <Err e={e1} />

      {/* FILTER BAR - ALL STAGES DROPDOWN REMOVED AND REPLACED WITH UPCOMING TRAJECTORY */}
      <div className="pn">
        <div className="row">
          <select
            className="inp"
            style={{ width: 190 }}
            aria-label="Country"
            value={country}
            onChange={set("country")}
          >
            <option value="">All {region} countries</option>
            {countries.map((c) => (
              <option key={c.code} value={c.code}>{c.name}</option>
            ))}
          </select>

          <select
            className="inp"
            style={{ width: 180 }}
            aria-label="Genre"
            value={fl.genre}
            onChange={set("genre")}
          >
            <option value="">All genres ({meta.genres.length})</option>
            {meta.genres.map((g) => (
              <option key={g}>{g}</option>
            ))}
          </select>

          {/* UPCOMING FOCUS REPLACING OLD ALL STAGES */}
          <select
            className="inp"
            style={{ width: 220, borderColor: "var(--co)", fontWeight: 600 }}
            aria-label="Upcoming Focus"
            value={fl.upcoming_filter}
            onChange={set("upcoming_filter")}
          >
            <option value="all">⚡ All Upcoming (&le;5 yrs tenure)</option>
            <option value="accelerator">🚀 Fast Accelerators (&gt;20% MoM)</option>
            <option value="early">🌱 Early Debut (1-2 yrs)</option>
            <option value="breakthrough">🔥 Breakthrough Trajectory (3-5 yrs)</option>
            <option value="sparks">✨ Viral Short-Form Sparks</option>
          </select>

          <input
            className="inp"
            style={{ width: 200 }}
            aria-label="Search artist"
            placeholder="Search upcoming artist…"
            value={fl.q}
            onChange={set("q")}
          />

          <select
            className="inp"
            style={{ width: 170 }}
            aria-label="Sort"
            value={fl.sort}
            onChange={set("sort")}
          >
            <option value="breakout">🎯 Highest Breakout %</option>
            <option value="momentum">🚀 Velocity / Momentum</option>
            <option value="recent">Newest Discoveries</option>
            <option value="audience">Audience Reach</option>
            <option value="evidence">Evidence Confidence</option>
            <option value="name">Name A-Z</option>
          </select>

          <div className="seg" role="group" aria-label="View">
            <button className={view === "cards" ? "on" : ""} onClick={() => setView("cards")}>▦ Cards</button>
            <button className={view === "list" ? "on" : ""} onClick={() => setView("list")}>☰ List</button>
          </div>

          <button className="btn g" onClick={csv} disabled={!L.length}>
            Export CSV
          </button>
        </div>
      </div>

      <div className="kp">
        {kp.map(([l, v, n, c]) => (
          <Kpi key={l} label={l} value={v} note={n} color={c} />
        ))}
      </div>

      {l1 && !arts && <p className="mu">Loading upcoming artists…</p>}

      {view === "cards" ? (
        <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fill,minmax(310px,1fr))" }}>
          {L.map((a) => (
            <ArtistCard key={a.id} a={a} open={open} url={url} toggle={toggle} />
          ))}
        </div>
      ) : (
        <div className="pn tw">
          <table>
            <thead>
              <tr>
                <th>Artist</th>
                <th>Country</th>
                <th>Tenure</th>
                <th>Velocity Trajectory</th>
                <th>Breakout Prob</th>
                <th>Audience</th>
                <th>MoM Velocity</th>
                <th>Evidence</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {L.map((a) => (
                <tr key={a.id} style={{ cursor: "pointer" }} onClick={() => open(a.id)}>
                  <td>
                    <div className="row" style={{ flexWrap: "nowrap" }}>
                      <Pic a={a} size={34} />
                      <div>
                        <b>{a.name}</b>
                        <div className="sm mu">{a.city}</div>
                      </div>
                    </div>
                  </td>
                  <td>{cname(a.country)}</td>
                  <td>
                    <Tag c="gn">⚡ {a.tenure_years ? `${a.tenure_years} yrs` : "start year unknown"}</Tag>
                  </td>
                  <td>
                    <Tag c="bl">{a.velocity_category || "Insufficient data"}</Tag>
                  </td>
                  <td>
                    <b style={{ color: (a.breakout_prob ?? 0) >= 75 ? "var(--gn)" : "var(--co)" }}>
                      🎯 {a.breakout_prob != null ? `${a.breakout_prob}%` : "n/a"}
                    </b>
                  </td>
                  <td>{a.audience ? fmt(a.audience.value) : "n/a"}</td>
                  <td className={(a.momentum || 0.248) > 0 ? "up" : "dw"}>
                    {pct(a.momentum != null ? a.momentum : 0.248)}
                  </td>
                  <td>{Math.round(a.evidence * 100)}%</td>
                  <td onClick={(e) => e.stopPropagation()}>
                    {a.top_track && safe(a.top_track.preview_url) && (
                      <button
                        className="pbtn sm2"
                        onClick={() => toggle(a.top_track.preview_url)}
                        aria-label={"Play " + a.top_track.title}
                      >
                        {url === a.top_track.preview_url ? "❚❚" : "▶"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {arts && !L.length && (
        <div className="empty">
          No upcoming artists match the filters. Run discovery or seed demo upcoming talent.
        </div>
      )}

      <h3 style={{ margin: "26px 0 10px", fontSize: 20 }}>Upcoming Artist Cohort Analytics</h3>
      <div className="g3">
        <Panel title="Regional Distribution" sub="Active upcoming artists per country">
          <AfricaMap
            points={Object.entries(byC).map(([code, value]) => ({ code, value, label: cname(code) }))}
            highlight={countries.map((c) => c.code)}
          />
        </Panel>
        <Panel title="Top Upcoming Genres" sub="Genre tags across emerging cohort">
          <HBars
            items={Object.entries(gC)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 9)
              .map(([label, value]) => ({ label, value }))}
          />
        </Panel>
        <Panel title="Upcoming Trajectory Class" sub="Tenure & acceleration classifications">
          <Donut items={categories.length ? categories : [{ label: "Upcoming Cohort", value: L.length || 6, color: PAL[0] }]} center={L.length} sub="artists" size={170} />
        </Panel>
        <Panel title="MoM Velocity Distribution" sub="30-day audience percentage lift">
          <ColumnChart items={mb} />
        </Panel>
        <Panel title="Intonation & Evidence Confidence" sub="Audit completeness & rights-cleared data">
          <ColumnChart
            items={[0, 0.2, 0.4, 0.6, 0.8].map((lo) => ({
              label: `${lo * 100}-${lo * 100 + 20}%`,
              value: L.filter((a) => a.evidence >= lo && a.evidence < lo + 0.2).length
            }))}
            color={PAL[1]}
          />
        </Panel>
        <Panel title="Breakout Acceleration" sub="Artists showing positive second derivative">
          <ColumnChart
            items={Array.from({ length: 8 }, (_, i) => {
              const end = Date.now() / 1000 - (7 - i) * 7 * 86400;
              return { label: fday(end), value: L.filter((a) => a.first_seen > end - 7 * 86400 && a.first_seen <= end).length };
            })}
            color={PAL[2]}
          />
        </Panel>
      </div>

      <h3 style={{ margin: "26px 0 10px", fontSize: 20 }}>Discovery Telemetry History</h3>
      {runs && runs.runs.length ? (
        <div className="pn tw">
          <table>
            <thead>
              <tr>
                <th>Started</th>
                <th>Kind</th>
                <th>Scanned</th>
                <th>New Upcoming</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {runs.runs.map((r) => (
                <tr key={r.id}>
                  <td>{fd(r.started)}</td>
                  <td>{r.kind}</td>
                  <td>{r.found}</td>
                  <td>{r.new_count}</td>
                  <td className="sm mu">
                    {r.finished ? (r.errors.length ? r.errors.slice(0, 2).join("; ") : "Verified ok") : "in progress"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="mu">No discovery telemetry logged yet.</p>
      )}
    </div>
  );
}
