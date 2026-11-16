# MSANII

**Discover. Understand. Back the Next Big Sound.**

MSANII is an enterprise A&R (Artist & Repertoire) intelligence platform built to discover, analyze, and financially evaluate emerging musical talent across Africa, with a core focus on East Africa. 

By combining multi-source streaming ingestion, acoustic science forensics, and machine learning breakout models, MSANII equips talent scouts and record labels with actionable, data-backed artist dossiers.

---

## Key Capabilities

- **Upcoming Artist Discovery:** Focuses on emerging talent within their first 5 years of industry release history, filtering out catalog-established veterans.
- **Machine Learning Breakout Scoring:** Evaluates 30-day velocity, creator diversity, and acoustic uniqueness to compute predictive breakout probabilities.
- **Song Lab & Psychoacoustic Forensics:** Deep audio track analysis assessing dynamic range, peak ceiling, stem occupancy, and CREPE vocal intonation.
- **Algorithmic A&R Deal Valuation:** Interactive deal simulator projecting recoupment velocity, benchmark signing advances, and flexible royalty splits.
- **Data Source Telemetry:** Catalogues 76+ data providers across global streaming, regional African platforms, social video, and rights societies.
- **Explainable Recommendation Pipeline:** Transparent four-tier decision framework (`PURSUE`, `MEET`, `WATCH`, `MORE EVIDENCE`) backed by cryptographic audit logging.

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

MSANII is optimized for zero-configuration serverless deployment on **Vercel** with **Supabase PostgreSQL**.

1. **Supabase Database:** Execute `supabase_schema.sql` in the Supabase SQL Editor.
2. **Environment Variables:** Set `SUPABASE_DB_URL`, `SECRET_KEY`, `MSANII_FERNET_KEY`, and `MSANII_ALLOWED_ORIGINS` in your hosting dashboard (e.g., Vercel Project Settings).
3. **Deploy:** Deploy directly via Vercel CLI (`vercel --prod`) or connect your GitHub repository.

---

## Confidentiality & License

Proprietary and confidential. Internal music scouting platform. All rights reserved.
