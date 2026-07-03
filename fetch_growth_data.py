"""
fetch_growth_data.py

Pulls LIVE metro-area population estimates from the U.S. Census Bureau's
Population Estimates Program (PEP) API and computes year-over-year growth
for each of the 11 metros in data/cities_data.csv.

Why only this piece is "live":
Zillow, Redfin, Walk Score, and GreatSchools do not offer free, self-serve
public APIs (Walk Score's costs money past a tiny free tier; GreatSchools
requires a partner application; Zillow/Redfin have none at all). The Census
Bureau, on the other hand, publishes population data through a genuinely
free public API. This script is the real, working "live data pull" --
everything else in this project is a manually-curated snapshot (clearly
labeled as such) that you refresh periodically from Redfin's Data Center
(redfin.com/news/data-center) or Zillow Research (zillow.com/research/data).

Usage:
    python scripts/fetch_growth_data.py

Optional but recommended: get a free Census API key (instant, no approval
wait) at https://api.census.gov/data/key_signup.html and set it as an
environment variable so you don't get rate-limited:
    export CENSUS_API_KEY="your_key_here"

Output:
    Overwrites the `population_growth_pct` column in data/cities_data.csv
    with fresh figures, and leaves every other column untouched.
"""

import os
import sys
import time
import requests
import pandas as pd

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cities_data.csv")

# CBSA (Core-Based Statistical Area) codes for each metro in our dataset.
# These rarely change, but if the Census Bureau ever redefines a metro's
# boundaries, cross-check at https://www.census.gov/geographies/reference-files/time-series/demo/metro-micro/delineation-files.html
CBSA_CODES = {
    "Seattle": "42660",        # Seattle-Tacoma-Bellevue, WA
    "Los Angeles": "31080",    # Los Angeles-Long Beach-Anaheim, CA
    "Houston": "26420",        # Houston-The Woodlands-Sugar Land, TX
    "Atlanta": "12060",        # Atlanta-Sandy Springs-Alpharetta, GA
    "Phoenix": "38060",        # Phoenix-Mesa-Chandler, AZ
    "San Antonio": "41700",    # San Antonio-New Braunfels, TX
    "Raleigh": "39580",        # Raleigh-Cary, NC
    "Hampton Roads": "47260",  # Virginia Beach-Norfolk-Newport News, VA-NC
    "Oakland": "41860",        # San Francisco-Oakland-Berkeley, CA (Oakland is part of this CBSA)
    "Tampa": "45300",          # Tampa-St. Petersburg-Clearwater, FL
    "Richmond": "40060",       # Richmond, VA
}

# The PEP vintage endpoint changes each year as the Census Bureau rolls
# forward. As of mid-2026 the latest available vintage is 2024. Update
# this if the script starts returning 404s.
PEP_VINTAGE_YEAR = 2024
BASE_URL = f"https://api.census.gov/data/{PEP_VINTAGE_YEAR}/pep/population"


def fetch_metro_population(cbsa_code: str, api_key: str | None) -> dict | None:
    """Fetch current-vintage and prior-year population for one metro."""
    params = {
        "get": "NAME,POP_2024,POP_2023",
        "for": f"metropolitan statistical area/micropolitan statistical area:{cbsa_code}",
    }
    if api_key:
        params["key"] = api_key

    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        rows = resp.json()
        header, values = rows[0], rows[1]
        record = dict(zip(header, values))
        return {
            "name": record.get("NAME"),
            "pop_current": float(record.get("POP_2024", 0) or 0),
            "pop_prior": float(record.get("POP_2023", 0) or 0),
        }
    except Exception as e:  # noqa: BLE001 - we want to fall back gracefully, not crash
        print(f"  [warn] Census fetch failed for CBSA {cbsa_code}: {e}")
        return None


def main():
    api_key = os.environ.get("CENSUS_API_KEY")
    if not api_key:
        print("No CENSUS_API_KEY set (still works, just rate-limited on shared IPs).")
        print("Get a free key: https://api.census.gov/data/key_signup.html\n")

    if not os.path.exists(CSV_PATH):
        print(f"Could not find {CSV_PATH}. Run this from the project root.")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)
    updated = 0

    for city, cbsa in CBSA_CODES.items():
        print(f"Fetching {city} (CBSA {cbsa})...")
        result = fetch_metro_population(cbsa, api_key)
        time.sleep(0.3)  # be polite to the API

        if result and result["pop_prior"] > 0:
            growth_pct = round(
                (result["pop_current"] - result["pop_prior"]) / result["pop_prior"] * 100, 2
            )
            df.loc[df["city"] == city, "population_growth_pct"] = growth_pct
            updated += 1
            print(f"  -> {growth_pct}% YoY growth (live)")
        else:
            existing = df.loc[df["city"] == city, "population_growth_pct"]
            fallback = existing.values[0] if len(existing) else "N/A"
            print(f"  -> using existing snapshot value: {fallback}% (fetch failed)")

    df.to_csv(CSV_PATH, index=False)
    print(f"\nDone. Live-updated {updated}/{len(CBSA_CODES)} metros.")
    print(f"Saved to {CSV_PATH}")


if __name__ == "__main__":
    main()
