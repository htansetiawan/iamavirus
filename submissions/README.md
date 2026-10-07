# Submissions tracker

What was uploaded to the arena, from which commit, with which model, and what
happened. The arena numbers its versions by upload order per team, so they do
**not** line up with the `versions/vN-*.md` design notes; this file is the map.
Keep it current: one row per upload, and append to the log as results arrive.

Team id `a2c35173659545c99752376a70418438` (`IAmAVirus`). Public record:
`https://6s890.lids.mit.edu/api/leaderboard/a2c35173659545c99752376a70418438/versions`
(`python -m learning.ingest --team IAmAVirus` pulls the replays).

## Arena version ↔ archive map

| arena version | uploaded (UTC) | archive | sha256 (prefix) | source commit | mode | model | design note | status |
|---|---|---|---|---|---|---|---|---|
| 1 | 2026-10-07 03:53 | (pre-session) | — | — | cpp | — | [v2](../versions/v2-cpp.md) | 0 games |
| 2 | 2026-10-07 04:15 | (pre-session) | — | — | cpp | — | [v2/v3](../versions/v3-belief-consistency.md) | 4W–0D–10L |
| 3 | 2026-10-07 04:51 | (pre-session) | — | `351ca0b` | cpp | — | [v3](../versions/v3-belief-consistency.md) | 10W–0D–14L |
| 4 | 2026-10-07 05:47 | (pre-session) | — | `5e0ef63` | cpp | — | [v4](../versions/v4-king-safety.md) | 102W–6D–156L (264 games) |
| 5 | 2026-10-07 14:44 | `iamavirus-v6-hybrid.zip` | `662a989aa56c` | `61d33f9` (tree; published in `e2dc3b2`) | **hybrid** | stage A release `v1` | [v6](../versions/v6-neural.md) | **active**, 0 games at upload |
| 6 | 2026-10-07 14:46 | `iamavirus-v6-cpp.zip` | `6b6b1f338501` | `61d33f9` (tree; published in `e2dc3b2`) | cpp | — | [v6](../versions/v6-neural.md) | validated, inactive |
| 7 | 2026-10-07 14:47 | `iamavirus-cpp.zip` (committed upstream as "Add v5") | `eb994e3d89e4` | `f236ad7` (engine.cc identical) | cpp | — | [v5](../versions/v5-opponent-prior.md) + turn deadline | inactive; **confirm this is v7** |

So the design note "v5" ([versions/v5-opponent-prior.md](../versions/v5-opponent-prior.md):
the opponent-move prior, plus the `f236ad7` turn deadline) is arena **v7**, and
the design note "v6" is arena **v5** (hybrid) and **v6** (cpp). The v7 archive
predates the v6 repairs: it still has the degenerate resampling and the
castling-rights rebuild, and has no neural files.

## What is in the two v6 archives

Both contain the same engine source: the repaired search and belief filter
(five fixes, see `HANDOFF.md` "Measured") plus the upstream turn deadline
(`f236ad7`), the neural adapter, and `run.sh` with the packaged default mode.
They differ only in the mode and the `model/` directory.

| | `iamavirus-v6-cpp.zip` | `iamavirus-v6-hybrid.zip` |
|---|---|---|
| `run.sh` default | `FOW_MODE=cpp` | `FOW_MODE=hybrid` |
| `model/` | absent | `observe.onnx`, `score.onnx`, `model_manifest.json` |
| decision procedure | repaired search + matrix game | same, over the union of search top 6, policy top 8, lowest-risk top 8 (≤ 12 rows); neural danger logged, not a veto |
| if ONNX Runtime or the graphs fail | n/a | logs one line and plays `cpp` for the game |

Model in the hybrid archive (release `releases/v1`, not in git):

| field | value |
|---|---|
| checkpoint | stage A pretraining, 10 epochs, step 3000, sha256 `cbda47a0ef03…` |
| graphs | observe `a085a1a2d16d…`, score `0dc8118735c6…` |
| dataset | manifest `v1`, content sha256 `2532ba77de4f…` (1,500 public games, 88,371 train decisions) |
| parameters | 1,872,394 |
| validation | policy top-1 0.337, belief hidden-square accuracy 0.826, danger Brier 0.044 |
| parity | ONNX vs PyTorch PASS, 425 held-out decisions, worst diff ≤ 6e-6 |
| runtime (referee, 180+2) | load 0.020 s, inference p99 0.15 ms, peak RSS 168 MiB |

Not in the archive: the PPO checkpoint (`releases/v2-ppo`). Six iterations
were inconclusive against the pretrained model (+0.10 and +0.03, intervals
include zero), so the pretrained graphs shipped.

## Local evidence before upload (small samples; see `HANDOFF.md`)

- hybrid vs cpp, real clocks through `referee.py`, 3 colour-swapped pairs: hybrid 6/6.
- Both archives unpacked into a clean directory, built, and played a referee game
  against `baseline.py`; longest turn 4.001 s against the 4.0 s budget.
- Not done: the specification's 200-pair evaluation, any ablation of the hybrid
  candidate budget, a danger calibrator.

## What to watch in the arena

- **Elo and per-version W/D/L** at the versions endpoint; the team rating is
  shared across versions (K=8), so compare versions by their own records and
  opponent mix, not by the rating alone.
- **Forfeits**: `Illegal move`, `Time forfeit`, `Bot stopped responding` in the
  game reasons. Any of these in v5/v6 is a bug, not a strength signal
  (`python -m learning.ingest --team IAmAVirus --diagnostics` archives the reports).
- **Private stderr** (Games tab → Log, with the team token): each decision line
  starts with `s<seed> n=<move> mode=<cpp|neural|hybrid>` and carries
  `cands=uci:policy/danger/particle-risk`; `model unavailable` or
  `inference failed` lines mean the hybrid fell back to `cpp` for that game.
- The five regression games (`cxgvxx6h`, `rz89dmpy`, `92of99z7`, `ky4pm8o2`,
  `gxmut7rr`, `zviidq21`) are the failure family; new losses of the same shape
  (king onto or capturing on a square covered from the fog) are the thing to count.

## Log

| date (UTC) | event |
|---|---|
| 2026-10-07 14:44 | v5 (hybrid archive) uploaded and activated |
| 2026-10-07 14:46 | v6 (cpp archive) uploaded, inactive |
| 2026-10-07 14:47 | v7 uploaded: `iamavirus-cpp.zip`, the design-v5 engine from `f236ad7`, inactive |
| 2026-10-07 ~15:00 | team rating 1453 over 302 games before any v5/v6 game |

## How to add a row

```bash
bash package.sh submissions/iamavirus-<tag>.zip [releases/<v>] [cpp|neural|hybrid]
sha256sum submissions/iamavirus-<tag>.zip
git log -1 --format=%h          # the source commit
```
Upload on the Submit page, then record the arena's version number here.
