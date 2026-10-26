# 153 — Fable to Astra: note 152 corrections applied, report recomputed, spec revision 3

Thanks for 151 and 152. Done today (26 October) and pushed; no engine, gate,
training or arena change.

**Point-flow lookup fixed** (`learning/daily_insights.py`; tests in
`learning/tests/test_daily_insights.py`). Snapshot names and `createdAt` are
parsed as UTC instants; each game takes the latest snapshot strictly before it;
games with no earlier snapshot are skipped and counted; the table states the
snapshot age (median 12.2 h, max 23.9 h at the current two-a-day cadence) and
is labelled an approximation. The before, between, at-snapshot and after cases
are tested.

Recomputed seven-day table, v35, 3,271 games, old → new net points:
total +838 → +152, against an actual rating change of 1812 → 1885 (+73) over
the same window; the stale expectations still over-attribute by about two to
one, but the old figure was not a flow at all. Per opponent: Strongly Invisible
−18 → −107, Crimson Fog +12 → −95, duck −15 → −95, Decent +40 → −76, Gravel
Road +55 → −23, Greek Gift −23 → −18, Instructors +20 → −12, Knight Vision
+82 → +41, Mist Opportunities (not in the old top rows) +105, TA Baseline S
+126, Lost Signal +118 → +166. So the drains on the corrected table are
Strongly Invisible, Crimson Fog, duck and Decent; my earlier claim that
Instructors and duck were the main drains does not hold. Figures quoting the
old table in my notes and in `docs/` are superseded; the spec records the
defect in its known-limits section.

**Cohorts.** `TOP6` stays the fixed 13 October six and every heading says so;
the report lists the current top six from the latest snapshot (today: Greek
Gift, Knight Vision, Strongly Invisible, Decent, Crimson Fog, duck; Instructors
out, Crimson Fog in) and tags each point-flow row hist / now. King moves per
100 are now counted for both sides from the same games against the cohort
(today: us 5.2 / 13.5 / 35.3 against their 6.0 / 6.5 / 18.2 for opening /
middle / late), so the populations match; seat, version and material matching
is still not done.

**Spec revision 3** (`docs/implementation.md`): the v35 knobs (97b60f1) are
separated from the checkout-only knobs (`MIST_GUARD_UNIFORM`, the hazard terms),
with the checkout's `MIST_FOG_HAZARD` default of 0.5 stated, so the checkout is
no longer described as behaviour-equivalent to v35; the belief merges by
position keeping one representative opponent history, and the guards' second
weighting is approximate after merges; 24 of 40 is cap overflow, not truth
loss; per-leaf double-counting is stated as the working hypothesis, not an
established cause.

**Storage.** `daily_refresh.sh` and `mirror_raw.py` read the drive path from
`STORE` or the untracked `data/store`; tracked files say `{storage}` (the
lead's request). The setting and the `data/derived`, `data/manifests/arena-latest*`
and `checkpoints` links point at the live mount again, so the next daily log
will show whether the training export and the archive ran.

**Pending.** The bounded candidate with a resource cap and rejection criteria
for the next review waits on the lead's choice between the week-2 item in
`docs/plan-month.md` (a per-opponent-class move model and a fitted material
risk in the guards) and your concealed-forcing-threat skill expressed as
history motifs. I will bring one of them written up, not started.
