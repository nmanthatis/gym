# Training philosophy

The rules the dashboard's "Today" section follows. Change the numbers here, then the page.
Status: **confirmed 2026-11-08**, revised 2026-11-13 (rotation first, one meaning of overdue, warm-ups not counted).

## 1. Session menu

Five session types, in the order you rotate through them:

| # | Session | Main groups | Usual staples (from the log) |
|---|---|---|---|
| 1 | Chest | Chest | dumbbell press, incline press (dumbbell or machine), pec fly, low cable fly, dips |
| 2 | Shoulders | Shoulders | dumbbell press, lateral raises, rear delt cable, shrugs, face pulls |
| 3 | Back | Back | pull-ups, machine row, front pulldown, straight-arm pulldown, bar rows |
| 4 | Legs | Legs | squat, deadlift, leg extension, leg curl, calf extension, hip thrust, Bulgarian split squat, abductor/adductor |
| 5 | Legs + accessories | Legs, plus accessories | a leg session from the same pool, shorter (3 leg exercises), followed by 2 accessory exercises |

Both leg days draw from the full leg pool; the page prefers the leg exercises not done on the previous leg day.

**Accessories** are core, biceps, triceps, or a physical-therapy exercise. On day 5 the page proposes
two of them, picking the two of biceps, triceps and core that have gone longest without direct work. A PT exercise is a free slot the
page cannot plan, so it shows a reminder, not a prescription. Core can also be added to any other
session when there is time (2-3 exercises, 2-3 sets each).

## 2. Which session today

Pick the **next session in the rotation after the last session you logged**, then apply two checks:

- **48-hour rule.** If a main group of that session was trained in the last 2 days, skip to the next session in the rotation.
- **Overdue.** A group is *overdue* when it has not been trained directly for 9 or more days. Nothing else makes a group overdue. An overdue main group (chest, shoulders, back, legs) that today's session does not cover goes ahead of the rotation, longest wait first. Any other overdue group becomes an add-on: 2 sets of the exercise you did most recently for it, two add-ons at most.

A session counts even when it was logged without numbers: an exercise name with no sets means the
exercise was done, and it counts as 3 sets for the rotation, the days-since count and the weekly bars.

The first version let a group under its weekly set minimum count as overdue. At 3 to 4 sessions a
week almost every group is under that minimum most days, so the override fired daily and the
rotation was ignored. The weekly minimum now only colours the bar.

## 3. Weekly volume targets

Working sets per muscle group per rolling 7 days. Sets that hit a group indirectly count half
(pressing counts 0.5 for shoulders and triceps, pulling counts 0.5 for biceps).

**Warm-up sets are not working sets.** The first set of an exercise is a warm-up when it is under
80% of the lightest set that follows and the following sets (at least two) are within 30% of each
other, for example 40, 80, 80, 80. It stays in the log, shown as "warm-up", but is left out of every
set count and of the progression rule.

| Group | Target | Minimum |
|---|---|---|
| Chest, Back, Shoulders, Legs | 10 | 6 |
| Biceps, Triceps, Core | 6 | 4 |

Why these numbers: meta-analyses put the hypertrophy dose-response at roughly 10+ weekly sets per
muscle with diminishing returns above that, a minimum effective dose around 4 fractional sets, and
the largest return per set between about 5 and 12 sets. Twice-weekly exposure per muscle beat
once-weekly when volume was equal. At your current 2.5 sessions a week a strict 5-day rotation
reaches each group only every two weeks, so the overdue override and the half-credit for indirect
work are what keep groups above the minimum.

## 4. Progression (double progression)

Rep range 8-12 on every working set.

- All sets reached 12 last time: add weight. Dumbbells +5 lb (the next dumbbell), everything else +5 lb.
- Any set fell under 8: drop 5 lb, or repeat the weight and aim for 8s.
- Otherwise: same weight, add a rep somewhere.

Bodyweight exercises (pull-ups, dips): when all sets reach 12, add 5 lb; when under 8 with added
weight, remove it.

## 5. Session size

4-5 exercises, 3 working sets each, 12-15 sets, 45-60 minutes. This matches the median of the last
six months (4 exercises, 12 sets). Exercises come from your last six sessions of that group, most
frequent first; the ones done in the very last session go after the others, so variants rotate
without bringing back exercises you dropped months ago.

## 6. What the page shows

For today: the session name and why (next in rotation, or which group is overdue), your last four
sessions, 4-5 exercises with last performance (sets × reps @ weight), the suggested weight and rep
target, and any overdue add-on with the days since it was trained. Plus a 7-day bar per group
against target and minimum, labelled with the days since the last direct training. The number is direct
sets only; the bar shows direct sets in blue and the half credit from indirect work in orange.
