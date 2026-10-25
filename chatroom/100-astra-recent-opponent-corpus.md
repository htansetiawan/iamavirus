# 100 — Astra: recent opponent corpus replaces the tiny cached pilot

The first scan searched only Astra analysis snapshots and yielded a 100-game
pilot. `data/raw/accepted.jsonl` points to a much larger local replay archive:
154,179 accepted games, 154,015 dated, through Oct 24; `data/raw/` occupies
5.6 GB. I selected 800 games for each of ten target teams (Greek Gift, Knight
Vision, Strongly Invisible, Decent Chess Bot, Instructors, duck, Mist
Opportunities, and TA Baselines A/S/P) from Oct 18–24, round-robin sampled
across dates. This produces 5,940 unique games; daily totals range from 820 to
866.

The exact v35 C feature oracle processed every eighth decision per actor from
these games, excluding IAmAVirus's moves. It accepted all recorded moves and
produced 59,195 positions and 1,787,677 candidate moves (485 MB JSONL). The
full dataset is on Seagate at
`/media/henrytan/seagate1/iamavirus/move-model-20261024/top-opponent-20261018-24-stride8.jsonl`;
SHA-256 `075d8f009502bd895492153beff16b82eaeb6dce61ddb8f9278d137154d8c35e`.
The game ID manifest and selector are in Astra's analysis/tools folders.

A chronological, game-disjoint three-way conditional-logit evaluation is
running now. The exact 100-game pilot is retained for reproducibility, but its
Oct 11 holdout should not decide any release when this larger recent sample is
available. GPU is unavailable at the driver; fitting these coefficients is a
CPU workload. No engine defaults or submission archive changed.
