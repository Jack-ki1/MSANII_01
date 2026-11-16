import { useState } from "react";
import { Logo, Spark, mk } from "./ui";
import { Radar, LineChart, Donut, HBars, AfricaMap, Scatter, Funnel, ColumnChart, PAL } from "./charts";

const N_SOURCES = 76, N_LIVE = 9, N_GENRES = 86;
const SAMPLE = mk(18000, 0.09, 0.1, 7).slice(-60);
const GENRES = ["Afrobeats", "Amapiano", "Bongo Flava", "Singeli", "Gengetone", "Benga", "Taarab", "Kidandali", "Afro-soul", "Afro-fusion", "Highlife", "Ndombolo", "Soukous", "Mbalax", "Gqom", "Kwaito", "Afro-house", "Ethio-jazz", "Mugithi", "Ohangla", "Chakacha", "Zilizopendwa", "Kadongo Kamu", "Afro-gospel", "Hip hop", "Drill", "R&B", "Neo-soul", "Dancehall", "Reggae", "Fuji", "Juju", "Azonto", "Kuduro", "Zouk", "Coupe-decale", "Maskandi", "Mbaqanga", "Lo-fi", "Alternative", "Indie pop", "Folk", "Jazz", "Deep house"];
const EAST = ["KE", "TZ", "UG", "RW", "BI", "ET", "SS", "SO", "DJ", "ER"];
const img = (id) => `https://images.unsplash.com/${id}?auto=format&fit=crop&w=900&q=70`;
const FAQ = [["Where does the data come from?", "From public provider APIs (MusicBrainz, Deezer, Audius, iTunes, Last.fm, YouTube, Spotify, Wikipedia and more), from files and links your team uploads in Song Lab, and from manual or CSV imports. Every figure keeps its source and date."],
  ["Does MSANII score songs automatically?", "It measures what can honestly be measured from audio (levels, dynamics, clipping, an estimated tempo) and shows the method and confidence. Artistic pillar scores come from human A&R reviews until a validated model exists, and the platform says so."],
  ["Can it tell if an artist bought streams?", "No, and it never accuses anyone. It raises transparent signals (sudden jumps, inconsistent platforms, concentrated UGC) with a confidence level so your team can investigate."],
  ["Which countries are covered?", "All 54 African countries are available. Your workspace region defaults to East Africa and can be changed in Settings; Discover then lets you pick a country inside that region."],
  ["Who can sign in?", "Only people invited by an admin. Roles are admin, reviewer and viewer, with optional authenticator-app MFA and a tamper-evident audit log."],
  ["What does MSANII not do yet?", "Live TikTok and Instagram data need approved providers, predictive models wait for enough history, and many catalogued sources are listed but not yet connected. The Settings page shows each source's real status."]];

