"""
Main entry point for Pakistan Autonomous Business & Executive Intelligence System.
Supports autonomous batch discovery, resuming, Excel export, and dashboard launching.
"""

import os
import sys
import argparse
import yaml
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.storage.database import DatabaseManager
from src.processing.batch_runner import BatchRunner
from src.export.excel_exporter import ExcelExporter
from src.export.report_generator import ReportGenerator


def setup_logging(logs_dir: str = "logs") -> None:
    os.makedirs(logs_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(logs_dir, "system.log"), encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_config(config_path: str = "config.yaml") -> dict:
    if not os.path.exists(config_path):
        # Fallback to script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        alt_path = os.path.join(script_dir, config_path)
        if os.path.exists(alt_path):
            config_path = alt_path
        else:
            print(f"Config file not found at {config_path} or {alt_path}")
            sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
        # Normalize relative paths to script directory if needed
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if "paths" in cfg:
            for k, p in cfg["paths"].items():
                if not os.path.isabs(p):
                    cfg["paths"][k] = os.path.join(script_dir, p)
        return cfg


def main():
    parser = argparse.ArgumentParser(
        description="Pakistan Autonomous Business & Executive Intelligence System"
    )
    parser.add_argument(
        "--target",
        type=int,
        default=None,
        help="Target number of authentic companies to discover and verify (e.g. 20, 100, 1000)"
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Start a fresh discovery run without resuming previous batches"
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export current database to 12-sheet Excel file without running discovery"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print quality and geographic summary report to console"
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Launch local Streamlit dashboard"
    )

    args = parser.parse_args()
    config = load_config()
    setup_logging(config.get("paths", {}).get("logs_dir", "logs"))
    logger = logging.getLogger("Main")

    db_path = config.get("paths", {}).get("database", "database/pakistan_business_intelligence.db")
    db = DatabaseManager(db_path)

    if args.dashboard:
        import subprocess
        dashboard_script = os.path.join(os.path.dirname(__file__), "src", "dashboard", "app.py")
        print(f"Launching Streamlit dashboard: {dashboard_script}")
        subprocess.run(["streamlit", "run", dashboard_script])
        return

    if args.report:
        rep_gen = ReportGenerator(db)
        print(rep_gen.generate_markdown_report())
        return

    if args.export:
        exporter = ExcelExporter(db, config.get("paths", {}).get("excel_output", "output/Pakistan_Business_Intelligence.xlsx"))
        path = exporter.export_workbook()
        print(f"\n[SUCCESS] Excel workbook generated at: {path}")
        return

    # Discovery Run
    target = args.target if args.target is not None else config.get("targets", {}).get("total_companies_target", 1000)
    print("=" * 75)
    print(" Pakistan Autonomous Business & Executive Intelligence System")
    print("=" * 75)
    print(f"Target Companies   : {target}")
    print(f"Batch Size         : {config.get('targets', {}).get('batch_size', 50)}")
    print(f"Database Path      : {db_path}")
    print(f"Excel Deliverable  : {config.get('paths', {}).get('excel_output')}")
    print(f"Resuming Run       : {not args.fresh}")
    print("-" * 75)

    runner = BatchRunner(config, db)

    def on_batch_progress(prog):
        print(f"[*] Batch {prog['batch_number']} Done | Processed: {prog['processed']}/{prog['total_pool']} | Confirmed: {prog['confirmed']} | Duplicates: {prog['duplicates']} | Failed: {prog['failed']}")

    result = runner.run_pipeline(
        target_limit=target,
        resume=(not args.fresh),
        progress_callback=on_batch_progress
    )

    print("\n" + "=" * 75)
    print(" Execution Completed Successfully")
    print("=" * 75)
    stats = result["stats"]
    print(f"Total Authentic Companies Discovered : {stats['total_discovered']}")
    print(f"Confirmed Companies (Cat A & B)       : {stats['confirmed_companies']}")
    print(f"Executives / Decision Makers Found   : {stats['total_executives']}")
    print(f"CEOs and Founders Identified         : {stats['total_ceos']}")
    print(f"Business Emails Discovered (MX Valid): {stats['published_emails']}")
    print(f"Published Phones Verified (+92)      : {stats['published_phones']}")
    print(f"Main Excel Database Generated at     : {result['final_excel']}")
    print("=" * 75)


if __name__ == "__main__":
    main()
