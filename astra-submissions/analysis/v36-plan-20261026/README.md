# v36 planning evidence

The recommendation is in [the human-readable plan](../../../docs/v36-plan.md).
[decision-contract.md](decision-contract.md) records the agreed acceptance gates,
owners, budgets and stop rules. Fable's agreement is in
[chatroom 164](../../../chatroom/164-fable-v36-analysis-and-plan.md).

These files are planning and analysis artifacts. They are not a claim that the
candidate passed the fresh-set, full-game or release gates.

| File | Purpose |
| --- | --- |
| `analyze_evidence.py` | Independent analysis of the four existing paired replay sets; never runs an engine or fits a model |
| `b2-evidence.json` | Complete paired counts, CP changes, game-cluster intervals, fatal-case differences, control-veto rates and input hashes |
| `artifacts.json` | Pre-fix and corrected candidate hashes, baseline/opponent hashes, source revisions, ZIP-member hashes and the superseded queue's provenance |
| `opponent-environment.json` | External Misty environment content hashes, installed versions, interpreter and Stockfish binary; the opponent ZIP contains only a wrapper |
| `decision-contract.md` | Fresh-data definition, exact thresholds, fixed compute budget, source-review obligations and release decision |

To reproduce the completed replay analysis on this machine:

```sh
python3 astra-submissions/analysis/v36-plan-20261026/analyze_evidence.py \
  --results /home/henrytan/fable-persist/suite/v20 \
  --out /tmp/v36-b2-evidence.json
```

The input suites and result files are outside Git, under the path above. Their
full SHA-256 hashes are in the report. Join decisions by **`game:k`**, where k
is our decision count, not the replay's ply index. All four sets have complete,
unique paired IDs and no reported execution errors. Only positions with CP
scores in both arms enter CP differences; missing CP values are not zeros.

Confidence intervals resample games 2,000 times with seed 20261026036, keeping
all scored decisions from each sampled game. The mean is decision-weighted;
resampling clusters accounts for multiple decisions from one control game.
These intervals describe the selected development data, not selection/tuning
uncertainty, the future opponent pool or Elo. B2 was designed after seeing B1's
failures in the later loss set, so that set is no longer untouched confirmation.

No additional replay, training run or full-game experiment was launched by Astra
to produce this analysis. Fable stopped the old bench after three recorded
games when the fallback correction superseded its candidate. The corrected
candidate is separately hashed and has not been benched; a final artifact freeze
and its release gates are planned after review. Old results cannot certify the
new bytes.
