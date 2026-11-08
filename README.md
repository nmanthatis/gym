# gym

Analysis pipeline for the "Workout Monitoring" Google Sheet. The sheet stays the place to log;
this folder turns its CSV export into tidy tables and a static dashboard.

## Run

```
python scripts/update.py
```

then open `dashboard/index.html` in a browser. Steps, individually:

| script | does |
|---|---|
| `scripts/fetch.py` | downloads the Log tab to `data/raw/log.csv` (sheet must stay link-viewable) |
| `scripts/clean.py` | normalizes it into `data/clean/*.csv` and writes `data/clean/anomalies.csv` |
| `scripts/build_dashboard.py` | embeds the clean data into `dashboard/template.html` -> `dashboard/index.html` |

Python 3.12, standard library only.

## Today section

The dashboard opens with a suggested session for today. The rules (rotation, overdue override,
weekly set targets, double progression) are written in `PHILOSOPHY.md`; the implementation is the
`todaySection` block in `dashboard/template.html`. Change the numbers in both places together.

## Hosted version

`.github/workflows/update.yml` runs the same three steps on GitHub Actions every day at 09:00 UTC
(and on demand from the Actions tab), then publishes the `dashboard/` folder to GitHub Pages.
The built `index.html` and the cleaned tables are not committed; the workflow regenerates them.
One-time setup in the repository: Settings -> Pages -> Source: **GitHub Actions**.

## Clean tabs in the workbook

The workbook has two extra tabs, **Clean sessions** and **Clean sets**, each a single `IMPORTDATA`
formula pointing at the published CSVs (`https://nmanthatis.github.io/gym/data/exercises.csv` and
`.../sets.csv`). They refresh on their own after each daily build, so they are a live view of the
cleaned log, not a copy to edit.

## Conventions the cleaner applies

- weight but no reps -> 10 reps (`reps_defaulted=1` in `sets.csv`, shown as `*` in the dashboard)
- reps but no weight -> bodyweight set (`bodyweight=1`)
- a negative weight is machine assistance; pull-ups at 40 lb or more before March 2024 and dips at
  20 lb or more before July 2024 are converted (`ASSIST_RULE` in `clean.py`); assisted sets count for nothing but reps
- on pull-ups, dips and muscle-ups a weight-only value under 15 is a rep count typed into the weight column
- weights are lb; exercise names are mapped through `config/exercise_map.csv`
  (raw spelling -> canonical name, muscle group, and how the columns are read:
  `weight`, `reps`, `seconds`, `mixed`, `cardio`, `other`)
- a mapped exercise name found in the Comments or BodyWeight column fills in a missing name,
  or overrides a wrong one (logged in `anomalies.csv`)
- an unnamed data row directly under a named empty row takes that name
- date typos that jump back by about a year are corrected to the neighbouring year
- `?`, `(`, `)` are stripped from numbers; a weight under 15 next to reps over 45 is swapped

Anything the script changed, guessed or dropped is listed in `data/clean/anomalies.csv` with the sheet row number.

## Adding a new exercise name

Run `clean.py`; it prints `UNMAPPED names`. Add a line to `config/exercise_map.csv` and re-run.
