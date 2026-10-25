# v35 hidden-threat move-prior refit pilot

> **Methodology correction (2026-10-25):** The earlier `hidden_two_only`
> coefficients and held-out metrics in this document were produced by a fitting
> bug. The fitter optimized only features 26–27, then the builder inserted those
> coefficients into the full v35 prior. Training and validation therefore did
> not match runtime. Do not use the earlier hidden-only NLL, coefficients, or
> 83→47/91 comparison as predictive evidence for a correctly fitted specialist.
> Replay results remain observations about those exact binaries, but do not
> validate that fitting procedure. The `full_refit` path fitted the full feature
> vector and remains valid. Corrected fit and replay results are recorded below.

## Data and split

Candidate features came from exact v35 `move_features()` in the archived C
source. A C replay probe enumerated true legal candidates and verified the
recorded move is among them. The cache contains only 100 usable filtered games
and ends on 2026-10-11; the split is by whole game, ordered by replay date and
ID: 60 train / 20 validation / 20 test games (2,173 / 759 / 814 positions).
The test positions are the most recent 20 games and include 62 cases where
the observed move activated one of the two hidden-threat features. This is a
small historical pilot, not a current-field sample.

The original v35 prior's fit window ended on Oct 10, so the Oct 11 test games
are later than that published fitting window. The new training games overlap
the old model's training period; they do not leak into the held-out test.
The filtered archive has poor coverage of some opponents (only one cached
Strongly Invisible game, with no retained opponent decision), so this cannot
be used to claim opponent-specific generalization.
The source archive was `fable-submissions/iamavirus-v35-mist-c-v14.zip`
(SHA-256 `24791ca64a429f5ae931466ce3c1af36c6974e1295203e99a00a991976955b4c`);
the extracted baseline binary SHA-256 was
`f8ef3027756da506d7b367e22ff93ec4cb17bd912eca68c4bfaa8fda5bc028ff`.

## Held-out results

The first table is retained as an historical record. Its `hidden_two_only`
row is invalid as a fitted-model result; only the frozen v35 and full-refit rows
remain usable.

| Model | Overall NLL ↓ | Top-1 | Brier ↓ | Candidate ECE ↓ | Hidden-threat NLL ↓ | Hidden-threat top-1 |
|---|---:|---:|---:|---:|---:|---:|
| Frozen v35 | 2.6629 | 26.90% | 0.8462 | 0.00184 | 2.8726 | 22.58% |
| Frozen v35 + two fitted hidden-threat weights | 2.6766 | 26.54% | 0.8523 | 0.00094 | **2.4271** | **30.65%** |
| Regularized full refit | **2.6592** | **27.27%** | 0.8478 | 0.00173 | 2.7073 | 27.42% |

Validation selected L2 strength 1.0 for both refits. The earlier two-feature
held-out metrics are invalidated by the methodology correction above. The full
refit is essentially tied overall and improves hidden-threat
top-1 modestly while worsening hidden-threat NLL. No model dominates. These
differences are not strength evidence, and 62 hidden-threat examples are too
few for a release decision.

## Exact sequential-belief and one-reply referee gate

The historical two-feature binary was built from the exact v35 archive, changing only
the two `theta_full` coefficients. On the same 16 targeted unseen-arrival
prefixes and identical search parameters, baseline v35 selected a referee
fatal move in 16/16. The candidate selected 7/16 recorded nonfatal legal
alternatives; 9/16 remained immediately fatal. Exact sequential belief traces
showed median true-board posterior share rising from 0.0675% to 0.478% and
median truth rank improving from 273.5 to 33 for that binary. This is a
binary-specific observation on selected loss data, not evidence that the fit
method generalizes. Exact enumeration found no immediate king-capture reply to
any of the moves it changed to a nonfatal alternative. Opponent replies are enumerated on the true board
only for that terminal check; no reply policy, material value, or deeper
continuation is modeled, so this is not a playing-strength estimate.

On 12 previously selected nonfatal king-move controls, frozen v35 and the
two-feature candidate both chose 0/12 immediately fatal moves. Neither
selection allowed an immediate opponent king-capture reply. The candidate
changed its move relative to baseline in 6/12 controls; all six were still
immediately safe. This is encouraging but a tiny, selected control set, not a
strategic safety result.
The candidate builder reproduces the tested binary hash
`4793cd6d9b5c7beb6962423c13f154024a72b2830b804fe7ac9bdc1e9d8715f4` from the
two coefficients above.

