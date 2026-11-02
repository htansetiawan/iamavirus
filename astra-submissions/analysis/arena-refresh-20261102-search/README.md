# Fresh arena data while conditional-value search is tested

2 November 2026. The bounded public refresh completed once, on original handle
80068, exit 0: 300 listed games, 282 new accepted replays, 18 cached, zero
errors or quarantines. It made 292 GET requests at 1.2-second pacing and took
360.51 seconds. This is a newest-300 refresh, not proof of archive completeness.
The external drive remains read-only; the data went to the existing local cache.

All 282 new games are annotated: 22,981 moves and 23,263 validated frames.
The original 19 tags are preserved. Separate supplements record 389 queen
captures with visibility before the victim's decision and immediately before
capture, plus 13 en passant captures that the legacy destination-occupied
capture tag omits. These supplements are visibility/event labels, not net
losses or proof of mistakes. There are 280 distinct complete move sequences;
two duplicate-sequence groups must stay together in any future train/test split.
There is no overlap with experiment 234's 25-game replay panel. These inspected
new labels are development data, not a newly declared test holdout.

`manifest.json` pins every new replay. `taxonomy-integrity.json` checks coverage,
hashes, denominators, all policy/version/colour/opponent panels, supplements,
and trajectory identities. Annotation handle 34463 exited 0; independent
verification also exited 0. The frozen experiment 234 dependencies were checked
before annotation. No model, history table, guard, candidate, or gate changed.

## Arena standing and opponent coverage

The public leaderboard snapshot at **05:28:31 UTC** has IAmAVirus v37 active,
**1874.30 Elo, rank 12** among all visible rated teams including staff and
external teams. The active record is **96W–8D–90L / 194 games**. Cached replay
metadata matches all four leaderboard counts, and all 194 replay hashes and
outcomes are verified. Only two of those games were newly downloaded here;
the rest were already cached. Do not equate the new-download subset with the
complete record for this version.

| Opponent / played version | v37 W–D–L | Score |
|---|---:|---:|
| Instructors v4 | 6–0–4 | 60.0% |
| HYPOTHERMIA v4 | 2–1–7 | 25.0% |
| duck v6 | 3–1–12 | 21.9% |
| Greek Gift v25 | 0–0–4 | 0.0% |
| Decent Chess Bot v7 | 4–1–9 | 32.1% |
| Knight Vision v36 | 0–0–4 | 0.0% |
| Crimson Fog v4 | 1–0–9 | 10.0% |
| Strongly Invisible v41 | 3–0–13 | 18.8% |

Against the six highest-rated teams in this snapshot, v37 has 11W–2D–51L:
12/64 points, **18.75%**. Each opponent cell is small; these are descriptive
records, not categorical capability or causal estimates.

We also compare against v35's cached historical outcomes in exactly matching
opponent-ID / played-opponent-version / our-colour strata. There are 190
covered v37 games: v37 scored 99 points (52.11%), versus 102.63 expected points
(54.02%) using historical v35 rates. Four v37 games have no matching old stratum
and are excluded from both sides of this comparison. All baseline support
counts are retained in `arena-panel.json`; 8,492 selected metadata rows are
frozen in `arena-selected.jsonl.gz`. An independent direct row-level calculation
agrees. Time, small strata and correlated games remain confounders: this does
not prove a regression, and it is not an Elo estimate.

The practical conclusion is narrower: refreshed data has not yet demonstrated
that v37 resolves our duck/HYPOTHERMIA/top-six weakness. The isolated search
experiment 234 should finish its existing frozen gate, rather than changing
its settings in response to this report.

## Execution and limits

`refresh.py`, `finish.py`, `annotate.py` and `arena_panel.py` retain the executable
collection and analysis steps. `completion.json` records the original terminal
handles. The first exploratory metadata query encountered a legacy null date
before filtering to our versions; it wrote no output. The saved script filters
by team/version, handles missing dates explicitly, and finds zero missing dates
in the selected v35/v37 data. No API refresh or match was repeated.

These data are from the public read-only API at
<https://6s890.lids.mit.edu/api/leaderboard> and completed replay endpoints.
The timestamp, raw snapshot path/hash and ranking definition are saved in
`standings.json`. Cores 0–1 are released after successful collection and
annotation; full-game lanes retain cores 2–5 until their own original handles
and owned bot processes finish.
