"""
live_nav_fetch.py
=================
Fetches live NAV data from mfapi.in for 6 key mutual fund schemes.
Saves raw JSON and parsed CSV to data/raw/.

Usage:
    python scripts/live_nav_fetch.py
"""

import requests
import json
import csv
import logging
from pathlib import Path
from datetime import datetime

# ── Setup ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Fund registry ──────────────────────────────────────────────────────────────
SCHEMES = {
    125497: "HDFC_Top_100_Direct",
    119551: "SBI_Bluechip_Direct",
    120503: "ICICI_Pru_Bluechip_Direct",
    118632: "Nippon_Large_Cap_Direct",
    119092: "Axis_Bluechip_Direct",
    120841: "Kotak_Bluechip_Direct",
}

MFAPI_BASE = "https://api.mfapi.in/mf"


# ── Core fetch function ─────────────────────────────────────────────────────────
def fetch_nav(scheme_code: int) -> dict:
    """
    Fetch NAV history for a given AMFI scheme code from mfapi.in.

    Args:
        scheme_code: AMFI numeric scheme code.

    Returns:
        Parsed JSON response dict with 'meta' and 'data' keys.

    Raises:
        requests.HTTPError: If the API returns a non-200 status.
    """
    url = f"{MFAPI_BASE}/{scheme_code}"
    logger.info(f"Fetching NAV for scheme {scheme_code} → {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
    logger.info(
        f"  ✓ {data['meta']['scheme_name']} — {len(data['data'])} NAV records retrieved"
    )
    return data


def save_raw_json(data: dict, scheme_code: int) -> Path:
    """
    Save the raw JSON API response to data/raw/.

    Args:
        data: Parsed JSON dict from mfapi.in.
        scheme_code: AMFI scheme code (used in filename).

    Returns:
        Path to the saved JSON file.
    """
    filename = RAW_DIR / f"nav_live_{scheme_code}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"  Saved raw JSON → {filename.name}")
    return filename


def save_parsed_csv(data: dict, scheme_code: int, scheme_label: str) -> Path:
    """
    Parse the mfapi JSON response and save as a tidy CSV.

    Columns: amfi_code, scheme_name, fund_house, scheme_category, date, nav

    Args:
        data: Parsed JSON dict from mfapi.in.
        scheme_code: AMFI scheme code.
        scheme_label: Human-readable scheme label for the filename.

    Returns:
        Path to the saved CSV file.
    """
    meta = data["meta"]
    records = data["data"]

    filename = RAW_DIR / f"nav_live_{scheme_label}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["amfi_code", "scheme_name", "fund_house", "scheme_category", "date", "nav"],
        )
        writer.writeheader()
        for row in records:
            writer.writerow(
                {
                    "amfi_code": scheme_code,
                    "scheme_name": meta["scheme_name"],
                    "fund_house": meta["fund_house"],
                    "scheme_category": meta["scheme_category"],
                    "date": row["date"],
                    "nav": row["nav"],
                }
            )
    logger.info(f"  Saved parsed CSV → {filename.name} ({len(records)} rows)")
    return filename


def fetch_all_schemes() -> list[dict]:
    """
    Fetch NAV data for all registered schemes and save raw + parsed files.

    Returns:
        List of meta dicts for all successfully fetched schemes.
    """
    results = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"=== Live NAV Fetch Started: {timestamp} ===")
    logger.info(f"Schemes to fetch: {len(SCHEMES)}")

    for code, label in SCHEMES.items():
        try:
            data = fetch_nav(code)
            save_raw_json(data, code)
            save_parsed_csv(data, code, label)

            # Collect summary
            latest = data["data"][0]  # mfapi returns newest first
            results.append(
                {
                    "amfi_code": code,
                    "scheme_label": label,
                    "scheme_name": data["meta"]["scheme_name"],
                    "fund_house": data["meta"]["fund_house"],
                    "latest_date": latest["date"],
                    "latest_nav": float(latest["nav"]),
                    "total_records": len(data["data"]),
                }
            )
        except requests.RequestException as e:
            logger.error(f"  ✗ Failed to fetch scheme {code}: {e}")
        except Exception as e:
            logger.error(f"  ✗ Unexpected error for scheme {code}: {e}")

    # Save combined summary CSV
    if results:
        summary_path = RAW_DIR / "nav_live_summary.csv"
        with open(summary_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        logger.info(f"\n=== Summary saved → {summary_path.name} ===")

    # Print summary table
    print("\n" + "=" * 80)
    print(f"{'AMFI Code':<12} {'Scheme Label':<35} {'Latest Date':<14} {'Latest NAV':>12}")
    print("-" * 80)
    for r in results:
        print(f"{r['amfi_code']:<12} {r['scheme_label']:<35} {r['latest_date']:<14} {r['latest_nav']:>12.4f}")
    print("=" * 80)
    print(f"\nSuccessfully fetched {len(results)}/{len(SCHEMES)} schemes")

    return results


# ── Entry point ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    fetch_all_schemes()
