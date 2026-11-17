# MSANII

**Discover. Understand. Back the Next Big Sound.**

MSANII is an enterprise A&R (Artist & Repertoire) intelligence platform built to discover, analyze, and financially evaluate emerging musical talent across Africa, with a core focus on East Africa. 

By combining multi-source streaming ingestion, acoustic science forensics, and machine learning breakout models, MSANII equips talent scouts and record labels with actionable, data-backed artist dossiers.

---

## Key Capabilities

- **Upcoming Artist Discovery:** Finds emerging artists (about five years or less of career) from free public sources. Where a career start year is unknown the artist is shown as "start year unknown" rather than guessed.
- **Evidence-first recommendations:** Four tiers (`PURSUE`, `MEET`, `WATCH`, `MORE EVIDENCE`) built from human A&R reviews and observed audience growth. Missing data lowers confidence and never raises a score. A heuristic breakout score can support `MEET` but can never promote an artist to `PURSUE` without growth evidence.
- **Song Lab:** Measures tempo, key, a loudness proxy and clipping from rights-cleared uploads, each with its method, confidence and caveat. Pitch accuracy (CREPE) and stem separation (Demucs) are **not implemented**.
- **Scenario calculator:** An assumption-driven advance and recoupment calculator. The assumptions are shown with the result; it is a negotiating aid, not a valuation.
- **Forecast:** Log-linear audience trend with a 95% prediction interval from the fitted residuals. No forecast is produced with fewer than 4 observations over 7 days.
- **Data providers:** A catalogue of about 90 candidate sources with an honest status for each; roughly a dozen are actually implemented.
- **Tamper-evident audit log:** A hash-chained log of security-relevant events. It detects casual edits; it is not keyed, so someone with database write access could rebuild it.

### What is not a trained model
There are no outcome labels in the database, so nothing is fitted and no accuracy is reported. The breakout score is a hand-weighted logistic heuristic (`msanii/ml.py`), labelled uncalibrated everywhere it appears. Demo artists (fictional, flagged `demo`) show fixed sample visuals behind an "Illustrative sample data" banner; real artists never do.

---

## Tech Stack

- **Backend:** Python 3.10+ / Flask 3.0+
- **Frontend:** React 18, Vite 5, Custom SVG Visualization Engine
- **Database:** Supabase PostgreSQL (Production) / SQLite WAL (Local Development)
- **Audio Forensics:** Python wave/audioop & FFmpeg
- **Deployment:** Vercel Serverless WSGI / Docker

---

## Quick Start (Local Development)

### 1. Prerequisites
- Python 3.10 or higher
- Node.js 18+ & npm
- FFmpeg (optional, for non-WAV audio and video decoding)

### 2. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt


# Start the Flask API
flask --app msanii run --port 5000
```

### 3. Frontend Development
```bash
# In a separate terminal:
cd frontend
npm install
npm run dev                     # Starts dev server on http://localhost:5173
```
To compile production assets for Flask / Vercel:
```bash
cd frontend && npm run build
```

---

## Deployment & Database Setup

### Vercel + Supabase
1. **Database schema:** run `supabase_schema.sql` once (Supabase SQL editor, or `SUPABASE_DB_URL=... python manage.py migrate-pg`). It is idempotent. It enables row level security on every table with **no policies** and revokes `anon`/`authenticated` privileges: the app connects directly with its own role, never through the Supabase Data API. Do not add `USING (true)` policies.
2. **Vercel environment variables** (Project > Settings > Environment Variables, Production and Preview): `SUPABASE_DB_URL` (pooler URI, port 6543), `MSANII_FERNET_KEY`, `MSANII_ALLOWED_ORIGINS`, `MSANII_BASE_URL`, and for the first deploy only `MSANII_ADMIN_EMAIL` + `MSANII_ADMIN_PASSWORD`. Remove the password variable after the first sign-in. See `.env.example`. `vercel.json` no longer carries an `env` block: it is not applied at runtime.
3. **Deploy** by pushing to the connected GitHub branch (or `vercel --prod`).
4. **Know the limits of serverless:** the filesystem is ephemeral (`/tmp`), request bodies are capped (about 4.5 MB), there is no background scheduler, and heavy audio analysis (librosa) does not fit. Song Lab uploads and autonomous discovery need the Docker deployment below, or an external worker.

### Docker (full feature set)
`docker build -t msanii . && docker run -p 5000:5000 -v msanii-data:/data -e MSANII_FERNET_KEY=... -e MSANII_ADMIN_EMAIL=... -e MSANII_ADMIN_PASSWORD=... msanii` runs the web server and the scheduler in one container with SQLite on the volume, or set `SUPABASE_DB_URL` to use Supabase.

### Access requests
Applicants submit the form on the login page; administrators are notified by e-mail (if SMTP is configured) and approve inside the app. Approval creates a single-use 72-hour invite and the applicant chooses their own password. No password is ever generated or e-mailed.

### Tests
`python -m pytest` runs on SQLite. To run the same suite on PostgreSQL: `MSANII_TEST_PG_URL=postgresql://... python -m pytest` (the schema is rebuilt for each test, so use a throw-away database).

---

## Confidentiality & License

Proprietary and confidential. Internal music scouting platform. All rights reserved.
