import { useState, useEffect } from "react";
import { api, setCsrf, setOnAuthLost } from "./api";
import { CSS } from "./styles";
import { CSS2 } from "./styles2";
import { Logo, Tag } from "./ui";
import { Home } from "./home";
import { Login } from "./login";
import { Discover } from "./discover";
import { Analyze } from "./analyze";
import { Recommend } from "./recommend";
import { Settings } from "./settings";
import { Search } from "./search";
import { setNames } from "./shared";

const NAV = [
  ["discover", "◎", "Discover", "Upcoming artist trajectory"],
  ["analyze", "🔬", "Analyze & Lab", "Forensics, stems & 20-plot telemetry"],
  ["recommend", "★", "Recommend", "A&R deal valuation & $3,750 advance"],
  ["settings", "⚙", "Settings & Guideline", "76+ providers & Python ML tuning"]
];

const ls = {
  get: (k) => {
    try {
      return localStorage.getItem(k);
    } catch {
      return null;
    }
  },
  set: (k, v) => {
    try {
      localStorage.setItem(k, v);
    } catch {
      /* storage unavailable */
    }
  }
};

export default function App() {
  const [view, setView] = useState("boot");
  const [user, setUser] = useState(null);
  const [tab, setTab] = useState("discover");
  const [sel, setSel] = useState(null);
  const [meta, setMeta] = useState(null);
  const [col, setCol] = useState(ls.get("msanii.col") === "1");
  const [find, setFind] = useState(false);
  const [due, setDue] = useState(0);

  const invite = new URLSearchParams(location.search).get("invite");

  useEffect(() => {
    setOnAuthLost(() => {
      setUser(null);
      setView("login");
    });
    api("/auth/me")
      .then((r) => {
        setCsrf(r.csrf);
        setUser(r.user);
        setView("app");
      })
      .catch(() => setView(invite ? "login" : "home"));
  }, []); // eslint-disable-line

  const loadMeta = () =>
    api("/meta")
      .then((m) => {
        setNames(m);
        setMeta(m);
      })
      .catch(() => {});

  useEffect(() => {
    if (view === "app") {
      loadMeta();
      api("/tasks")
        .then((t) => setDue(t.tasks.length))
        .catch(() => {});
    }
  }, [view, tab]); // eslint-disable-line

  useEffect(() => {
    const k = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setFind(true);
      }
    };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, []);

  const signedIn = (u, c) => {
    setCsrf(c);
    setUser(u);
    setView("app");
    setTab("discover");
    history.replaceState(null, "", location.pathname);
  };

  const out = async () => {
    try {
      await api("/auth/logout", { method: "POST" });
    } catch {
      /* already signed out */
    }
    setCsrf("");
    setUser(null);
    setMeta(null);
    setView("home");
  };

  const open = (id) => {
    setSel(id);
    setTab("analyze");
    setFind(false);
  };

  const toggle = () => {
    setCol(!col);
    ls.set("msanii.col", col ? "0" : "1");
  };

  return (
    <div className="m">
      <style>{CSS}{CSS2}</style>

      {view === "boot" && <p className="mu" style={{ padding: 24 }}>Connecting to MSANII Neural Engine…</p>}
      {view === "home" && <Home go={() => setView("login")} />}
      {view === "login" && <Login onIn={signedIn} back={() => setView("home")} />}

      {view === "app" && user && (
        <div className={"shell " + (col ? "col" : "")}>
          <aside className="side" style={{ display: "flex", flexDirection: "column" }}>
            <div className="row sp" style={{ padding: "12px 10px 8px", flexWrap: "nowrap" }}>
              <Logo />
            </div>

            {/* Upcoming Artist Subtitle */}
            <div
              className="lbl"
              style={{
                fontSize: 10,
                fontWeight: 800,
                color: "var(--co)",
                letterSpacing: "0.8px",
                padding: "0 12px 14px",
                opacity: 0.9
              }}
            >
              UPCOMING ARTIST INTELLIGENCE
            </div>

            <nav aria-label="Main" style={{ flex: 1 }}>
              {NAV.map(([k, g, l, sub]) => (
                <button
                  key={k}
                  className={"nv " + (tab === k ? "on" : "")}
                  disabled={k === "settings" && user.role !== "admin"}
                  title={k === "settings" && user.role !== "admin" ? "Admins only" : `${l} – ${sub}`}
                  onClick={() => setTab(k)}
                  style={{
                    position: "relative",
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    margin: "2px 0"
                  }}
                >
                  <span className="ic2" aria-hidden="true" style={{ fontSize: 16 }}>{g}</span>
                  <span className="lbl" style={{ fontWeight: tab === k ? 700 : 500 }}>{l}</span>
                  {k === "recommend" && due > 0 && (
                    <span className="bdg lbl" style={{ marginLeft: "auto" }}>{due}</span>
                  )}
                  {k === "analyze" && !sel && (
                    <span
                      className="lbl"
                      style={{
                        marginLeft: "auto",
                        fontSize: 9,
                        background: "rgba(124, 92, 255, 0.2)",
                        color: "#7c5cff",
                        padding: "1px 5px",
                        borderRadius: 4,
                        fontWeight: 700
                      }}
                    >
                      LAB
                    </span>
                  )}
                </button>
              ))}
            </nav>

            <div style={{ marginTop: "auto", padding: 12, borderTop: "1px solid var(--bd2)" }} className="sfoot">
              <div className="sm mu lbl" style={{ wordBreak: "break-all", fontSize: 11, marginBottom: 4 }}>
                {user.email}
              </div>
              <div className="row sp" style={{ marginTop: 4 }}>
                <Tag c="bl">{user.role}</Tag>
                <button className="btn g" style={{ padding: "3px 10px", fontSize: 12 }} onClick={out}>
                  Sign out
                </button>
              </div>
            </div>
          </aside>

          <main className="main">
            <div className="tb">
              <button
                className="ibtn"
                onClick={toggle}
                aria-label={col ? "Expand sidebar" : "Collapse sidebar"}
                title={col ? "Expand sidebar" : "Collapse sidebar"}
              >
                {col ? "☰" : "◀"}
              </button>

              <button className="sbox" onClick={() => setFind(true)} aria-label="Search upcoming artists">
                ⌕ <span>Search upcoming artists, sounds or tracks…</span>
                <kbd>Ctrl K</kbd>
              </button>

              <div className="row" style={{ gap: 8, marginLeft: "auto" }}>
                <span
                  className="bdg"
                  style={{
                    background: "rgba(16, 185, 129, 0.15)",
                    color: "#10b981",
                    border: "1px solid #10b981",
                    fontSize: 11,
                    padding: "3px 8px"
                  }}
                >
                  ⚡ Upcoming Focus &le;5y
                </span>

                {meta && <Tag c="bl">{meta.workspace?.region || "East Africa"}</Tag>}

                <button
                  className="ibtn"
                  onClick={() => setTab("recommend")}
                  aria-label={`${due} reviews due`}
                  title={`${due} reviews due`}
                  style={{ position: "relative" }}
                >
                  🔔
                  {due > 0 && (
                    <span
                      className="bdg"
                      style={{
                        position: "absolute",
                        top: -6,
                        right: -6,
                        background: "var(--co)",
                        color: "#fff",
                        borderRadius: 99,
                        fontSize: 11,
                        padding: "0 6px"
                      }}
                    >
                      {due}
                    </span>
                  )}
                </button>

                {col && (
                  <button className="btn g" onClick={out} style={{ padding: "4px 10px", fontSize: 12 }}>
                    Sign out
                  </button>
                )}
              </div>
            </div>

            {!meta ? (
              <p className="mu" style={{ padding: 24 }}>Connecting to database telemetry…</p>
            ) : (
              <>
                {tab === "discover" && <Discover user={user} meta={meta} open={open} />}
                {tab === "analyze" && <Analyze id={sel} user={user} onPickArtist={open} />}
                {tab === "recommend" && <Recommend user={user} open={open} />}
                {tab === "settings" && user.role === "admin" && (
                  <Settings meta={meta} reloadMeta={loadMeta} />
                )}
              </>
            )}
          </main>

          {find && <Search onPick={open} onClose={() => setFind(false)} />}
        </div>
      )}
    </div>
  );
}
