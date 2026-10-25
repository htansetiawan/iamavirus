# v36 guard: stratified random-replay safety controls

**Result:** No immediate king-fatal action in either version across 138 tested
positions. The v36 guard changed 26/138 choices. This is a non-regression
signal for immediate king safety in the sampled positions, not a playing
strength result.

## Sample and method

`select_random_v35_guard_controls.py` sampled one eligible, historically
nonfatal IAmAVirus v35 decision from each distinct completed game. Sampling
was seeded and random within opponent × recorded game result × our color cells,
with up to five games per cell. Opponents were Greek Gift, Knight Vision,
Strongly Invisible, Decent Chess Bot, Crimson Fog, Instructors, and duck,
matching the Oct. 25 top six plus duck. The selection excluded all games in the
91 hidden-arrival target set, the prior 12 curated controls, and the prior 23
broad controls. The resulting sample has 138 games; Crimson Fog has only three
eligible Black wins, so that cell is short by two.

At each saved pre-action observation, both immutable archives replayed the
same actor-visible history and selected a move with a 0.5-second search cap.
The baseline used v35's default guard `0.02`; the candidate was built from the
v36 archive and used its default `0.0001`. Full true-board state was used only
after selection to score whether each chosen action immediately exposed the
king to capture. The bot did not receive it. The compared executable hashes
are v35 `f8ef3027756da506d7b367e22ff93ec4cb17bd912eca68c4bfaa8fda5bc028ff` and
v36 `eed0257297be608d093ae328d81cc3a2108b8e720d72d2b9f52dd61311a8dc17`.

## Results

| Opponent | Cases | Choices changed | v35 fatal | v36 fatal |
|---|---:|---:|---:|---:|
| Crimson Fog | 18 | 4 | 0 | 0 |
| Decent Chess Bot | 20 | 5 | 0 | 0 |
| Greek Gift | 20 | 4 | 0 | 0 |
| Instructors | 20 | 5 | 0 | 0 |
| Knight Vision | 20 | 2 | 0 | 0 |
| Strongly Invisible | 20 | 5 | 0 | 0 |
| duck | 20 | 1 | 0 | 0 |
| **Total** | **138** | **26** | **0** | **0** |

The candidate chose one of the enumerated true-board-safe alternatives in
65/138 cases. This is only a mechanical property of the selected action; it
does not imply strategic improvement.

## Limits and decision

The games were deliberately stratified by past outcome and color; the total
is not a deployment-weighted sample. One decision per game avoids repeated
positions from a single game, but all decisions are still from this arena
population. Only immediate king fatality was measured. We did not play
counterfactual continuations, measure material loss, or estimate Elo. The
sample complements the 91 selected hidden-arrival losses (83→61 fatal choices,
26 saved and 4 introduced), but cannot resolve those strategic tradeoffs.

An initial sample selection was discarded after an audit found that it was
not reproducible across filesystem traversal order and could leave cells short
after filtering fatal recorded decisions. The selector now sorts source paths,
uses the recorded seed, and fills cells only with nonfatal recorded decisions;
the comparison was rerun on the regenerated manifest. The report above gives
only the reproducible run.

Keep v36 marked **exploratory**. The evidence supports that it reduces fatal
choices on the selected hidden-arrival set without an observed immediate-fatal
choice in 138 stratified ordinary controls; its 16-game full-clock self-play
screen was even (8/16). An arena trial can measure it prospectively, but do
not claim strength gain or promote it based on these offline gates.

## Artifacts and reproduction

- Sample: `random-v35-guard-controls-20261025.json`
  (SHA-256 `9a86e667eb180dd19f0ab0812b71ced4f12f8cb7e2ba11378a172b315d1db28b`)
- Comparison: `random-v35-guard-controls-compare-20261025.json`
  (SHA-256 `112f42ddd5ed4e97a146fd69de0d4017889168ce12d75a76189f837fc14d68e0`)
- Selector: `astra-submissions/tools/select_random_v35_guard_controls.py`
  (SHA-256 `d40345a44a54a568b08cec0337a6e15d433298c51c051be8a9f18cc83fac0f79`)

The sample can be regenerated from the repository root with:

```sh
python3 astra-submissions/tools/select_random_v35_guard_controls.py \
  --exclude astra-submissions/analysis/standing-trend-20261024/hidden-arrival-cases-ply70.json \
  --exclude astra-submissions/analysis/hidden-slider-zone-20261025/hidden-slider-zone-safe-controls.json \
  --exclude astra-submissions/analysis/hidden-slider-zone-20261025/v35-guard0001-broad-controls-5s.json \
  --per-color-outcome 5 --max-ply 80 --seed 20261025 \
  --output astra-submissions/analysis/hidden-slider-zone-20261025/random-v35-guard-controls-20261025.json
```

Replay comparison used `astra-submissions/tools/compare_hidden_slider_zone_prefixes.py`
with the archived v35 and v36 extraction directories.
