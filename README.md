# 🛰️ Metro Intelligence Dashboard

An interactive Streamlit dashboard comparing 11 U.S. metros (Seattle, LA, Houston,
Atlanta, Phoenix, San Antonio, Raleigh-Durham, Hampton Roads, Oakland, Tampa,
Richmond) on home prices, walkability, school quality, and growth momentum —
with an adjustable scoring engine that recommends the best-fit city for a
**first-time buyer** or an **investor**, sliders and all.

![status](https://img.shields.io/badge/status-ready--to--deploy-00E5FF)

## What's real-time vs. curated

Being upfront about this, since it matters:

| Data | Source | Refresh |
|---|---|---|
| Population growth | U.S. Census Bureau PEP API (free, public) | **Live** — run `scripts/fetch_growth_data.py` |
| Home prices, walkability, school scores | Redfin, Zillow, Walk Score, school-district research | Curated snapshot (mid-2026), stored in `data/cities_data.csv` |

Zillow, Redfin, Walk Score, and GreatSchools don't offer free self-serve public
APIs (Walk Score's is paid past a tiny free tier; GreatSchools requires a
partner application; Zillow/Redfin have none). So those columns are a manually
maintained CSV you refresh periodically — the dashboard itself and the scoring
engine are fully live/interactive, it's just the underlying price/school/walk
figures that need a periodic manual update rather than a real-time pull.

**To keep it current:** update `data/cities_data.csv` every month or so from
[Redfin's Data Center](https://www.redfin.com/news/data-center) and
[Zillow Research](https://www.zillow.com/research/data/) (both publish free
downloadable CSVs). If you get a Walk Score or GreatSchools API key later,
it's a five-minute edit to `fetch_growth_data.py`-style scripts to pull those
live too.

## Features

- 🎛️ **Buyer Profile presets** (First-Time Buyer / Investor / Custom) that set
  sensible default priority weights
- 🎚️ **Adjustable sliders** for Affordability / Growth / Walkability / Schools
- 💵 **Budget slider** and **Match % filter dropdown**
- 🗺️ Dark-mode interactive map sized/colored by composite match score
- 📊 Ranked bar chart, radar chart (top 3 comparison), and two scatter plots
- 🏆 Auto-generated recommendation card with data-backed rationale bullets
- 🌌 Custom "high-tech" dark theme (glassmorphism cards, neon gradient accents)

## Run locally

```bash
git clone <your-repo-url>
cd city-dashboard
pip install -r requirements.txt
streamlit run app.py
```

## Refresh live population growth data

```bash
export CENSUS_API_KEY="your_free_key"   # optional but recommended
python scripts/fetch_growth_data.py
```

Get a free Census API key instantly (no approval wait) at
https://api.census.gov/data/key_signup.html

## Deploy to Streamlit Community Cloud (free)

1. Push this folder to a new GitHub repo:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Metro Intelligence Dashboard"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git push -u origin main
   ```
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub.
3. Click **New app**, pick your repo/branch, set the main file to `app.py`.
4. Deploy. Your dashboard gets a public URL like
   `https://<your-app>.streamlit.app`.

## Project structure

```
city-dashboard/
├── app.py                     # Streamlit dashboard
├── data/
│   └── cities_data.csv        # Curated snapshot dataset
├── scripts/
│   └── fetch_growth_data.py   # Live Census population growth puller
├── .streamlit/
│   └── config.toml            # Dark theme config
├── requirements.txt
└── README.md
```

## Customizing the scoring model

The composite score is a weighted blend of four 0–100 normalized sub-scores
(see `score_dataframe()` in `app.py`):

- **Affordability** — inverse of median home price (cheaper = higher score)
- **Growth** — blend of population growth and positive price momentum
- **Walkability** — Walk Score, normalized against the dataset
- **Schools** — school quality score, normalized against the dataset

Add more cities by appending rows to `data/cities_data.csv` — no code changes
needed, the app reads the CSV dynamically.
