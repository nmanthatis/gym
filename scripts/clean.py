"""Normalize data/raw/log.csv into tidy tables under data/clean/.

Conventions (confirmed by the user):
  * a set with a weight but no reps  -> 10 reps
  * a set with reps but no weight    -> bodyweight set
  * weights are lbs; exercise names carry a muscle-group prefix

Outputs:
  data/clean/sets.csv        one row per set
  data/clean/exercises.csv   one row per exercise per day, with volume / best set / est. 1RM
  data/clean/cardio.csv      cardio rows with their raw columns kept as logged
  data/clean/bodyweight.csv  weigh-ins
  data/clean/anomalies.csv   everything the script changed, guessed or could not use
"""
from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "log.csv"
MAP = ROOT / "config" / "exercise_map.csv"
OUT = ROOT / "data" / "clean"

DEFAULT_REPS = 10
# bodyweight exercises: a logged weight at or above the threshold, before the date, is machine
# assistance (stored as a negative weight); a weight-only value under REPS_IN_WEIGHT_MAX is a rep count
ASSIST_RULE = {"B: Pullups": (40, date(2024, 3, 1)), "Ch: Dips": (20, date(2024, 7, 1))}
BODYWEIGHT_EXERCISES = {"B: Pullups", "Ch: Dips", "B: Muscle Ups"}
REPS_IN_WEIGHT_MAX = 15
GROUP_PREFIX = {"B": "Back", "Bi": "Biceps", "Ch": "Chest", "Sh": "Shoulders",
                "Tr": "Triceps", "L": "Legs", "Co": "Core", "Ca": "Cardio"}


# ----------------------------------------------------------------------------- helpers
def load_map() -> dict[str, dict]:
    with MAP.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {norm_key(r["raw"]): r for r in rows}