## Decision

Do not change the submitted v35 coefficients or ZIP based on this pilot. These
fixed-binary controls do not validate the flawed fit objective. Require
corrected-fit, broader controls, and continuation evidence before promotion.

## Recent hidden-only fit: sequential safety evidence, with overlap caveat

The historical Oct 18–24 fit's two hidden-threat coefficients were rebuilt in isolation
from the exact v35 archive (full coefficients only; cheap prior unchanged):
`MM_CHECK_UNSEEN=1.3592952`, `MM_THREAT_UNSEEN=0.5914142`, binary SHA-256
`adbbb2a4dc998d2485844ccaf8ad3a4783e9f5f6b5efbb14b4cc3df8ee298ff9`.

On the 16-case hidden-arrival slice, baseline v35 selected 16 referee-fatal
moves; the recent hidden-only candidate selected 9 fatal moves and 7 known-safe
alternatives. On the same 12 selected nonfatal controls, both baseline and
candidate selected zero fatal moves and two known-safe alternatives. No chosen
candidate move on either slice allowed an immediate king-capture reply. These
are fixed-prefix, one-ply diagnostics; no changed move was branched into an
opponent policy or longer continuation.

The wider 91-case hidden-arrival diagnostic at a five-second search cap found
baseline 83/91 fatal choices and 7/91 known-safe alternatives, versus candidate
43/91 and 48/91. By opponent, fatal choices were Duck 25→18 (n=27), Strongly
Invisible 22→7 (n=22), Decent Chess Bot 20→10 (n=24), and Instructors 16→8
(n=18). The candidate had no immediate king-capture replies after any of its
chosen moves. This is a large selected-loss safety signal, not a strength
estimate.

**Data overlap was detected.** Twenty-six of the 91 target games were in the
5,940-game fit sample, and in four target cases the immediately preceding
opponent decision was among the stride-8 training rows. The 91-case result is
therefore provisional. Before treating it as held-out evidence, refit after
excluding all 91 target games, then repeat the 91-case candidate and baseline
traces with the same search budget. Even a clean repeat still needs broader
nonfatal controls and branched/self-play strength validation. No ZIP or arena
version is cleared.

To remove this overlap, I created a second Seagate dataset excluding all 91
target game IDs (3,523 candidate rows removed; 5,889 games and 59,100 positions
remain). The original hidden-only fit on this set is invalidated by the
training/runtime mismatch; its reported 1.3541/0.5908 weights and test metrics
must not be used as evidence of predictive gain.

The earlier 91-position comparison reported baseline fatal choices 83/91 vs candidate
47/91; that candidate came from the invalid hidden-only fit and is retained only
as a binary-specific historical observation. Its metrics, truth-mass change,
and per-opponent deltas are not evidence for a correctly fitted specialist.

The candidate and baseline were also replayed on 25 nonfatal king-move controls
from 25 distinct games, all disjoint from the fit corpus. At five seconds per
decision, both selected 0/25 referee-fatal moves; neither selection permitted
an immediate king-capture reply. The hidden-only candidate chose one of the
listed safe non-king alternatives in 1/25 versus baseline 4/25 (the list holds
at most five examples, so this is not a full strategic-choice score). It
changed 6/25 moves versus baseline's 9/25 changes from the recorded safe king
move. These controls show no immediate king-safety regression in this sample,
but they do not bound material loss, long-term position quality, or policy
strength. The next gate is paired full-game self-play against the frozen v35
binary, followed by opponent-reply continuations for rescued tactical moves.

Artifacts: `recent-hidden-only-hidden-arrival-compare.json`,
`recent-hidden-only-controls-12-referee.json`,
`recent-hidden-only-wide-compare-91-5s.json`, and the individual traces in
this directory. The correction superseding the older hidden-only claims is in
[`chatroom/109-astra-hidden-prior-fit-methodology-correction.md`](../../../chatroom/109-astra-hidden-prior-fit-methodology-correction.md); the earlier Fable handoff is in
[`chatroom/104-astra-hidden-prior-wide-replay-provisional.md`](../../../chatroom/104-astra-hidden-prior-wide-replay-provisional.md).

## Expanded recent data in progress

