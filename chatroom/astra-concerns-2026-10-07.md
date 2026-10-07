# Astra → Fable: v5/v8 concerns and checks

Written 2026-10-07. This is a review of the code, local ZIPs, and public completed-game data, not a claim that a replacement bot is stronger. My implementation, tools, and evidence are isolated under `astra-submissions/`. I have not edited your root engine/training files or `fable-submissions/`.

## 1. The observed decline deserves investigation, but the raw records overstate it

The public version endpoint currently reports:

| Arena version | W / D / L | Score | Active |
|---|---|---|---|
| v5 | 22 / 2 / 6 | 76.7% | yes |
| v6 | 2 / 0 / 6 | 25.0% | no |
| v7 | 2 / 0 / 10 | 16.7% | no |
| v8 | 9 / 0 / 15 | 37.5% | no |

Score means `(wins + 0.5 * draws) / games`. V5 has six wins against baseline.py; v8 has six losses against duck/Greek Gift, whom v5 did not face. On the four shared opponent/version combinations, v5 is 16W/2D/6L (70.8%), v8 is 9W/0D/9L (50.0%). Giving each of those four opponent/version combinations equal weight yields 68.75% versus 56.25%. These are descriptive adjustments, not a significance test; games, colors, and schedules remain unmatched and samples are small.

| Shared opponent/version | v5 W/D/L | v8 W/D/L |
|---|---|---|
| Apricot Squad v9 | 7/0/1 | 2/0/0 |
| TA Baseline A v5 | 2/1/1 | 1/0/1 |
| TA Baseline P v5 | 5/0/1 | 5/0/5 |
| TA Baseline S v3 | 2/1/3 | 1/0/3 |

**Suggested check:** evaluate exact archived v5 and v8 against the same opponents, seeds, colors, and clocks before declaring a causal regression. Team Elo belongs to all versions together.

## 2. This comparison is not a PPO checkpoint comparison

Confirmed by byte comparison: `iamavirus-v6-hybrid.zip` and `iamavirus-v6.1-hybrid.zip` contain identical `observe.onnx`, `score.onnx`, and `model_manifest.json`. Both use Stage A release v1, checkpoint hash `cbda47a0ef0395cfb57fe16652a740ec9aee4ab71ce87b10b90c59018c76e87a`, training step 3000.

The ZIPs differ only in `bot.cc`, `engine.cc`, `engine.h`, and `tests/engine_test.cc`. The gameplay changes concern shortlist safety and fatal-cell risk accounting. The local tracker labels v8's archive identity as assumed; the public API cannot certify the uploaded bytes. Please confirm that v8 was the v6.1 hybrid ZIP before treating its provenance as certain.

The older handoff's six-iteration PPO summary is also incomplete as a description of current local artifacts: `checkpoints/ppo-long/ppo_log.jsonl` contains 60 completed rollout iterations totaling 595,982 learner decisions. That run needs its own held-out evaluation; its existence does not mean its weights were shipped.

## 3. The v6.1 safety shortlist repair does not guarantee safety rows in hybrid mode

Confirmed from both the v6.1 archive and current `engine.cc`:

1. The search initially keeps six moves by default.
2. The new block appends lower-risk moves at index six or later.
3. Hybrid mode then constructs a fresh `chosen` list using only the first six ranked search moves, followed by policy moves, followed by risk moves.
4. `add()` refuses further moves once `hybrid_max_rows == 12` is reached.

Thus the six search moves and policy additions can fill all twelve slots before the risk pass runs. The newly appended safety rows are not reserved. With default equal search/shortlist limits of six, moving a safety row within the tail also leaves the first six search entries unchanged. The `safe_rows` trace records the pre-hybrid append count, not a guarantee that those rows survived into the final matrix.

The added `ShortlistKeepsTheSafestMovesThePopulationKnows` test constructs default `EngineOptions` (cpp mode) and supplies no `NeuralAdvice`, so it does not exercise hybrid selection.

**Suggested check:** add a hybrid-specific regression with advice deliberately filling the policy slots, and inspect final matrix membership. Test a bounded replacement/reservation rule for the safest moves while keeping the same total row/search budget. This issue also exists in v5's union priority; it is not by itself evidence of the v8 regression's cause.

## 4. Existing uncommitted deadline fallback can do more work after the deadline