export function Home({ go }) {
  const [tab, setTab] = useState(0);
  const tabs = ["Discover", "Analyze", "Recommend", "Settings"];
  return (<div className="hp">
    <header className="hero" style={{ paddingBottom: 170 }}>
      <nav className="hn"><Logo light /><div className="hl"><a href="#tour" style={{ color: "#fff" }}>Platform</a><a href="#avm" style={{ color: "#fff" }}>Method</a><a href="#map" style={{ color: "#fff" }}>Markets</a><a href="#faq" style={{ color: "#fff" }}>FAQ</a></div><button className="btn lm" onClick={go}>Sign in</button></nav>
      <div className="eq" aria-hidden="true">{Array.from({ length: 48 }, (_, i) => <i key={i} style={{ animationDelay: `${(i % 12) * -0.17}s`, animationDuration: `${1 + (i % 7) * 0.18}s` }} />)}</div>
      <div className="hb"><div>
        <div className="tag" style={{ background: "rgba(255,255,255,.18)", color: "#fff", borderColor: "transparent", marginBottom: 14 }}>Invite-only · Built for African A&amp;R</div>
        <h1 className="hh">Discover. Understand.<br />Back the next<br /><em>big sound.</em></h1>
        <p className="lead">Find emerging artists across Africa, read their story, sample their songs, test the evidence, and decide with confidence. Data and culture, in one place.</p>
        <div className="row"><button className="btn lm" onClick={go}>Sign in with your invite</button><a className="btn gh" href="#tour" style={{ textDecoration: "none" }}>Take the tour</a></div></div>
        <div className="fl" aria-hidden="true">
          <div className="fc" style={{ transform: "rotate(-4deg)" }}><span className="sm mu">Audience</span><h2>28.4K</h2><Spark d={SAMPLE} /><span className="sm mu">Illustrative</span></div>
          <div className="fc" style={{ width: 190 }}><span className="sm mu">Evidence confidence</span><h2>85%</h2><div className="mtr"><i style={{ width: "85%" }} /></div><span className="sm mu">Illustrative</span></div>
          <div className="fc" style={{ transform: "rotate(4deg)" }}><span className="sm mu">30-day momentum</span><h2>+24%</h2><Spark d={SAMPLE.slice(-30)} /><span className="sm mu">Illustrative</span></div></div></div>
      <div className="cl" /></header>

    <div className="tick" aria-hidden="true"><div>{[...GENRES, ...GENRES].map((g, i) => <span key={i}>♪ {g}</span>)}</div></div>

    <section id="how"><div className="ey">HOW IT WORKS</div><h2 className="h">From a name on a chart to a decision you can defend</h2><p className="lead2">Four steps, each with its evidence attached.</p>
      <div className="steps" style={{ maxWidth: 1100, margin: "20px auto 0" }}>
        {[["Discover", "Search a country and genre inside your region. MSANII queries open and keyed sources, de-duplicates artists and starts a time-stamped audience history."], ["Understand", "Each artist gets a dossier: biography, picture, links and songs you can sample, with a place to write the story only your scouts know."], ["Analyse", "Audience, UGC and growth-integrity analysis, human reviews on 11 criteria, and Song Lab for your own uploads and links."], ["Decide", "Tiers (Pursue, Meet, Watch, More evidence) come with reasons, risks and what is missing. Decisions are signed and audited."]].map(([t, d]) => <div className="stp" key={t}><h3>{t}</h3><p className="mu">{d}</p></div>)}</div></section>

    <section id="tour" style={{ background: "var(--sf)" }}><div className="ey">THE PLATFORM</div><h2 className="h">Four workspaces, one flow</h2><p className="lead2">A quick look at what your team works with every day (sample numbers, for illustration only).</p>
      <div className="tabsx" role="tablist">{tabs.map((t, i) => <button key={t} role="tab" aria-selected={tab === i} className={tab === i ? "on" : ""} onClick={() => setTab(i)}>{t}</button>)}</div>
      <div className="shot">
        {tab === 0 && <div className="g2"><div className="pn"><h3 className="t">Where artists are</h3><AfricaMap points={[{ code: "KE", value: 14, label: "Kenya" }, { code: "TZ", value: 9, label: "Tanzania" }, { code: "UG", value: 11, label: "Uganda" }, { code: "RW", value: 5, label: "Rwanda" }]} highlight={EAST} /></div>
          <div className="pn"><h3 className="t">Genres in view</h3><HBars items={[{ label: "Afro-fusion", value: 12 }, { label: "Singeli", value: 9 }, { label: "Kidandali", value: 7 }, { label: "Gospel-pop", value: 6 }, { label: "Taarab-pop", value: 4 }]} /><h3 className="t" style={{ marginTop: 14 }}>Maturity</h3><Donut items={[{ label: "Early", value: 14 }, { label: "Emerging", value: 18 }, { label: "Developing", value: 7 }]} center="39" sub="artists" size={150} /></div></div>}
        {tab === 1 && <div className="g2"><div className="pn"><h3 className="t">Audience over time</h3><LineChart series={[{ name: "Deezer fans", data: SAMPLE }, { name: "Last.fm", data: SAMPLE.map((v, i) => v * 2.4 + i * 90), color: PAL[1] }]} area={false} /></div>
          <div className="pn"><h3 className="t">Artistic Value Model (human review)</h3><Radar axes={["Vocal", "Writing", "Song", "Composition"]} sets={[{ name: "Reviewer A", values: [78, 71, 66, 74], color: PAL[0] }, { name: "Reviewer B", values: [70, 76, 62, 69], color: PAL[3] }]} size={250} /></div></div>}
        {tab === 2 && <div className="g2"><div className="pn"><h3 className="t">Artistic vs momentum</h3><Scatter xl="Artistic score" yl="Momentum" xr={[40, 100]} yr={[-10, 50]} xt={70} yt={15} quad={["Trend riders", "Breakout", "Unproven", "Hidden gems"]} points={[{ x: 78, y: 28, r: 11, label: "Artist A", color: PAL[2] }, { x: 64, y: 40, r: 9, label: "Artist B", color: PAL[3] }, { x: 82, y: 5, r: 8, label: "Artist C", color: PAL[0] }, { x: 52, y: 2, r: 7, label: "Artist D", color: PAL[7] }]} /></div>
          <div className="pn"><h3 className="t">Pipeline funnel</h3><Funnel steps={[{ label: "Discovered", value: 120 }, { label: "Reviewed", value: 48 }, { label: "In pipeline", value: 22 }, { label: "Contacted", value: 9 }, { label: "Pursue", value: 3 }]} /></div></div>}
        {tab === 3 && <div className="g2"><div className="pn"><h3 className="t">Sources catalogued</h3><HBars items={[{ label: "Streaming", value: 18 }, { label: "Social & UGC", value: 12 }, { label: "Rights", value: 15 }, { label: "Radio & TV", value: 7 }, { label: "Live", value: 9 }, { label: "Analytics", value: 7 }, { label: "Open data", value: 8 }]} /><p className="sm mu">{N_SOURCES} sources catalogued, {N_LIVE} with working adapters today.</p></div>
          <div className="pn"><h3 className="t">Weekly review tasks</h3><ColumnChart items={["Mon", "Tue", "Wed", "Thu", "Fri"].map((l, i) => ({ label: l, value: [4, 2, 5, 1, 3][i] }))} /></div></div>}
        <p className="sm mu" style={{ textAlign: "center", marginTop: 10 }}>Illustrative preview with sample numbers.</p></div></section>

    <section id="avm"><div className="split"><div><div className="ey" style={{ textAlign: "left" }}>THE METHOD</div><h2 className="h" style={{ textAlign: "left", margin: "0 0 14px" }}>Artistic value, explained instead of guessed</h2>
      <p className="mu" style={{ marginBottom: 18 }}>The Artistic Value Model looks at four pillars. Today each is scored by human reviewers on named criteria, with machine measurements shown beside them (never mixed in unmarked).</p>
      {[["Vocal ability", "Vocal identity, performance ability", PAL[0]], ["Songwriting", "Storytelling, originality, emotional and cultural connection", PAL[1]], ["Song as a whole", "Structure, production, artistic direction", PAL[2]], ["Composition & arrangement", "Melody, musicality, groove", PAL[3]]].map(([t, d, c], i) => <div className="pilr" key={t}><div className="nb" style={{ background: c }}>{i + 1}</div><div><b>{t}</b><div className="sm mu">{d}</div></div></div>)}</div>
      <div className="pn"><Radar axes={["Vocal", "Writing", "Song", "Composition"]} sets={[{ name: "Human review", values: [76, 70, 68, 72], color: PAL[0] }]} size={280} /><p className="sm mu" style={{ textAlign: "center" }}>Illustrative. Missing evidence stays blank.</p></div></div></section>

    <section style={{ background: "var(--sf)" }}><div className="ey">PRINCIPLES</div><h2 className="h">Evidence before opinion</h2><p className="lead2">What MSANII will and will not do.</p>
      <div className="prin">{[["Never fabricates", "No invented lyrics, keys, pitch accuracy or scores. If it cannot be measured, it says so."], ["Signals, not accusations", "Unusual growth is flagged with a confidence level. Manipulation is never asserted."], ["Humans decide", "Machine measurements and human reviews stay separate and labelled."], ["Rights respected", "Only audio and video your team is licensed to analyse can be uploaded."], ["Source on every number", "Provider, date and method travel with each figure."], ["Built for Africa", "Region-first discovery, local genres, and room for regional platforms and societies."]].map(([t, d]) => <div key={t}><b>{t}</b><span className="mu">{d}</span></div>)}</div></section>

    <section id="map"><div className="ey">MARKETS</div><h2 className="h">Start in East Africa. Go anywhere in Africa.</h2><p className="lead2">Pick a region once in Settings, then choose a country inside it whenever you discover.</p>
      <div className="split"><AfricaMap highlight={EAST} /><div><div className="chips" style={{ marginBottom: 16 }}>{["East Africa", "West Africa", "Southern Africa", "North Africa", "Central Africa"].map((r, i) => <span key={r} className={"chip " + (i === 0 ? "on" : "")}>{r}</span>)}</div>
        <p className="mu" style={{ marginBottom: 12 }}>Kenya, Tanzania, Uganda, Rwanda, Burundi, Ethiopia, South Sudan, Somalia, Djibouti and Eritrea are highlighted in the default East Africa region. The other regions are one setting away.</p>
        <div className="g4"><div className="pn" style={{ marginBottom: 0 }}><h2>54</h2><span className="sm mu">countries available</span></div><div className="pn" style={{ marginBottom: 0 }}><h2>{N_GENRES}</h2><span className="sm mu">genres and sub-genres</span></div></div></div></div></section>

    <section style={{ background: "var(--sf)" }}><div className="ey">SOUND &amp; STORY</div><h2 className="h">Every artist has a story and a sound</h2><p className="lead2">Read the biography, sample the songs, add your own notes, and run your own audio, video or links through Song Lab.</p>
      <div className="gal">{[["photo-1493225457124-a3eb161ffa5f", "On stage"], ["photo-1511671782779-c97d3d27a1d4", "In the studio"], ["photo-1514525253161-7a46d19cd819", "In the crowd"]].map(([id, c]) => <div key={id}><img src={img(id)} alt="" loading="lazy" referrerPolicy="no-referrer" onError={(e) => { e.currentTarget.style.display = "none"; }} /><span>{c}</span></div>)}</div></section>

    <section><div className="ey">GENRES</div><h2 className="h">{N_GENRES} genres and counting</h2><p className="lead2">From Singeli and Gengetone to Amapiano, Taarab, Highlife and Afro-jazz.</p>
      <div className="cloud">{GENRES.map((g, i) => <span key={g} style={{ background: ["#e8f2ff", "#efeaff", "#e2f8f4", "#fff3dc", "#fde7f3", "#f1ffd0"][i % 6], color: ["#0756b5", "#5b3fd6", "#0d8a7c", "#a56a0b", "#b0246f", "#4f6b00"][i % 6], fontSize: 13 + (i % 5) * 2 }}>{g}</span>)}</div></section>

    <section style={{ background: "var(--sf)" }}><div className="ey">A WEEK WITH MSANII</div><h2 className="h">Built around how A&amp;R teams actually work</h2><p className="lead2" />
      <div className="day">{[["MON", "Run discovery for a country and genre. See who is new and who has fresh signals."], ["TUE", "Open dossiers. Read the story, sample the songs, refresh profiles."], ["WED", "Reviewers score the shortlist. UGC and platform figures get imported."], ["THU", "Song Lab: upload demos or paste links and check levels, dynamics and clipping."], ["FRI", "Committee: compare artists, record decisions, clear review tasks."]].map(([d, t]) => <div key={d}><b>{d}</b><p className="mu" style={{ marginTop: 6 }}>{t}</p></div>)}</div></section>

    <section><div className="ey">TRUST</div><h2 className="h">Private by design</h2><p className="lead2">An internal platform holding research, decisions and provider credentials.</p>
      <div className="prin">{[["Invite-only access", "No public sign-up. Roles for admins, reviewers and viewers."], ["Protected sessions", "HttpOnly cookies, CSRF protection and optional MFA."], ["Secrets stay server-side", "Provider keys are encrypted and never shown again."], ["Tamper-evident audit", "Signed decisions and a hash-chained log of sensitive actions."]].map(([t, d]) => <div key={t}><b>{t}</b><span className="mu">{d}</span></div>)}</div></section>

    <section id="faq" style={{ background: "var(--sf)" }}><div className="ey">QUESTIONS</div><h2 className="h">Straight answers</h2><p className="lead2" /><div className="faq">{FAQ.map(([q, a]) => <details key={q}><summary>{q}</summary><p>{a}</p></details>)}</div></section>

    <section><div className="band2"><h2>Your next hit is out there.</h2><p style={{ marginBottom: 18, opacity: .95 }}>We help you find it first, and prove why.</p><button className="btn lm" onClick={go}>Sign in</button></div></section>
    <footer className="hf"><div className="cols"><div><Logo light /><p style={{ marginTop: 10 }}>Autonomous artist discovery and evidence-led A&amp;R for African music.</p></div>
      <div><b>Platform</b><p>Discover</p><p>Analyze</p><p>Recommend</p><p>Settings</p></div><div><b>Method</b><p>Artistic Value Model</p><p>Growth integrity</p><p>Song Lab</p></div><div><b>Access</b><p>Invite-only</p><p>Audit and security</p><p>FAQ</p></div></div></footer>
  </div>);
}
