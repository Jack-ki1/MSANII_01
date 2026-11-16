import { useState } from "react";
import { api } from "./api";
import { Logo, Tag } from "./ui";

export function Login({ onIn, back }) {
  const tk = new URLSearchParams(location.search).get("invite") || "";
  const [mode, setMode] = useState(tk ? "invite" : "in"); // "in" | "request" | "invite"
  const [f, setF] = useState({
    email: "", password: "", code: "", token: tk,
    full_name: "", organization: "", role_title: "A&R Scout", region: "East Africa", notes: ""
  });
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const [mfa, setMfa] = useState(false);
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const sub = async (e) => {
    e.preventDefault();
    setErr("");
    setOk("");
    setBusy(true);

    try {
      if (mode === "request") {
        const r = await api("/auth/request-access", {
          method: "POST",
          body: {
            full_name: f.full_name,
            email: f.email,
            organization: f.organization,
            role_title: f.role_title,
            region: f.region,
            notes: f.notes
          }
        });
        setOk(r.message || "Request transmitted to kimothojackson1125@gmail.com. Check your email for approval & guidelines.");
        setF({ ...f, password: "", notes: "" });
      } else if (mode === "invite") {
        await api("/auth/accept-invite", {
          method: "POST",
          body: { token: f.token, password: f.password }
        });
        setOk("Account created. Sign in with the email your invite was sent to.");
        setMode("in");
        setF({ ...f, password: "", token: "" });
        history.replaceState(null, "", location.pathname);
      } else {
        const r = await api("/auth/login", {
          method: "POST",
          body: { email: f.email, password: f.password, ...(f.code && { code: f.code }) }
        });
        onIn(r.user, r.csrf);
      }
    } catch (x) {
      if (x.data && x.data.mfa_required) setMfa(true);
      setErr(x.message || "Operation failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="lw">
      <div className="lp">
        <Logo light />
        <div>
          <h1>Upcoming Artists. <em>Verified Data.</em></h1>
          <p style={{ marginTop: 12, opacity: 0.92, maxWidth: 380 }}>
            The executive intelligence suite for discovering, analyzing, and recommending
            the next generation of musical talent within their first 5 years.
          </p>
          <div style={{ marginTop: 24, display: "flex", gap: 8, flexWrap: "wrap" }}>
            <Tag c="gn">5-Year Upcoming Focus</Tag>
            <Tag c="bl">CREPE f0 Intonation</Tag>
            <Tag c="am">Safe Zone Bot Detection</Tag>
          </div>
        </div>
        <button className="btn gh" style={{ alignSelf: "flex-start" }} onClick={back}>
          Back to home
        </button>
      </div>

      <div className="lf">
        <form style={{ width: 380, maxWidth: "100%" }} onSubmit={sub}>
          {/* Top Segmented Mode Selector */}
          <div className="seg" style={{ width: "100%", marginBottom: 20 }}>
            <button
              type="button"
              className={mode === "in" ? "on" : ""}
              style={{ flex: 1 }}
              onClick={() => { setMode("in"); setErr(""); setOk(""); }}
            >
              Sign In
            </button>
            <button
              type="button"
              className={mode === "request" ? "on" : ""}
              style={{ flex: 1 }}
              onClick={() => { setMode("request"); setErr(""); setOk(""); }}
            >
              Request Access
            </button>
            <button
              type="button"
              className={mode === "invite" ? "on" : ""}
              style={{ flex: 1 }}
              onClick={() => { setMode("invite"); setErr(""); setOk(""); }}
            >
              Invite Token
            </button>
          </div>

          <h2 style={{ fontSize: 26, marginBottom: 4 }}>
            {mode === "request" ? "Request Platform Access" : mode === "invite" ? "Accept Your Invitation" : "Sign in to MSANII"}
          </h2>
          <p className="sm mu" style={{ marginBottom: 16 }}>
            {mode === "request"
              ? "All access requests are reviewed directly by Jackson Kimotho (kimothojackson1125@gmail.com)."
              : mode === "invite"
              ? "Enter your secure token and create your 10+ character password."
              : "Authorized executive & reviewer login."}
          </p>

          {/* REQUEST ACCESS MODE */}
          {mode === "request" && (
            <>
              <p>
                <label className="sm mu" style={{ display: "block", marginBottom: 4 }}>Full Name</label>
                <input
                  className="inp"
                  aria-label="Full Name"
                  placeholder="e.g. Jackson Kimotho"
                  required
                  value={f.full_name}
                  onChange={set("full_name")}
                />
              </p>
              <p>
                <label className="sm mu" style={{ display: "block", marginBottom: 4 }}>Work Email</label>
                <input
                  className="inp"
                  type="email"
                  aria-label="Work Email"
                  placeholder="you@company.com"
                  required
                  value={f.email}
                  onChange={set("email")}
                />
              </p>
              <div className="row" style={{ gap: 8 }}>
                <div style={{ flex: 1 }}>
                  <label className="sm mu" style={{ display: "block", marginBottom: 4 }}>Organization</label>
                  <input
                    className="inp"
                    placeholder="Record label / Agency"
                    value={f.organization}
                    onChange={set("organization")}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="sm mu" style={{ display: "block", marginBottom: 4 }}>Role / Title</label>
                  <select className="inp" value={f.role_title} onChange={set("role_title")}>
                    <option>A&R Scout</option>
                    <option>A&R Director</option>
                    <option>Label Executive</option>
                    <option>Music Data Scientist</option>
                    <option>Audio Engineer</option>
                    <option>Independent Manager</option>
                  </select>
                </div>
              </div>
              <p style={{ marginTop: 10 }}>
                <label className="sm mu" style={{ display: "block", marginBottom: 4 }}>Territory Focus</label>
                <select className="inp" value={f.region} onChange={set("region")}>
                  <option>East Africa (Kenya, TZ, UG, Rwanda)</option>
                  <option>West Africa (Nigeria, Ghana, Senegal)</option>
                  <option>Southern Africa (South Africa, Zimbabwe)</option>
                  <option>Diaspora (UK, US, Europe)</option>
                  <option>Pan-African (All Hubs)</option>
                </select>
              </p>
              <p>
                <label className="sm mu" style={{ display: "block", marginBottom: 4 }}>Reason for Access / Portfolio</label>
                <textarea
                  className="inp"
                  rows="3"
                  placeholder="Tell Jackson why you'd like access to MSANII and your scouting focus..."
                  value={f.notes}
                  onChange={set("notes")}
                />
              </p>
            </>
          )}

          {/* SIGN IN MODE */}
          {mode === "in" && (
            <>
              <p>
                <label className="sm mu" style={{ display: "block", marginBottom: 4 }}>Work Email</label>
                <input
                  className="inp"
                  type="email"
                  aria-label="Work email"
                  placeholder="you@company.com"
                  required
                  value={f.email}
                  onChange={set("email")}
                  autoComplete="email"
                />
              </p>
              <p>
                <label className="sm mu" style={{ display: "block", marginBottom: 4 }}>Password</label>
                <input
                  className="inp"
                  type="password"
                  aria-label="Password"
                  placeholder="Password"
                  required
                  value={f.password}
                  onChange={set("password")}
                  autoComplete="current-password"
                />
              </p>
              {mfa && (
                <p>
                  <label className="sm mu" style={{ display: "block", marginBottom: 4 }}>MFA Code</label>
                  <input
                    className="inp"
                    aria-label="MFA code"
                    placeholder="6-digit authenticator code"
                    inputMode="numeric"
                    value={f.code}
                    onChange={set("code")}
                    autoComplete="one-time-code"
                  />
                </p>
              )}
            </>
          )}

          {/* INVITE TOKEN MODE */}
          {mode === "invite" && (
            <>
              <p>
                <label className="sm mu" style={{ display: "block", marginBottom: 4 }}>Invite Token</label>
                <input
                  className="inp"
                  aria-label="Invite token"
                  placeholder="Paste your 32-character invite token"
                  required
                  value={f.token}
                  onChange={set("token")}
                  autoComplete="off"
                />
              </p>
              <p>
                <label className="sm mu" style={{ display: "block", marginBottom: 4 }}>New Password</label>
                <input
                  className="inp"
                  type="password"
                  aria-label="New password"
                  placeholder="10+ characters, letters & numbers"
                  required
                  value={f.password}
                  onChange={set("password")}
                  autoComplete="new-password"
                />
              </p>
            </>
          )}

          {ok && (
            <div className="bn" style={{ background: "rgba(31,157,115,.12)", color: "#2ea043", marginTop: 12, padding: "10px 14px", borderRadius: 8, fontSize: 13 }}>
              <b>✓ Notice:</b> {ok}
            </div>
          )}
          {err && (
            <div className="bn" style={{ background: "rgba(239,106,91,.12)", color: "#ef6a5b", marginTop: 12, padding: "10px 14px", borderRadius: 8, fontSize: 13 }} role="alert">
              <b>Error:</b> {err}
            </div>
          )}

          <button
            className="btn"
            style={{ width: "100%", marginTop: 16 }}
            disabled={busy}
          >
            {busy
              ? "Processing…"
              : mode === "request"
              ? "Submit Access Request"
              : mode === "invite"
              ? "Create Account"
              : "Sign in"}
          </button>

          {mode === "in" && (
            <div style={{ marginTop: 14, textAlign: "center" }}>
              <span className="sm mu">New to MSANII? </span>
              <button
                type="button"
                className="btn g"
                style={{ padding: "2px 8px", fontSize: 12 }}
                onClick={() => { setMode("request"); setErr(""); setOk(""); }}
              >
                Request an account
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
