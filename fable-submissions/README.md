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
| *(not yet uploaded)* | — | `iamavirus-v6.1-cpp.zip` | `ed79ce45b31e` | see `git log` (v6.1) | cpp | — | [v6](../versions/v6-neural.md) + two repairs below | built 15:30 UTC |
| 9 | 2026-10-07 17:08 | `iamavirus-v9-hybrid.zip` | `3076b45fb01d` | `3d65839` tree | **hybrid** | stage A release `v1` | v5 behaviour (12 rows) + fatal-cell risk charge + safety rows + deadline made harmless (cells shrink; skipped cells get a one-ply verdict) | **active**; 6W–0D–0L at 17:45 UTC |
| **10** | 2026-10-07 17:29 | `iamavirus-v10-hybrid.zip` (uploaded under its then-name `iamavirus-v12-hybrid.zip`) | `6f57a44ec814` | `ac22cdd` | **hybrid** | stage A release `v1` | v9 + safety rows reserved in the hybrid union + node-capped deadline fallback (from Astra's review) | uploaded 17:29 UTC; 0 games at 17:50 |
| **12** | 2026-10-07 ~20:45 | `iamavirus-v12-hybrid.zip` (was `iamavirus-v11-candidate-hybrid.zip`) | `68a89006f6c2` | see `git log` (v11 candidate, 19:44 UTC) | **hybrid** | stage A release `v1` | v10 + population-wide exposure term + pawn visibility deductions (**on**, three-seed check) + clock scaling by difficulty + underpromotion rule + per-particle move memory. Balanced benchmark, 634 seats: king losses 6.46%, true attacker held 0.228, left ≥3 en prise 7.70% (real player 8.04%), survival of the fatal ply 54–58% by seed (off: 54–58%). Paired vs archived v5 at real clocks (its engine, as the v12-candidate bytes): **10W–0D–10L over 20 games** (16-game gate 9–7 plus a 4-game smoke of the final bytes 1–3), paired score 0.500, bootstrap 95% 0.300–0.700 (v9 on the same gate: 0.472, 0.306–0.639); clean-dir build OK | built 19:44 UTC; **uploaded by the user as arena v12**; file renamed; v11 (Astra) was active at upload |
| *(label; alternative next upload)* | — | `iamavirus-v11-candidate-twoply-hybrid.zip` | `022fd76bb778` | see `git log` (two-ply candidate, 20:03 UTC) | **hybrid** | stage A release `v1` | the v11 candidate + **two-ply hidden-threat term** at weight 1.0 (`FOW_HIDDEN_THREAT`): decisions that leave the opponent a ≥3-point hidden threat one quiet move away fall 11.74% → 7.35% (real players 9.60%) with king losses, one-ply en prise and fatal-ply survival unchanged (balanced 634 seats). Real-clock lanes vs the v11 candidate running; clean-dir build OK | built 20:03 UTC; **upload after its lanes hold; whichever candidate is uploaded first becomes arena v11** |
| *(label; next upload)* | — | `iamavirus-v11-hybrid.zip` | `d549f8b5379d` | see `git log` (v11 candidate) | **hybrid** | stage A release `v1` | arena v10 + population-wide one-ply **exposure term** (`exposure_mode=1`): offline 634 seats, left ≥3 en prise 7.83% vs 10.10%, king losses 6.55% both, survival 58% both; clean-dir build + referee game OK, 4.0 s/turn, 0 skipped cells | built 18:05 UTC; **not uploaded; rename to the arena number at upload** — **superseded** by `iamavirus-v11-candidate-hybrid.zip` (file removed 19:55 UTC; bytes in git history) |
| — | — | `iamavirus-v11-cpp.zip` | `44c95a14a849` | same | cpp | — | same engine, no model | not uploaded — **superseded**; file removed 20:05 UTC (cpp sibling of the exposure-only v11; bytes in git history) |
| *(label; candidate)* | — | `iamavirus-v12-candidate-hybrid.zip` | `0ed702004ff0` | `2b1099b` | **hybrid** | stage A release `v1` | v11 + visibility deductions in the belief + clock scaling by difficulty + underpromotion rule + per-particle move memory (hand prior) | built 19:50 UTC; paired gate vs v5 queued — **superseded** by `iamavirus-v11-candidate-hybrid.zip` (same engine behaviour; its lanes are the candidate's evidence) |
| *(label; candidate)* | — | `iamavirus-v12-candidate-v2model-hybrid.zip` | `3ff351e4ec50` | `2b1099b` | **hybrid** | stage A release `v2` (3,258 games, top-team-weighted cloning) | same engine with the v2 model | built 19:50 UTC; paired gate vs v5 queued — **superseded** by `iamavirus-v11-candidate-hybrid.zip` (same engine behaviour; its lanes are the candidate's evidence) |
| **11** | 2026-10-07 ~20:35 | `astra-submissions/iamavirus-v12-hybrid.zip` | `a5f806d0039f` | `5bc00b6` (Astra) | **hybrid** | stage A release `v1` (unchanged) | Astra's conservative trial: the exposure-only runtime (bytes of the former `iamavirus-v11-hybrid.zip`, `d549f8b5379d`) plus provenance; label 12 by the +1 rule. Astra's gates: nine unit suites, 18,625 referee checks; historical 37 target seats material exposure ≥300 cp 21 → 12 of 274 decisions (duck 7 → 4, TA-A 3 → 1, TA-S 11 → 7), king losses 20/274 unchanged; 2W–2L vs arena v10 at 180+2 | **uploaded by the user as arena v11** (the file keeps Astra's label 12); active on upload |
| *(label only)* | — | *(Astra)* `astra-submissions/iamavirus-v10-hybrid.zip` `52b7217d5d83` and `iamavirus-v11-hybrid.zip` `797028f47af9` | | Astra fork of the arena-v5 bytes | hybrid | stage A release `v1` (unchanged) | v5 + one invariant: the final hybrid union keeps at least one minimum-particle-risk move. Offline 7.02% vs 7.10% king losses (`astra-submissions/v10.md`, `implementation/RELEASE.md`) | **not arena numbers**: whichever is uploaded next becomes arena v11 and should be renamed then |
| — | — | `iamavirus-v9-cpp.zip` | `7b8b4343dd79` | `3d65839` tree | cpp | — | v9 engine, no model | not uploaded |
| — | — | `iamavirus-v10-cpp.zip` | `954310feee0d` | `ac22cdd` | cpp | — | v10 engine, no model | not uploaded |
| 8 (assumed; confirm) | 2026-10-07 16:08 | `iamavirus-v6.1-hybrid.zip` | `0e4db2bf507b` | see `git log` (v6.1) | **hybrid** | stage A release `v1` | same | built 15:30 UTC |
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
| 2026-10-07 15:05 | v7 (design-v5 engine): **2W–10L** vs the TA baselines, including an **illegal move** forfeit (`m6uovffl`: it sent `e8c8`, castling with a right the king had forfeited — the `Recover` rights-rebuild bug fixed in the v6 archives). Of its 10 king-capture losses, 9 were taken by a piece invisible to us at our last view, 5 of them king moves into the covered square: the failure family again. |
| 2026-10-07 20:46 | **Arena v12 = Fable's first candidate** (`68a89006f6c2`), file renamed `iamavirus-v12-hybrid.zip`. Arena v11 (Astra, `a5f806d0039f`) is the active version; both at 0 games. The two-ply and full archives keep their `v11-candidate-*` names until their queued lanes have started; they are candidates for arena v13. |
| 2026-10-07 20:36 | **Arena v11 = Astra's `astra-submissions/iamavirus-v12-hybrid.zip`** (`a5f806d0039f`, exposure-only runtime). The user will try Fable's first candidate next; when uploaded it becomes arena v12 and `iamavirus-v11-candidate-hybrid.zip` is renamed `iamavirus-v12-hybrid.zip`. |
| 2026-10-07 20:25 | Astra v12 trial archive (`a5f806d0039f`) mapped as a repository trial candidate. Duck's active version changed to v5 at 20:15 UTC; new duck results are not pooled with the v4 history. |
| 2026-10-07 20:08 | Smoke lane of the final v11-candidate bytes vs v5: 1–3 over 4 games; all 20 real-clock games: 10–10, paired 0.500 (0.300–0.700). Two-ply candidate published after the suite passed (594 checks). |
| 2026-10-07 20:05 | **Two-ply candidate built** (`022fd76bb778`): the one new term measured by a true-board oracle metric added to the benchmark (`left a 2-ply hidden threat`), 11.74% → 8.34% (w 0.5) → 7.35% (w 1.0), nothing else moves. Two real-clock lanes vs the v11 candidate queued. v10 at 37W–1D–34L. |
| 2026-10-07 20:00 | Paired gate of the v11 candidate's engine vs archived v5 complete: 9–7 over 16 games, score 0.562 (0.375–0.750). `iamavirus-v12-candidate-hybrid.zip` removed as superseded (same behaviour; bytes in git history at `aabd4d1`). v10 at 35W–1D–31L. |
| 2026-10-07 19:55 | **v11 candidate built** (`68a89006f6c2`): deductions kept on after the three-seed survival check (off 368/345/343, on 341/365/347); balanced harness; exposure-only v11 file and the v2-model candidate removed as superseded. v10 at 31W–1D–26L; rating 1525 vs TA Baseline A 1528, TA Baseline S 1708, duck 1909. |
| 2026-10-07 19:50 | v12 candidates built (full tree; one with the v2 model); gates queued. v10 at 15W–0D–9L incl. its first win vs duck (`chccdlu3`). |
| 2026-10-07 18:05 | v11 candidate built (exposure term). v10 at 6W–0D–4L. |
| 2026-10-07 17:08 | **v9 uploaded and activated** (the first v9 build, sha `3076b45f`); 6W–0D–0L by 17:45 UTC. The rebuilt archive with Astra's two fixes is renamed v10 and held back. |
| 2026-10-07 17:05 | v9 archives built (see rows). v8 ended 9W–15L; v5 re-activated at ~16:45 and immediately beat TA Baseline P twice (both colours). |
| 2026-10-07 16:10 | v5 (hybrid) final record **22W–2D–6L** (score 0.77; opponents mostly baseline.py, Apricot Squad, TA Baseline A/S). Losses `wcfhi31w` and `mgm3sltv` share one shape: our king on h1 with a hidden bishop on b7 on the open long diagonal; the belief rated every move at ~10% risk, so the risk term could not separate the fatal move. v8 (v6.1-hybrid, assumed) uploaded and activated at 16:08. |
| 2026-10-07 15:25 | v6 (cpp): 2W–6L (wins vs Apricot Squad ×2 incl. `rz1wn4kx`; losses vs TA Baseline S ×2, duck ×2, Instructors ×2). Analysis in "v6.1" below. v5 (hybrid) re-activated. |
| 2026-10-07 15:05 | v5 (hybrid): 1W–1L vs TA Baseline P; the loss (`nn8dt0e9`, 108 plies) was `f7f6` exposing the king to an unseen piece on g2. v6 (cpp) was then made active. |

## Naming convention (from 2026-10-07 evening)

Archives are named after the arena version they will be uploaded as, plus the
mode: `iamavirus-v9-hybrid.zip` is the file to upload as arena v9. The arena
numbers uploads sequentially per team, and **both agents (Fable and Astra)
draw from that one sequence**: before building an archive, take the next
number after the highest one in this table (uploaded or reserved), add the row
here with "reserved", and fill in the upload time once the versions endpoint
shows it. Never reuse a number. Earlier files (`v6-*`, `v6.1-*`) predate the
convention; the table maps them.

## Record by opponent, v5–v8 (as of 16:50 UTC)

| opponent | v5 | v6 | v7 | v8 |
|---|---|---|---|---|
| Apricot Squad | 7-0-1 | 2-0-0 | | 2-0-0 |
| Greek Gift | | | | 0-0-2 |
| Instructors | | 0-0-2 | | |
| TA Baseline A | 2-1-1 | | 1-0-5 | 1-0-1 |
| TA Baseline P | 6-0-1 | | 1-0-1 | 5-0-5 |
| TA Baseline S | 2-1-3 | 0-0-2 | 0-0-4 | 1-0-3 |
| baseline.py | 6-0-0 | | | |
| duck | | 0-0-2 | | 0-0-4 |
| **total** | **23-2-6** | 2-0-6 | 2-0-10 | 9-0-15 |

v5 re-activated at ~16:45 UTC after v8's record. **Correction:** the turn
deadline was already in v5's bytes (Astra, `chatroom/003`), so it is not the
v8 cause; see `chatroom/007`. Leading explanation: schedule and sample size.

## v6.1: two repairs from the first v6 arena losses

Replaying the losses offline through the engine (`HANDOFF.md`, "Measured")
found a payoff bug: a matrix cell where a move loses the king outright scored
a flat −30,000, while a move that only *might* lose it scored its search value
minus its risk charge, which in a bad position lies below −30,000 — so the
certain loss outranked the probable escape. In `1sv22xki` ply 40 one seed in
four chose a 100%-risk rook move over a 33%-risk king move for that reason.
Fatal cells now carry the same risk charge, and the shortlist is extended
with any move the population rates safer than everything the search kept.
Regression test: `engine_test: ShortlistKeepsTheSafestMovesThePopulationKnows`
(all four seeds now choose the safest measured move). Of the eight v6 games
(2W–6L), five losses were decided with ≤ 3 safe moves left, i.e. the position
was already lost; the remaining three were belief failures where the
population rated a truly fatal move at 0% risk.

## How to add a row

```bash
bash package.sh fable-submissions/iamavirus-<tag>.zip [releases/<v>] [cpp|neural|hybrid]
sha256sum fable-submissions/iamavirus-<tag>.zip
git log -1 --format=%h          # the source commit
```
Upload on the Submit page, then record the arena's version number here.
