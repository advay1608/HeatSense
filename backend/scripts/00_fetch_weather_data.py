"""
00_fetch_weather_data.py
-------------------------
Fetches real, all-time historical daily maximum temperature data from the
Open-Meteo Historical Weather Archive API (powered by ECMWF ERA5 reanalysis).

Replaces synthetic/placeholder data with genuine, citable public meteorological
records across all available years (1950 to present day).

Usage:
    python backend/scripts/00_fetch_weather_data.py
    python backend/scripts/00_fetch_weather_data.py --city mumbai
    python backend/scripts/00_fetch_weather_data.py --lat 28.6139 --lon 77.2090 --name "New Delhi"
    python backend/scripts/00_fetch_weather_data.py --start-date 1980-01-01
"""

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
import pandas as pd

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
from common import DATA_PATH, write_result

METADATA_PATH = os.path.join(os.path.dirname(DATA_PATH), "dataset_metadata.json")

# Predefined city coordinates for urban heat risk analysis
PRESET_CITIES = {
    "delhi": {
        "name": "New Delhi, India",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "description": "National Capital Region experiencing intense Urban Heat Island (UHI) dynamics and extreme summer heatwaves.",
    },
    "mumbai": {
        "name": "Mumbai, India",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "description": "Coastal megacity with high humidity and prolonged thermal discomfort.",
    },
    "bengaluru": {
        "name": "Bengaluru, India",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "description": "Deccan plateau urban center undergoing rapid microclimate warming from urban expansion.",
    },
    "chennai": {
        "name": "Chennai, India",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "description": "Tropical coastal metropolitan area vulnerable to humid heat stress.",
    },
    "kolkata": {
        "name": "Kolkata, India",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "description": "Eastern Gangetic delta urban zone with compound heat-humidity extremes.",
    },
    "phoenix": {
        "name": "Phoenix, Arizona, USA",
        "latitude": 33.4484,
        "longitude": -112.0740,
        "description": "Sonoran desert metropolis with severe prolonged extreme heat records.",
    },
    "london": {
        "name": "London, United Kingdom",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "description": "Temperate urban hub seeing unprecedented 40C heatwave spikes in recent years.",
    },
    "madrid": {
        "name": "Madrid, Spain",
        "latitude": 40.4168,
        "longitude": -3.7038,
        "description": "Inland Iberian plateau city subject to intense Mediterranean heatwaves.",
    },
    "tokyo": {
        "name": "Tokyo, Japan",
        "latitude": 35.6762,
        "longitude": 139.6503,
        "description": "High-density East Asian megacity with significant urban heat entrapment.",
    },
}


def fetch_open_meteo_archive(
    latitude: float,
    longitude: float,
    start_date: str = "1950-01-01",
    end_date: str = None,
    max_retries: int = 3,
) -> dict:
    """Queries Open-Meteo Historical Archive API for daily maximum temperatures."""
    if end_date is None:
        # Open-Meteo ERA5 archive is typically available up to 2-3 days prior to current date
        end_date = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")

    base_url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max",
        "timezone": "auto",
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    print(f"[API Fetcher] Querying Open-Meteo Archive:")
    print(f"             URL: {url}")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "HeatSense-Academic-Project/1.0 (Stats&Prob Module 2)"},
    )

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data
        except Exception as e:
            last_err = e
            print(f"[API Fetcher] Attempt {attempt}/{max_retries} failed: {e}. Retrying in 2s...")
            time.sleep(2)

    raise RuntimeError(f"Failed to fetch data from Open-Meteo API after {max_retries} attempts: {last_err}")