The repository contains 154,179 accepted game records through Oct 24. A
stratified manifest selects up to 800 games for each of ten strong teams and
TA baselines over Oct 18–24, yielding 5,940 unique games with 820–866 per day.
The exact feature oracle sampled every eighth decision per actor, excluded
IAmAVirus decisions, and verified all recorded moves: 59,195 positions and
1,787,677 legal candidates. The 485 MB JSONL is on Seagate at
`/media/henrytan/seagate1/iamavirus/move-model-20261024/top-opponent-20261018-24-stride8.jsonl`;
SHA-256 `075d8f009502bd895492153beff16b82eaeb6dce61ddb8f9278d137154d8c35e`.
The game manifest is `recent-game-sample.jsonl`; selection is reproducible
with `tools/select_recent_opponent_games.py`. The recent chronological fit is
complete and is the main predictive result below.

### Recent held-out fit

The game-disjoint split has 3,549 train / 1,183 validation / 1,183 test games,
with 35,481 / 11,783 / 11,931 sampled decisions. The held-out games fall on
Oct 23–24. There are 1,042 held-out decisions whose actual move activates at
least one hidden-threat feature. Validation selected L2 strength 1.0.

| Full prior | Overall NLL ↓ | Top-1 | Brier ↓ | Hidden NLL ↓ | Hidden top-1 |
|---|---:|---:|---:|---:|---:|
| Frozen v35 | 2.6423 | 26.31% | 0.8471 | 2.7186 | 24.66% |
| v35 plus only the two omitted weights | 2.6477 | 25.72% | 0.8517 | **2.2223** | **37.72%** |
| Regularized full refit | **2.6254** | **26.97%** | **0.8436** | 2.4583 | 32.73% |

The full refit improves overall NLL, top-1 and Brier, and improves overall NLL
for each of Duck (891 test decisions), Instructors (894), Greek Gift (939),
Knight Vision (879), Strongly Invisible (1,075), Decent Chess Bot (991), Mist
Opportunities (1,140), and all three TA baselines. It also improves hidden
move NLL for every one of those teams. The two-weight update has the best
aggregate hidden-threat slice, but loses slightly on overall metrics. These
are predictive held-out gains from a replay sample, not Elo estimates.

The separately refitted cheap prior slightly improves its own held-out NLL
(2.8149→2.8098) and top-1 (23.46%→24.13%), while its hidden-threat NLL is
slightly worse (3.3299→3.3466). Full and cheap arrays are now combined in a
research binary for exact sequential-belief checks; nothing is submitted.

### Excluded-game full-prior candidate and full-clock gate

To compare the broad predictive fit with the hidden-only intervention, I built
a second candidate with all 28 full-prior weights refit on the dataset that
excludes all 91 selected hidden-arrival target games; the cheap prior remained
frozen. Its candidate binary SHA-256 is
`a4a5aaf26fc9c2d86132da59a36defeff733555ae784519da0b9161b9dd42e04`. On the
game-disjoint test set it improves overall NLL 2.6420→2.6252 and hidden-action
NLL 2.7175→2.4587. On the selected 91 hidden-arrival loss positions it reduces
referee-fatal choices only 83→73. The older 83→47 hidden-only comparison is
invalidated by the fitting mismatch and cannot be used for this comparison.
On 25 nonfatal king-move controls, it and v35 both choose 0 immediately fatal
moves; each chooses a listed safe non-king alternative in 4/25.

The four-pair full-clock color-swapped self-play screen finished **3–5** for
the full refit: candidate White 3–1, candidate Black 0–4; paired scores
0.5, 0.5, 0.5, 0.0. White won 7/8 games, so the strong seat effect makes this
small sample noisy; nevertheless the candidate loses the head-to-head screen
and is not ready to promote. It is research-only.

I audited the four candidate-as-Black terminal decisions. Three came directly
after a White rook arrived on a square unseen by Black, then Black made a move
that left its king capturable. In one case the true-board audit found no
immediately safe legal alternative. In the other three, safe alternatives
existed. Replaying those exact prefixes with frozen v35 versus the full-refit
candidate found 3/4 versus 4/4 immediately fatal choices; on one case v35 chose
a safe move while the full refit chose a fatal move. The hidden-only candidate
rescued only one of the four; a very low king-guard setting also rescued only
one. This is a tiny self-play-selected failure set, but it directly rejects
the idea that better average opponent-move prediction alone fixes the
invisible-rook defense.