def norm_key(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def parse_date(s: str) -> date | None:
    s = s.strip()
    if not s:
        return None
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if not m:
        return None
    mo, d, y = map(int, m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def parse_num(s: str) -> tuple[float | None, str | None, str | None]:
    """Return (value, flag, leftover_text). Tolerates '26?', '240(', '60)'."""
    s = s.strip()
    if not s:
        return None, None, None
    try:
        return float(s), None, None
    except ValueError:
        pass
    cleaned = re.sub(r"[?()]", "", s)
    try:
        v = float(cleaned)
        return v, "uncertain" if "?" in s else "stray_char", None
    except ValueError:
        return None, "text", s


def fmt(v: float | None) -> str:
    if v is None:
        return ""
    return f"{v:g}"


def epley(weight: float, reps: float) -> float:
    return weight * (1 + reps / 30) if reps > 1 else weight


# ----------------------------------------------------------------------------- main
def main() -> int:
    emap = load_map()
    anomalies: list[dict] = []

    def note(row_no, issue, action, raw=""):
        anomalies.append({"sheet_row": row_no, "issue": issue, "action": action, "raw": raw})

    with RAW.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        raw_rows = list(reader)

    # ---- pass 1: dates (fix obvious year typos using the previous row's date)
    rows = []
    prev: date | None = None
    for i, r in enumerate(raw_rows, start=2):  # sheet row numbers (header is row 1)
        r = (r + [""] * 16)[:16]
        date_s, _, ex, _, w1, r1, w2, r2, w3, r3, w4, r4, w5, r5, comments, bw = r
        if not any(x.strip() for x in r):
            continue
        d = parse_date(date_s)
        if d is None and date_s.strip():
            note(i, "unparseable date", "row dropped", date_s)
            continue
        if d is None:
            if prev is None:
                note(i, "empty date", "row dropped", " | ".join(r))
                continue
            d = prev
            note(i, "empty date", f"assumed previous row's date {prev}", " | ".join(r))
        elif prev is not None and (prev - d).days > 180:
            # year typo: pick the year that lands closest to the previous row
            best = min((date(y, d.month, d.day) for y in (prev.year, prev.year + 1)
                        if _valid(y, d.month, d.day)), key=lambda c: abs((c - prev).days))
            if abs((best - prev).days) <= 21:
                note(i, f"date {d} jumps back {(prev - d).days} days", f"year corrected to {best}", date_s)
                d = best
            else:
                note(i, f"date {d} jumps back {(prev - d).days} days", "left as is", date_s)
        prev = d
        rows.append((i, d, ex, [(w1, r1), (w2, r2), (w3, r3), (w4, r4), (w5, r5)], comments, bw))

    # ---- pass 2: exercise name resolution + set parsing
    sets_out, ex_out, cardio_out, bw_out = [], [], [], []
    unmapped = defaultdict(int)
    prev_row = None  # (row_no, date, raw exercise name, had set data)
    for row_no, d, ex_raw, raw_sets, comments, bw_col in rows:
        ex_raw = ex_raw.strip()
        comments = comments.strip()
        bw_col = bw_col.strip()
        notes: list[str] = []
        flags: set[str] = set()
        has_set_data = any(w.strip() or r.strip() for w, r in raw_sets)

        # layout slip: a named row with no sets directly above an unnamed row with sets
        own_name = (comments and norm_key(comments) in emap) or (bw_col and norm_key(bw_col) in emap)
        if (not ex_raw and has_set_data and not own_name and prev_row and prev_row[2] and not prev_row[3]
                and prev_row[1] == d):
            ex_raw = prev_row[2]
            note(row_no, "sets on the line below the exercise name", f"merged into '{ex_raw}' from row {prev_row[0]}", ex_raw)
            flags.add("merged_from_row_above")
            # drop the empty placeholder emitted for the row above
            ex_out[:] = [e for e in ex_out if e["sheet_row"] != prev_row[0]]
        prev_row = (row_no, d, ex_raw, has_set_data)

        # body weight column: a number is a weigh-in, text is a note (or a misplaced name)
        bw_val, bw_flag, bw_text = parse_num(bw_col)
        if bw_val is not None:
            bw_out.append({"date": d.isoformat(), "bodyweight_lb": fmt(bw_val), "sheet_row": row_no})
            if bw_flag:
                note(row_no, f"bodyweight value '{bw_col}'", "kept after stripping characters", bw_col)

        # resolve the exercise name
        name_src = ex_raw
        if not name_src:
            for cand in (comments, bw_text or ""):
                if cand and norm_key(cand) in emap:
                    name_src = cand
                    flags.add("name_from_comment")
                    break
        m = emap.get(norm_key(name_src)) if name_src else None

        # a mapped exercise name sitting in the notes column overrides a wrong label,
        # unless the note is itself an ambiguous word (e.g. 'Inclined') from another muscle group
        for cand in (comments, bw_text or ""):
            if not cand or cand == name_src:
                continue
            alt = emap.get(norm_key(cand))
            if alt is None:
                notes.append(cand)
                continue
            if m is not None and alt["canonical"] == m["canonical"]:
                continue
            if alt.get("ambiguous") and m is not None and alt["group"] != m["group"]:
                notes.append(cand)
                continue
            if m is not None and ex_raw:
                note(row_no, f"row labelled '{ex_raw}' but note says '{cand}'",
                     f"exercise set to {alt['canonical']}", cand)
                flags.add("relabelled")
            m = alt
            name_src = cand

        if m is None:
            has_data = has_set_data
            if name_src:
                unmapped[name_src] += 1
                note(row_no, f"unmapped exercise '{name_src}'", "row kept with group Unknown" if has_data else "row dropped", name_src)
                if not has_data:
                    continue
                m = {"canonical": name_src, "group": "Unknown", "measure": "weight", "ambiguous": "yes"}
            else:
                if has_data:
                    note(row_no, "sets logged with no exercise name", "row dropped",
                         " | ".join(f"{w}/{r}" for w, r in raw_sets))
                elif comments or bw_text:
                    note(row_no, "note-only row", "kept as note", comments or bw_text)
                continue

        canonical, group, measure = m["canonical"], m["group"], m["measure"]
        if m.get("ambiguous"):
            flags.add("name_guessed")

        if measure == "cardio" or measure == "other":
            vals = [v for w, r in raw_sets for v in (w.strip(), r.strip())]
            cardio_out.append({"date": d.isoformat(), "exercise": canonical, "sheet_row": row_no,
                               "raw_values": " | ".join(v for v in vals if v),
                               "notes": "; ".join(n for n in [comments] + notes if n)})
            continue

        # ---- sets
        parsed = []
        for k, (w_s, r_s) in enumerate(raw_sets, start=1):
            w, wflag, wtext = parse_num(w_s)
            r, rflag, rtext = parse_num(r_s)
            if wtext:
                note(row_no, f"set {k} weight is text '{wtext}'", "weight ignored", wtext)
                notes.append(wtext)
                flags.add("text_in_number")
            if rtext:
                notes.append(rtext)          # e.g. 'Diamonds' pushup variant
                flags.add("text_in_number")
            if wflag in ("uncertain", "stray_char"):
                note(row_no, f"set {k} weight '{w_s.strip()}'", f"read as {fmt(w)}", w_s)
                flags.add(wflag)
            if w is None and r is None:
                continue
            if measure == "weight" and w is not None and r is not None and w < 15 and r >= 45:
                note(row_no, f"set {k} looks swapped ({fmt(w)} lb x {fmt(r)})", f"read as {fmt(r)} lb x {fmt(w)}", f"{w_s}/{r_s}")
                w, r = r, w
                flags.add("swapped")
            bodyweight = False
            reps_defaulted = False
            if canonical in ASSIST_RULE and w is not None and w > 0:
                thr, until = ASSIST_RULE[canonical]
                if w >= thr and d < until:
                    w = -w
                    flags.add("assisted")
            if canonical in BODYWEIGHT_EXERCISES and w is not None and r is None and 0 < w < REPS_IN_WEIGHT_MAX:
                r, w = w, None
                flags.add("reps_in_weight_column")
            if measure in ("reps", "seconds"):
                # the weight column holds reps (or seconds); a reps column, if any, also means reps
                val = w if w is not None else r
                if w is not None and r is not None and measure == "reps":
                    # both filled: treat W as added weight, R as reps (e.g. weighted pull-up style)
                    parsed.append((k, w, r, False, False)); continue
                parsed.append((k, None, val, True, False)); continue
            if measure == "mixed":
                if w is not None and r is None and w <= 30:
                    parsed.append((k, None, w, True, False)); continue
            if w is None:
                bodyweight = True
            elif r is None:
                r = DEFAULT_REPS
                reps_defaulted = True
            parsed.append((k, w, r, bodyweight, reps_defaulted))

        if not parsed:
            ex_out.append({"date": d.isoformat(), "exercise": canonical, "group": group, "measure": measure,
                           "sets": 0, "volume_lb": "", "best_weight_lb": "", "best_reps": "", "est_1rm_lb": "",
                           "notes": "; ".join(n for n in [comments] + notes if n),
                           "flags": " ".join(sorted(flags | {"no_sets"})), "sheet_row": row_no})
            continue

        vol = 0.0
        best_w, best_r, best_e1rm, best_reps_any = None, None, None, None
        for k, w, r, bodyw, defaulted in parsed:
            sets_out.append({"date": d.isoformat(), "exercise": canonical, "group": group, "measure": measure,
                             "set_no": k, "weight_lb": fmt(w), "reps": fmt(r),
                             "bodyweight": int(bodyw), "reps_defaulted": int(defaulted),
                             "flags": " ".join(sorted(flags)), "sheet_row": row_no})
            if r is not None:
                best_reps_any = r if best_reps_any is None else max(best_reps_any, r)
            if w is not None and w > 0 and r is not None and not bodyw:
                vol += w * r
                e = epley(w, r)
                if best_e1rm is None or e > best_e1rm:
                    best_e1rm = e
                if best_w is None or w > best_w or (w == best_w and r > best_r):
                    best_w, best_r = w, r
        ex_out.append({"date": d.isoformat(), "exercise": canonical, "group": group, "measure": measure,
                       "sets": len(parsed), "volume_lb": fmt(round(vol, 1)) if vol else "",
                       "best_weight_lb": fmt(best_w), "best_reps": fmt(best_r if best_w is not None else best_reps_any),
                       "est_1rm_lb": fmt(round(best_e1rm, 1)) if best_e1rm else "",
                       "notes": "; ".join(n for n in [comments] + notes if n),
                       "flags": " ".join(sorted(flags)), "sheet_row": row_no})

    # ---- write
    OUT.mkdir(parents=True, exist_ok=True)
    _write(OUT / "sets.csv", sets_out)
    _write(OUT / "exercises.csv", ex_out)
    _write(OUT / "cardio.csv", cardio_out)
    _write(OUT / "bodyweight.csv", bw_out)
    _write(OUT / "anomalies.csv", anomalies)

    days = {e["date"] for e in ex_out} | {c["date"] for c in cardio_out}
    print(f"sets: {len(sets_out):,}  exercise-days: {len(ex_out):,}  cardio rows: {len(cardio_out)}  "
          f"weigh-ins: {len(bw_out)}  training days: {len(days)}  anomalies: {len(anomalies)}")
    defaulted = sum(s["reps_defaulted"] for s in sets_out)
    bw = sum(s["bodyweight"] for s in sets_out)
    print(f"reps defaulted to {DEFAULT_REPS}: {defaulted:,}   bodyweight sets: {bw:,}")
    if unmapped:
        print("UNMAPPED names (add to config/exercise_map.csv):")
        for k, v in sorted(unmapped.items(), key=lambda kv: -kv[1]):
            print(f"  {v:3d}  {k}")
    return 0


def _valid(y, m, d) -> bool:
    try:
        date(y, m, d)
        return True
    except ValueError:
        return False


def _write(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    sys.exit(main())