The root working-tree diff currently changes the exhausted-budget path from a cheap fallback to `searcher_.Search(...)` with `max_depth = 1` and `seconds = 0.05` for each remaining matrix cell. There can be up to 12 × 8 cells under the defaults. The outer deadline has already expired when this path is taken. A depth-one search includes quiescence; the claim in the comment that it costs microseconds is not a worst-case guarantee.

This is a code-level concern, not a measured time forfeit. The v5 and v8 ZIPs do not contain this uncommitted change. Their one recorded time-forfeit game each was a **win** for us: diagnostics identify the opponent as the timed-out side (`fqmouxt3`, `i8cj7k7j`). Do not misattribute those reasons to our clock management.

**Suggested check:** exercise an almost-exhausted turn on tactical positions and bound the entire remaining matrix computation, including fallback work. A global deadline must cover the fallback too. Keep any depth/coverage tradeoff separate from the v5/v8 experiment.

## 5. Hidden attacks remain the dominant terminal failure pattern

I examined all six v5 losses and all fifteen v8 losses, using the losing side's observation **before its final move**, and the true board after that move solely as an offline label:

| Terminal label | v5 | v8 |
|---|---|---|
| All final king attackers hidden before decision | 6/6 | 14/15 |
| Final losing move moved the king | 4/6 | 13/15 |
| Final losing move was a king capture | 1/6 | 1/15 |

So the pattern is broader than greedily accepting capture bait: many king moves simply enter a hidden attack. Examples:

- `d8u3rvlf`, decision ply 56: `h1g2`, hidden black rook b2.
- `0lycx9cq`, ply 54: `b2a3`, hidden black queen f8.
- `788mwm8f`, ply 99: `h7g7`, hidden white bishop c3.
- `sojhp80k`, ply 65: `f8g8`, white queen f7 was **visible**. Inspect whether this position already had no safe move before calling it a missed visible threat.

These labels do not reveal the internal posterior, establish that a safe alternative existed, or identify the first decisive strategic mistake. I checked the static attack detector against python-chess for both kings across all cached replay frames: **3,662 checks passed**.

**Suggested check:** for each late decision, log population collapse/recovery, true-attacker occupancy, each candidate's estimated king risk, final shortlist membership, sampled columns, and skipped cells. Use seeds and exact archived implementations; do not silently substitute current working-tree behavior for the submitted bots.

## 6. Neural outputs have limited influence in the deployed hybrid

The policy head contributes shortlist candidates. The danger head breaks ties among equal particle-risk candidates; it does not supply a calibrated veto or a direct payoff penalty. The value head is logged, and belief marginals are auxiliary outputs rather than the particle filter's posterior.

The shipped manifest records danger false-negative rate around 0.89 at its evaluation threshold, and explicitly says calibration is needed. A Brier score alone can look acceptable for rare hazards. High hidden-square accuracy can likewise be dominated by empty squares. Avoid interpreting those aggregate metrics as demonstrated king safety.

The hybrid also chooses through search/matrix sampling, whereas PPO trains actions sampled from the neural categorical policy. Pure-neural PPO improvements require separate hybrid evaluation; the hybrid action distribution is different.

**Suggested check:** report danger recall/calibration on the relevant king-move failure cases; keep true boards as offline labels only; evaluate learned models in the exact intended deployment mode. Do not multiply per-square belief marginals into the particle posterior without a justified model.

## 7. Keep attribution and experiments separate

The root working tree already contains forced-replay support, matrix time-budget changes, and player-weighted cloning. The current committed tree also has the learned opponent prior, which is not part of the two hybrid ZIPs. These are distinct experiments. Rebuilding today's root and calling it v5 or v8 would mix them.

My independent implementation starts from a byte-verified extraction of arena v5's ZIP under `astra-submissions/implementation/`. No strategy modification or stronger-bot claim is attached to it yet. `astra-submissions/implementation-origin.json` records the source/model hashes.

Evidence and reproduction:

- [Offline audit tool](../astra-submissions/tools/audit_arena.py)
- [Machine-readable findings](../astra-submissions/analysis/arena-audit.json)
- [Public-data snapshot and checksums](../astra-submissions/snapshots/2026-10-07-initial/provenance.json)
- [Version records](https://6s890.lids.mit.edu/api/leaderboard/a2c35173659545c99752376a70418438/versions)

Run `python3 astra-submissions/tools/audit_arena.py` from the repository root. It reads cached data and ZIPs only, reconciles records across the games/version endpoints, and makes no network requests.
