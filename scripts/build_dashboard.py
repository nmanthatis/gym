"""Render dashboard/index.html from the cleaned tables (embeds the data as JSON)."""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLEAN = ROOT / "data" / "clean"
TEMPLATE = ROOT / "dashboard" / "template.html"
OUT = ROOT / "dashboard" / "index.html"


def read(name: str) -> list[dict]:
    p = CLEAN / name
    if not p.exists() or p.stat().st_size == 0:
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(s: str):
    return float(s) if s not in ("", None) else None


def main() -> int:
    exercises = read("exercises.csv")
    sets = read("sets.csv")
    cardio = read("cardio.csv")
    bodyweight = read("bodyweight.csv")
    anomalies = read("anomalies.csv")

    ex_rows = [{
        "d": e["date"], "ex": e["exercise"], "g": e["group"], "m": e["measure"],
        "n": int(e["sets"]), "vol": num(e["volume_lb"]), "bw": num(e["best_weight_lb"]),
        "br": num(e["best_reps"]), "e1": num(e["est_1rm_lb"]), "notes": e["notes"], "flags": e["flags"],
    } for e in exercises]
    set_rows = [{
        "d": s["date"], "ex": s["exercise"], "k": int(s["set_no"]), "w": num(s["weight_lb"]),
        "r": num(s["reps"]), "bwt": s["bodyweight"] == "1", "dflt": s["reps_defaulted"] == "1",
    } for s in sets]
    payload = {
        "generated": date.today().isoformat(),
        "exercises": ex_rows,
        "sets": set_rows,
        "cardio": [{"d": c["date"], "ex": c["exercise"], "raw": c["raw_values"], "notes": c["notes"]} for c in cardio],
        "bodyweight": [{"d": b["date"], "lb": num(b["bodyweight_lb"])} for b in bodyweight],
        "anomalies": len(anomalies),
    }
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", json.dumps(payload, separators=(",", ":")))
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
