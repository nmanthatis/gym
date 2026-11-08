"""Download the Log tab of the Workout Monitoring sheet as CSV into data/raw/log.csv."""
import sys
import urllib.request
from pathlib import Path

SHEET_ID = "1qX5deDZkB5k19U3lQRmMnEAOmzti3eAyl2iSCcC9BHM"
LOG_GID = "1872506981"

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "log.csv"


def main() -> int:
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={LOG_GID}"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = resp.read()
    if not data.startswith(b"Date,"):
        print("unexpected content (sheet not public?)", file=sys.stderr)
        return 1
    OUT.write_bytes(data)
    print(f"wrote {OUT} ({len(data):,} bytes, {data.count(b'\\n'):,} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