def ingest_data(
    city_key: str = "delhi",
    latitude: float = None,
    longitude: float = None,
    location_name: str = None,
    start_date: str = "1950-01-01",
    end_date: str = None,
) -> pd.DataFrame:
    """Fetches real weather data, cleans, validates schema, and saves to CSV."""
    if latitude is not None and longitude is not None:
        lat, lon = latitude, longitude
        name = location_name or f"Coordinates ({lat}, {lon})"
        desc = "Custom user-selected coordinates."
    else:
        city_info = PRESET_CITIES.get(city_key.lower(), PRESET_CITIES["delhi"])
        lat = city_info["latitude"]
        lon = city_info["longitude"]
        name = city_info["name"]
        desc = city_info["description"]

    print(f"[API Fetcher] Location selected: {name} (Lat: {lat}, Lon: {lon})")
    api_response = fetch_open_meteo_archive(lat, lon, start_date=start_date, end_date=end_date)

    daily = api_response.get("daily", {})
    times = daily.get("time", [])
    temps = daily.get("temperature_2m_max", [])

    if not times or not temps or len(times) != len(temps):
        raise ValueError(f"Malformed API response: times={len(times)}, temps={len(temps)}")

    records = []
    for d_str, t_val in zip(times, temps):
        if t_val is not None and not pd.isna(t_val):
            records.append({"date": d_str, "max_temp_c": round(float(t_val), 1)})

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").drop_duplicates(subset=["date"]).reset_index(drop=True)

    # Format date back to ISO string YYYY-MM-DD
    df_csv = pd.DataFrame({
        "date": df["date"].dt.strftime("%Y-%m-%d"),
        "max_temp_c": df["max_temp_c"]
    })

    # Save to dataset.csv
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    df_csv.to_csv(DATA_PATH, index=False)
    print(f"[API Fetcher] Successfully saved {len(df_csv):,d} valid records to:")
    print(f"             {DATA_PATH}")

    # Generate metadata file
    meta = {
        "location_name": name,
        "latitude": lat,
        "longitude": lon,
        "elevation_m": api_response.get("elevation", None),
        "timezone": api_response.get("timezone", "auto"),
        "start_date": df_csv["date"].iloc[0],
        "end_date": df_csv["date"].iloc[-1],
        "total_observations": len(df_csv),
        "temperature_stats": {
            "min_c": float(df_csv["max_temp_c"].min()),
            "max_c": float(df_csv["max_temp_c"].max()),
            "mean_c": round(float(df_csv["max_temp_c"].mean()), 2),
            "std_c": round(float(df_csv["max_temp_c"].std()), 2),
        },
        "source": "Open-Meteo Historical Weather Archive API",
        "underlying_model": "ECMWF ERA5 Reanalysis (0.25 deg grid resolution)",
        "citation": (
            f"Open-Meteo.com Historical Weather Archive API (ERA5 Reanalysis by ECMWF). "
            f"Data retrieved for {name} ({lat} N, {lon} E) spanning {df_csv['date'].iloc[0]} "
            f"to {df_csv['date'].iloc[-1]}."
        ),
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "description": desc,
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[API Fetcher] Metadata recorded -> {METADATA_PATH}")

    # Write dataset_info directly into shared results.json
    write_result("dataset_info", meta)

    return df_csv


def main():
    parser = argparse.ArgumentParser(description="Fetch all-time daily temperature data from Open-Meteo API.")
    parser.add_argument("--city", default="delhi", choices=list(PRESET_CITIES.keys()),
                        help=f"Preset city to fetch (default: delhi). Options: {', '.join(PRESET_CITIES.keys())}")
    parser.add_argument("--lat", type=float, default=None, help="Custom latitude")
    parser.add_argument("--lon", type=float, default=None, help="Custom longitude")
    parser.add_argument("--name", type=str, default=None, help="Custom location name")
    parser.add_argument("--start-date", default="1950-01-01", help="Start date in YYYY-MM-DD (default: 1950-01-01)")
    parser.add_argument("--end-date", default=None, help="End date in YYYY-MM-DD (default: latest available)")

    args = parser.parse_args()
    ingest_data(
        city_key=args.city,
        latitude=args.lat,
        longitude=args.lon,
        location_name=args.name,
        start_date=args.start_date,
        end_date=args.end_date,
    )


if __name__ == "__main__":
    main()
