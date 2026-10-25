# v35 hidden-threat move-prior refit pilot

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

| Model | Overall NLL ↓ | Top-1 | Brier ↓ | Candidate ECE ↓ | Hidden-threat NLL ↓ | Hidden-threat top-1 |
|---|---:|---:|---:|---:|---:|---:|
| Frozen v35 | 2.6629 | 26.90% | 0.8462 | 0.00184 | 2.8726 | 22.58% |
| Frozen v35 + two fitted hidden-threat weights | 2.6766 | 26.54% | 0.8523 | 0.00094 | **2.4271** | **30.65%** |
| Regularized full refit | **2.6592** | **27.27%** | 0.8478 | 0.00173 | 2.7073 | 27.42% |

Validation selected L2 strength 1.0 for both refits. The two-feature update
helps the small hidden-threat slice while worsening overall NLL, top-1 and
Brier. The full refit is essentially tied overall and improves hidden-threat
top-1 modestly while worsening hidden-threat NLL. No model dominates. These
differences are not strength evidence, and 62 hidden-threat examples are too
few for a release decision.

## Decision

Do not change the submitted v35 coefficients. Next, run the candidate weights
through the exact sequential belief update on game-disjoint replays, measure
truth support/rank and fatal-move decisions, then branch changed actions
through the referee. Expand the corpus with current public replays when API
access is available. Keep arena evaluation as the promotion gate.

## Reproduction

The large extracted candidate dataset is on the user-authorized Seagate disk:
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
```
