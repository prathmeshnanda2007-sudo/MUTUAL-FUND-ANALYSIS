"""
run_pipeline.py
===============
Master execution script for the Bluestock MF Analysis pipeline.
Runs all phases in sequence with status reporting.

Usage:
    python run_pipeline.py              # Run all phases
    python run_pipeline.py --phase 1    # Run only Day 1 (data ingestion)
    python run_pipeline.py --phase 2    # Run only Day 2 (ETL + DB)
"""

import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_script(script_path: Path, description: str) -> bool:
    """
    Run a Python script as a subprocess.

    Args:
        script_path: Path to the .py script.
        description: Human-readable description for logging.

    Returns:
        True if script exited with code 0, False otherwise.
    """
    logger.info(f"\n{'=' * 60}")
    logger.info(f"  RUNNING: {description}")
    logger.info(f"  Script:  {script_path.name}")
    logger.info(f"{'=' * 60}")

    start = time.time()
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(BASE_DIR),
        capture_output=False,
    )
    elapsed = time.time() - start

    if result.returncode == 0:
        logger.info(f"  DONE in {elapsed:.1f}s")
        return True
    else:
        logger.error(f"  FAILED (exit code {result.returncode}) after {elapsed:.1f}s")
        return False


def phase_1_data_ingestion() -> bool:
    """Phase 1: Fetch live NAV + run data ingestion diagnostics."""
    success = True
    success &= run_script(
        BASE_DIR / "scripts" / "live_nav_fetch.py",
        "Live NAV Fetch (mfapi.in)"
    )
    success &= run_script(
        BASE_DIR / "scripts" / "data_ingestion.py",
        "Data Ingestion Diagnostics"
    )
    return success


def phase_2_etl() -> bool:
    """Phase 2: Clean data + load to SQLite."""
    return run_script(
        BASE_DIR / "scripts" / "etl_pipeline.py",
        "ETL Pipeline (Clean + Load SQLite)"
    )


def phase_3_recommender_demo() -> bool:
    """Phase 3 quick demo: Test recommender."""
    logger.info("\nRecommender demo (Low risk):")
    result = subprocess.run(
        [sys.executable, str(BASE_DIR / "scripts" / "recommender.py"), "--risk", "Moderate"],
        cwd=str(BASE_DIR),
        capture_output=False,
    )
    return result.returncode == 0


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Bluestock MF Pipeline Runner")
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help="Run specific phase (1=ingestion, 2=ETL, 3=demo). Default: all phases.",
    )
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  BLUESTOCK MUTUAL FUND ANALYSIS — MASTER PIPELINE")
    print("=" * 60)

    phases = {
        1: ("Day 1 — Data Ingestion", phase_1_data_ingestion),
        2: ("Day 2 — ETL + SQLite Load", phase_2_etl),
        3: ("Recommender Demo", phase_3_recommender_demo),
    }

    if args.phase:
        name, fn = phases[args.phase]
        logger.info(f"Running Phase {args.phase}: {name}")
        success = fn()
        sys.exit(0 if success else 1)

    # Run all phases
    results = {}
    for phase_num, (name, fn) in phases.items():
        logger.info(f"\n>>> Phase {phase_num}: {name}")
        results[name] = fn()

    # Summary
    print("\n" + "=" * 60)
    print("  PIPELINE SUMMARY")
    print("=" * 60)
    all_ok = True
    for name, ok in results.items():
        status = "PASSED" if ok else "FAILED"
        print(f"  {status:<8}  {name}")
        if not ok:
            all_ok = False

    print("=" * 60)
    if all_ok:
        print("  All phases completed successfully.")
    else:
        print("  Some phases failed. Check logs above.")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
