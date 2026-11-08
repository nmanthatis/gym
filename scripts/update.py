"""Fetch the sheet, clean it, rebuild the dashboard. Run: python scripts/update.py"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

for step in ("fetch.py", "clean.py", "build_dashboard.py"):
    print(f"== {step}")
    rc = subprocess.call([sys.executable, "-I", str(HERE / step)])
    if rc:
        sys.exit(rc)
print("done -> dashboard/index.html")
