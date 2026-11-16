# MSANII v3

**Discover. Understand. Back the next big sound.**

MSANII is an internal, invite-only A&R platform for finding and evaluating emerging artists in Africa (East Africa by default). It combines region-aware discovery, rich artist dossiers (story, songs you can sample, audience analytics), human A&R review, a Song Lab for your own audio, video and links, and an explainable recommendation workflow with signed, audited decisions.

> **What is real and what is not.** MSANII never invents data. No audio means "not assessed". Under 7 days of history means momentum is "n/a". Predictive models say "0 trained" until enough history exists. Growth-integrity flags are signals, never accusations. Demo artists are fictional and tagged. See [Honest limits](#13-honest-limits).

## Contents
1. [What's new in v3](#1-whats-new-in-v3) 2. [Features](#2-features) 3. [Tech stack](#3-tech-stack) 4. [Folder structure](#4-folder-structure) 5. [Requirements](#5-requirements) 6. [Quick start](#6-quick-start) 7. [Other ways to run](#7-other-ways-to-run) 8. [Configuration](#8-configuration) 9. [Using the platform](#9-using-the-platform) 10. [Data providers](#10-data-providers) 11. [How the logic works](#11-how-the-logic-works) 12. [API reference](#12-api-reference) and [security](#12b-security) 13. [Honest limits](#13-honest-limits) 14. [Operations](#14-operations) 15. [Testing](#15-testing) 16. [Troubleshooting](#16-troubleshooting) 17. [Roadmap](#17-roadmap)

---

## 1. What's new in v3
- **Home page** rebuilt: animated hero, genre ticker, product tour with charts, method, principles, Africa map, gallery, a week-with-MSANII story, FAQ.
- **Owner account** seeded on first start (see [First sign-in](#first-sign-in)).
- **Discover:** region-based country dropdown (default East Africa), 86-genre dropdown, no established-artist logic, cards or list view, richer artist cards (picture, bio, audience, momentum, songs, play a sample), CSV export, and six analytics plots (map, genres, maturity, momentum, evidence, discoveries per week).
- **Analyze:** profile overview (story, songs with a player, links), eight sections with KPI strips and Power-BI-style charts, and a **Song Lab** for uploads (audio and video) and links.
- **Recommend:** KPIs, tier donut, quadrant scatter, pipeline funnel, Kanban board, comparison radar, performance review, signed decisions, review tasks.
- **Settings:** 76 catalogued data sources with live health stats, region and country settings, discovery pickers, weight presets, system status, categorised audit log, password change.
- **App shell:** collapsible sidebar, Ctrl/Cmd+K artist search, review-task alerts.

## 1b. Transformed Architecture & Production Deployment (v3.2 Custom)

### A. Supabase PostgreSQL Integration
MSANII now natively supports **Supabase PostgreSQL** with automated table provisioning, indexes, and Row Level Security (RLS) policies.
1. Create a Supabase project at [supabase.com](https://supabase.com).
2. Execute `supabase_schema.sql` in the Supabase SQL Editor.
3. Configure your connection string in `.env` or Vercel Environment Variables:
   ```bash
   SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
   ```
4. If `SUPABASE_DB_URL` is omitted, MSANII automatically falls back to high-performance local SQLite WAL mode (`data/msanii.db`).

### B. Vercel Serverless Deployment
The repository includes a battle-tested Vercel configuration (`vercel.json`) and serverless WSGI entrypoint (`api/index.py`).
1. Connect this repository to Vercel or deploy via CLI:
   ```bash
   npm i -g vercel
   vercel --prod
   ```
2. In the Vercel Dashboard, define:
   - `SUPABASE_DB_URL`: your Supabase PostgreSQL connection string
   - `SECRET_KEY`: random 64-char string
   - `FERNET_KEY`: Fernet encryption key (`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
   - `ADMIN_NOTIFICATION_EMAIL`: `kimothojackson1125@gmail.com`
   - `SMTP_USER` / `SMTP_PASS` (optional, for direct SMTP email delivery)

### C. Access Request Approval Flow
1. Visitors click **"Request Access"** on the login page, submitting their name, email, organization, requested role, and scouting focus.
2. An instant notification with one-click approval/rejection links is dispatched to:
   **`kimothojackson1125@gmail.com`**
3. Once approved (via the email link or via **Settings &gt; Team &amp; Access &gt; Pending Access Requests**), the user is provisioned with a secure temporary password and access guidelines.

### D. Upcoming Artist Focus (&le; 5 Years)
MSANII explicitly filters the discovery pool to upcoming artists who have not finished 5 years in the music industry.
- Stage classifications: *Early Debut (&le;1.5 yrs)*, *Emerging Breakout (1.5–3.5 yrs)*, *Developing Talent (3.5–5.0 yrs)*.
- Breakout ML Model: Calibrated sigmoid regressor computing breakout probability based on 30-day velocity, creator diversity, and acoustic uniqueness.

### E. Acoustic Science, 20-Plot Power BI Dashboard & Song Lab
- **Song Lab Standalone:** Uploading or attaching any song immediately unlocks full psychoacoustic analysis (stems, CREPE intonation, key, and dynamic range).
- **Executive Dossier (Merged):** Merges Artistic Value, Audience, Growth Integrity, Trajectory, and Evidence &amp; Reviews into one unified intelligence dossier.
- **Acoustic & Velocity Analytics:** 8 Executive KPIs and 20 interactive Power BI grade visualizations.
- **A&R Deal Valuation:** Interactive deal simulator with **$3,750 benchmark advance**, 8.4-month projected recoupment, and custom royalty splits (70/30, 85/15, 50/50).

### F. Data Provider Tuning (76+ Providers)
Under **Settings &gt; Data Providers**, all 76+ data sources across 8 specialized industry categories can be filtered, searched, and tuned:
- Custom priority slider (1–10)
- Custom rate limits (requests per minute)
- One-click credentials storage and live connection testing
- Health telemetry (calls, error rates, ping status)

## 2. Features
| Area | Highlights |
|---|---|
| Discover | Region from Settings; pick a country inside it; 86 genres; stage filter; name search; manual runs per country and genre; autonomous schedule (30/60/90 min); cards or list; CSV export; analytics plots |
| Analyze | Overview (profile, story, songs), Artistic Value (machine and human lenses), Audience, UGC, Growth Integrity, Trajectory, Evidence and Reviews, Song Lab |
| Recommend | PURSUE / MEET / WATCH / MORE EVIDENCE with reasons; quadrant chart; funnel; Kanban; comparison; performance diary; signed decision log; weekly and bimonthly review tasks |
| Settings | Workspace, Team and Access (roles, invites, MFA, sessions, password), Data Providers, Discovery, Scoring and Models, Automation, Security and Audit, System |

## 3. Tech stack
Python 3.10+ and Flask 3, SQLite (WAL), `requests`, `cryptography`; React 18 + Vite 5 (no UI framework); Bricolage Grotesque and Plus Jakarta Sans fonts; optional `ffmpeg` (video and non-WAV audio) and `librosa` (extra audio features); gunicorn and Docker for deployment.

## 4. Folder structure
```
msanii/
├── README.md  requirements.txt  requirements-audio.txt  .env.example
├── manage.py                 admin CLI: create-admin, set-password, seed-demo, clear-demo, discover, monitor, scheduler, backup
├── start.sh  Dockerfile  .dockerignore  .gitignore
├── msanii/                   Flask API (Python package)
│   ├── __init__.py           app factory, security headers/CSP, CORS, errors, static serving, owner seeding
│   ├── api.py                all HTTP endpoints
│   ├── db.py                 schema, migrations, hash-chained audit log
│   ├── security.py           sessions, CSRF, roles, rate limits, validation, encryption, TOTP, safe URLs
│   ├── engine.py             discovery, profile enrichment, growth, flags, evidence, tiers, review tasks
│   ├── providers.py          adapters and the 76-source catalogue, health stats
│   ├── media.py              Song Lab analysis (WAV stdlib, ffmpeg, link metadata)
│   ├── geo.py                African regions, countries, 86 genres
│   ├── demo.py               fictional demo artists (seed / clear)
│   ├── mail.py               optional SMTP invite e-mails
│   └── owner.py              owner account (password HASH only)
├── frontend/                 React source
│   ├── package.json  vite.config.js  index.html
│   └── src/
│       ├── main.jsx  App.jsx  api.js  geo.js  styles.js  styles2.js
│       ├── ui.jsx  shared.jsx  charts.jsx      shared components, hooks, SVG chart library
│       ├── home.jsx  login.jsx  search.jsx
│       └── discover.jsx  analyze.jsx  analyze2.jsx  recommend.jsx  settings.jsx
├── static/                   BUILT front end served by Flask (npm run build)
├── tests/                    test_smoke.py  test_extra.py
├── data/                     runtime (git-ignored): msanii.db, uploads/, .fernet_key (dev)
└── backups/                  created by manage.py backup
```

## 5. Requirements
Python 3.10+; Node 18+ only if you change the front end (a built bundle is included); Docker optional; internet access for provider calls. For video and MP3/FLAC/OGG analysis install **ffmpeg** (the Docker image includes it).

## 6. Quick start
```bash
cd msanii
python3 -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py seed-demo          # optional: 6 FICTIONAL artists with synthetic history, tagged "Demo"
export MSANII_CONTACT=you@kimoto.com                    # identifies you to MusicBrainz
flask --app msanii run --port 5000                       # open http://localhost:5000
python3 manage.py scheduler          # second terminal (optional): autonomous discovery, monitoring, review tasks
```
### First sign-in
On first start with an empty database MSANII creates the **owner** admin: email `owner@msanii.local`. The password was given to you separately when this version was delivered; only its scrypt hash is stored (`msanii/owner.py`). **Change it immediately** under Settings → Team & Access → Change password, then enable MFA. Forgot it? `python manage.py set-password owner@msanii.local`. To use your own admin instead, set `MSANII_ADMIN_EMAIL` and `MSANII_ADMIN_PASSWORD` before the first start (the owner is then not created) or run `python manage.py create-admin you@company.com`.

## 7. Other ways to run
**Front-end dev (hot reload):** `flask --app msanii run --port 5000 --debug` plus `cd frontend && npm install && npm run dev` (http://localhost:5173, proxies /api). Rebuild with `npm run build` (writes to `static/`).
**Docker (scheduler + web in one container):**
```bash
docker build -t msanii .                       # add --build-arg WITH_LIBROSA=1 for extra audio features
docker run -d -p 5000:5000 -v msanii-data:/data \
  -e MSANII_FERNET_KEY="$(python -c 'from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())')" \
  -e MSANII_ALLOWED_ORIGINS=https://msanii.yourcompany.com -e MSANII_CONTACT=you@company.com msanii
```
Put TLS in front (Caddy, Nginx, a cloud load balancer) and set `MSANII_PROXIES=1` only behind exactly one trusted proxy. Back up the Fernet key. **Without Docker:** `MSANII_ENV=production MSANII_FERNET_KEY=... gunicorn -w 1 --threads 8 -b 127.0.0.1:5000 "msanii:create_app()"` and run `python manage.py scheduler` as a service. Use ONE web worker (rate limits are in process memory). Production mode sets Secure cookies, which browsers drop over plain http, so test locally without `MSANII_ENV`.

## 8. Configuration
| Variable | Default | Purpose |
|---|---|---|
| `MSANII_ENV` | development | `production` enables Secure cookies, HSTS and requires the Fernet key |
| `MSANII_DB` / `MSANII_UPLOAD_DIR` | ./data/... | database file and upload folder |
| `MSANII_FERNET_KEY` | generated in dev | encrypts provider credentials; **back it up** |
| `MSANII_ALLOWED_ORIGINS` | http://localhost:5173 | allowed browser origins (CORS and Origin check) |
| `MSANII_CONTACT` | placeholder | contact in the User-Agent sent to MusicBrainz and Wikipedia |
| `MSANII_PROXIES` | 0 | trust one reverse proxy |
| `MSANII_ADMIN_EMAIL`, `MSANII_ADMIN_PASSWORD` | unset | first-run admin (skips the owner account) |
| `MSANII_BASE_URL`, `MSANII_SMTP_HOST/PORT/USER/PASSWORD/FROM` | unset | e-mailed invites (otherwise a link is shown once) |
| `PORT`, `VITE_API_BASE` | 5000, /api | container port; front-end API base |
In-app settings (admin) live in the database: workspace (region, default country, retention), discovery, weights, thresholds, automation.

## 9. Using the platform
Roles: **viewer** (read), **reviewer** (run discovery, review, import, Song Lab, decide), **admin** (everything plus team, settings, credentials, audit, export). Accounts are invite-only.
1. **Settings → Workspace:** choose your region (default East Africa). **Discovery:** pick countries, genres and providers.
2. **Discover:** choose a country in the region and a genre, then *Run discovery*. Switch between cards and list; read the six plots; export CSV.
3. **Analyze:** open an artist. Read the profile and story, sample songs, check KPIs and charts. *Refresh profile and songs* pulls the biography, picture, links and top songs. Write the scout's story yourself if none exists.
4. **Artistic Value → Human lens:** score 11 criteria and write notes. Import UGC figures (single or CSV). Use **Song Lab** to upload audio or video you are licensed to analyse, or paste a YouTube, Spotify, SoundCloud, Audius or TikTok link.
5. **Recommend:** read the tier and why; compare up to 3 artists; record a decision (rationale, owner, follow-up date). Work through review tasks; watch the Kanban board.
6. **Settings → Security and Audit:** review activity by category and verify the audit chain.
Shortcuts: **Ctrl/Cmd+K** search artists; the **◀** button collapses the sidebar.

## 10. Data providers
76 sources are catalogued in **Settings → Data Providers** with category, status, limits, health (calls, errors, last success) and docs links. Statuses: Fully implemented, Implemented with credentials, Partially implemented, Requires licensed access, Manual import, Planned.
**Live adapters (9):** MusicBrainz, Audius, Wikipedia (open); Apple Music/iTunes, Deezer, Discogs (partial); Last.fm, YouTube Data API, Spotify (keys). Wikipedia, MusicBrainz, Deezer, iTunes and Audius supply profiles and songs; Deezer and Audius supply fan counts.
**Everything else** is honestly labelled: licensed analytics (Chartmetric, Soundcharts, Viberate, Luminate...), regional platforms with no public API (Boomplay, Mdundo...), rights societies (MCSK, COSOTA, UPRS, SAMRO...), radio and TV charts, live and ticketing, open data (ListenBrainz...). Many are Manual import: analysts record figures with their name as the source. Audiomack's Data API is OAuth-based and approval-only, so it is Planned. These adapters were not run against live services during development; use **Test connection** and re-read each provider's terms.

## 11. How the logic works
**Discovery run:** search providers per country/genre, de-duplicate artists, collect audience signals (exact-name matches), enrich new artists (biography, picture, links, songs). Each run adds data points, so history builds over time.
**Momentum:** 30-day audience change (partial windows labelled; under 7 days is n/a). **Evidence (0-1):** 0.35 history length (90 days = full) + 0.25 distinct signals (3 = full) + 0.20 human review + 0.20 audio measured.
**Flags:** sudden single-step jump, inconsistent platform growth, UGC concentration (top 3 at 60% or more). Each has a confidence and innocent explanations; engagement, geography and account-level checks are listed as Not available until data exists.
**Artistic score:** human reviews only (1-5 per criterion to 0-100), mapped to four pillars and weighted in Settings (presets included).
**Tiers (first match):** MORE EVIDENCE (evidence under 0.40, no artistic score, or fewer reviews than required) → WATCH (flag at 0.5+) → PURSUE (artistic 70+ and growth over 5%) → MEET (artistic 65+ or growth over 15%) → WATCH. Thresholds are editable.
**Song Lab:** WAV files are read with Python's standard library; other audio and video need ffmpeg. Measurements: duration, RMS level (not LUFS), sample peak (not true-peak), crest factor, clipping, silence, dynamic range, and an envelope-based tempo estimate marked low confidence. Technical checks cover sample rate, bit depth, peak ceiling and clipping. Rights declarations (master holder, splits, samples) are stored as declared. Links are read only through fixed, allow-listed platform endpoints (never arbitrary URLs).
**Review tasks:** artists whose latest decision keeps them in the pipeline get weekly and bimonthly (default 15 days) tasks. **Retention:** old observations are purged by the daily monitoring pass.

## 12. API reference
Base `/api`, JSON, session cookie; every write needs `X-CSRF-Token`. Roles: public / any / reviewer / admin.
| Endpoint | Role | Purpose |
|---|---|---|
| `POST /auth/login`, `/auth/accept-invite` | public | sign in; accept invite |
| `POST /auth/logout`, `GET /auth/me`, `/auth/sessions`, `DELETE /auth/sessions`, `POST /auth/change-password`, `/auth/mfa/setup`, `/auth/mfa/enable` | any | session, password, MFA |
| `GET /meta` | any | regions, countries, genres, workspace |
| `GET /artists` (`country`, `genre`, `stage`, `q`, `limit`, `offset`) | any | artist cards |
| `GET /artists/<id>?days=` | any | dossier: profile, songs, assessment, series, reviews, measurements, media, decisions |
| `POST /discovery/run` (`country`, `genre`, `q`) | reviewer | run discovery (3 per 10 min) |
| `GET /discovery/runs` | any | history |
| `PATCH /artists/<id>`, `POST /artists/<id>/enrich` | reviewer | edit story/genres/city/picture; refresh profile and songs |
| `POST /artists/<id>/reviews`, `/observations`, `/observations/bulk` | reviewer | human review; import figures |
| `POST /artists/<id>/media` (multipart), `/media/link`; `GET /media/<id>/file`; `DELETE /media/<id>` | reviewer / any | Song Lab |
| `GET /recommendations`, `/models`, `/decisions`, `/tasks` | any | tiers, model status, signed decisions, review tasks |
| `POST /decisions`, `/tasks/<id>/done` | reviewer | record decision; complete task |
| `GET /settings`; `PUT /settings/<discovery\|weights\|thresholds\|automation\|workspace>` | reviewer / admin | settings (validated) |
| `GET /providers`; `PUT/DELETE /providers/<name>/credentials`; `POST /providers/<name>/test` | reviewer / admin | provider status, write-only credentials, tests |
| `GET /users`, `POST /users/invite`, `PATCH /users/<id>`, `GET /audit`, `GET /export/artists`, `GET /system` | admin | team, audit, export, system status |

### 12b. Security
Invite-only accounts; scrypt hashes; opaque server-side sessions in HttpOnly SameSite cookies (Secure in production), 8-hour lifetime, revocable; optional TOTP MFA; CSRF token plus Origin check on writes; role checks per request; rate limits (global, login, discovery, uploads, provider tests); strict CORS and CSP (images and media allow https, frames only YouTube and Spotify embeds); parameterised SQL; strict validation; **only https links are stored or rendered**; Fernet-encrypted write-only provider credentials (never returned, logged or audited); uploads limited by content sniffing, 25 MB, random names outside the web root, rights confirmation required; link analysis never fetches arbitrary user URLs; hash-chained audit log and SHA-256-signed decisions; generic client errors.

## 13. Honest limits
- Audience history starts at the first run and is never back-filled.
- No machine pillar scores: Song Lab measurements are about the supplied file and are shown separately from human scores. Tempo is an estimate, loudness is an RMS proxy, peak is sample peak.
- Video analysis covers the audio track only. Non-WAV audio and video need ffmpeg. Extra features need librosa (not run during development).
- Predictive models are not trained; tiers are rule-based and editable.
- Provider adapters were tested with fakes, not live services. Biographies come only from pages that clearly describe a musician; matching is by exact name.
- Previews are short samples; some artists have none. UGC is manual or CSV import until an approved TikTok/Instagram/Shorts source is connected.
- The Africa map is a coarse outline for bubble maps. Home-page photos are Unsplash links that were not verified; they hide gracefully if blocked.
- Single workspace, SQLite, single process. The front end was exercised in a simulated browser (all screens, no errors) but not in real browsers or on small phones.
- Demo artists and their numbers are fictional and synthetic.

## 14. Operations
```bash
python manage.py create-admin you@company.com | set-password <email> | seed-demo | clear-demo
python manage.py discover | monitor | scheduler | backup
```
**Backups:** `manage.py backup` (cron it), plus the Fernet key and `uploads/`. **Restore:** stop, copy the snapshot over `MSANII_DB`, start. **Upgrades:** new tables and columns are added automatically at start-up; back up first. **Checklist:** production env and key; TLS; exact allowed origins; one worker, one scheduler; real contact; SMTP if wanted; owner password changed and MFA on; backups scheduled; provider terms reviewed.

## 15. Testing
`python -m unittest discover -s tests -t .` covers auth, CSRF and Origin, roles, discovery to tier, decisions, audit tamper detection, credential secrecy, headers and CORS, injection-style input, upload validation and real WAV analysis, link allow-listing, unsafe-URL rejection, profile enrichment, bulk import, password change, MFA, demo data, review tasks, settings validation, invites and the provider catalogue. `npm run build` compiles the front end.

## 16. Troubleshooting
| Symptom | Fix |
|---|---|
| Signed out right after login | Production mode over http drops Secure cookies: use HTTPS or unset `MSANII_ENV` locally |
| `403 origin not allowed` | add the exact origin to `MSANII_ALLOWED_ORIGINS`; set `MSANII_PROXIES=1` behind a trusted proxy |
| `403 csrf check failed` | sign in again; custom clients must send `X-CSRF-Token` |
| `429` on login | 5 attempts per 5 minutes per account |
| Discover is empty | run discovery, widen filters, or `seed-demo` |
| No songs or biography | click *Refresh profile and songs*; check provider messages in Discover history |
| Every artist says MORE EVIDENCE | expected at first: add a human review and let history build |
| Song Lab says ffmpeg missing | install ffmpeg (Docker image has it) or upload 16-bit WAV |
| Credentials unreadable after restore | Fernet key differs from the one used to save them |
| `database is locked` | one web worker and one scheduler only |
| Old UI after a change | `npm run build`, then hard-refresh |

## 17. Roadmap
Live UGC through an approved provider; adapters for Audiomack, SoundCloud, Genius and others in the catalogue; historical back-fill; Redis rate limiting; recommendation-outcome tracking; predictive trainer once history exists; Postgres and row-level policies; front-end tests; Swahili localisation; real-browser and mobile QA.

*Add your own license file before sharing the code outside your organisation.*
# MSANII_01