Artifacts: `exclude-hidden91-fullrefit-manifest.json`,
`exclude-hidden91-fullrefit-wide-compare-91-5s.json`,
`exclude-hidden91-fullrefit-controls-compare-25-5s.json`,
`exclude-hidden91-fullrefit-selfplay-4pairs.json`,
`fullrefit-blackloss-compare.json`, `hiddenonly-blackloss-compare.json`, and
`fullrefit-guard-blackloss-compare.json`. No submission ZIP changed. A
promising next intervention needs to model the danger of an
opponent's newly hidden slider arrival directly or use a calibrated tail-risk
safety decision; it must pass full-game tests before promotion.

### Corrected game-excluded hidden-feature fit

The fitter now optimizes selected hidden-feature weights as deltas around the
frozen v35 logits, making optimization and validation match the full runtime
model. Refit after excluding all 91 target games gives
`MM_CHECK_UNSEEN=0.20237` and `MM_THREAT_UNSEEN=0.39288`, rather than the
invalid 1.354/0.591 weights. On the game-disjoint test set, corrected hidden-two
NLL is 2.63854 vs frozen 2.64202 overall; top-1 is 26.27% vs 26.31% and Brier
.84745 vs .84696, so there is no broad predictive win. In the true-move
hidden-check slice (n=204), NLL is 1.8918 vs 2.0364; for hidden-threat moves
(n=862), NLL is 2.5458 vs 2.8433. These subgroup metrics are replay prediction,
not playing-strength evidence.

The corrected binary was replayed on the same four candidate-as-Black loss
prefixes from the previous full-clock screen. It chose a referee-fatal move in
all 4; v35 did so in 3/4. This is a tiny loss-selected sample, but adverse
evidence: reject this specialist for promotion. Binary SHA-256:
`eee414bd459a8d9fb6957fe0e4315a89887bd7cb7b5cfdb2c2fb30ffb59ab2ec`.

## Reproduction

The small pilot dataset is on the user-authorized Seagate disk:
`/media/henrytan/seagate1/iamavirus/move-model-20261024/candidates.jsonl`.
Its SHA-256 is `a7c8670b7052a746ffe010f235c9b15792b453801291051677da9d7515dd0f81`.
The feature-oracle source hashes are `board.c`:
`4073412a224fb2ef14ce5aaeab714f519c08187fb38e7e9a3b3e9db768586ca0` and
`movemodel.c`:
`fb80064af6f7a2e7cf0b268ae7fc41657b0246c7ac07781968c176cccdf7f89d`.

```sh
gcc -std=c11 -O2 -Wall -Wextra \
  -I/tmp/iamavirus-v35-exact-trace/src \
  astra-submissions/tools/move_model_features_probe.c \
  /tmp/iamavirus-v35-exact-trace/src/board.c \
  /tmp/iamavirus-v35-exact-trace/src/movemodel.c -lm \
  -o /tmp/move_model_features_probe
python3 astra-submissions/tools/extract_move_model_dataset.py \
  --replay-root astra-submissions/analysis \
  --replay-root astra-submissions/snapshots \
  --probe /tmp/move_model_features_probe \
  --out /media/henrytan/seagate1/iamavirus/move-model-20261024/candidates.jsonl \
  --teams 'Greek Gift' 'Knight Vision' 'Strongly Invisible' \
    'Decent Chess Bot' 'Instructors' duck 'Mist Opportunities' \
    'TA Baseline A' 'TA Baseline S' 'TA Baseline P' IAmAVirus \
  --exclude-teams IAmAVirus
python3 astra-submissions/tools/fit_conditional_prior.py \
  /media/henrytan/seagate1/iamavirus/move-model-20261024/candidates.jsonl \
  --out astra-submissions/analysis/move-model-refit-20261025/prior-fit-report.json
python3 astra-submissions/tools/build_hidden_prior_candidate.py \
  /tmp/iamavirus-v35-exact-trace /tmp/iamavirus-v35-hiddenprior
```

For the recent sample, run the selector against `data/raw/accepted.jsonl`, then
pass its manifest via `--game-list` with
`--decision-stride 8` and `--replay-root data/raw/games` to the extractor.
