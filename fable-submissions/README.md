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
| **12** | 2026-10-07 20:45–21:15 | `iamavirus-v12-hybrid.zip` (was `iamavirus-v11-candidate-hybrid.zip`) | `68a89006f6c2` | see `git log` (v11 candidate, 19:44 UTC) | **hybrid** | stage A release `v1` | v10 + population-wide exposure term + pawn visibility deductions (**on**, three-seed check) + clock scaling by difficulty + underpromotion rule + per-particle move memory. Balanced benchmark, 634 seats: king losses 6.46%, true attacker held 0.228, left ≥3 en prise 7.70% (real player 8.04%), survival of the fatal ply 54–58% by seed (off: 54–58%). Paired vs archived v5 at real clocks (its engine, as the v12-candidate bytes): **10W–0D–10L over 20 games** (16-game gate 9–7 plus a 4-game smoke of the final bytes 1–3), paired score 0.500, bootstrap 95% 0.300–0.700 (v9 on the same gate: 0.472, 0.306–0.639); clean-dir build OK | built 19:44 UTC; **arena v12**; active 20:47–21:15 UTC, 7W–1D–8L over 16 games (two losses to Decent Chess Bot, two to TA Baseline P; see HANDOFF for the three patterns); v10 reactivated |
| *(label; alternative next upload)* | — | `iamavirus-v11-candidate-twoply-hybrid.zip` | `022fd76bb778` | see `git log` (two-ply candidate, 20:03 UTC) | **hybrid** | stage A release `v1` | the v11 candidate + **two-ply hidden-threat term** at weight 1.0 (`FOW_HIDDEN_THREAT`): decisions that leave the opponent a ≥3-point hidden threat one quiet move away fall 11.74% → 7.35% (real players 9.60%) with king losses, one-ply en prise and fatal-ply survival unchanged (balanced 634 seats). Real-clock lanes vs the plain candidate (arena v12): **7W–2D–7L over 16 games, paired score 0.500, bootstrap 95% 0.281–0.750**: even; clean-dir build OK | built 20:03 UTC; **upload after its lanes hold; whichever candidate is uploaded first becomes arena v11** |
| **13** | 2026-10-07 22:33 | `iamavirus-v13-hybrid.zip` (was `iamavirus-v11-candidate-full-hybrid.zip`) | `39fb4480e0b7` | see `git log` (full candidate, repacked after the suite) | **hybrid** | stage A release `v1` | the two-ply candidate + **clock defaults** (cap 7 s, hard cap 12 s, divisor 20: arena games ended with a median 121 s unused) + **matrix cells on both cores** (`cell_threads` 2). Suite 609 checks, 0 failures, worst budget overrun 0.004 s. **Real-clock lanes vs the two-ply archive: 10W–1D–5L over 16 games, paired score 0.656, bootstrap 95% 0.406–0.875** (as White 5/8, as Black 6/8); no overruns | **arena v13, activated 22:39 UTC**; file renamed |
| *(label; candidate for arena v13)* | — | `iamavirus-v11-candidate-caution-hybrid.zip` | `323707640ae7` | see `git log` (caution candidate, 21:58 UTC) | **hybrid** | stage A release `v1` | the full candidate + **repetition charge** + **two-ply king threat** at 0.6 (king losses 6.37 → 6.01%, survival of the real fatal ply 343 → 362 of 634; material left en prise 7.63 → 8.19%) + **opening book** (176 entries from the six strongest teams, first 10 plies). Suite 622 checks, 0 failures. **Real-clock lanes vs the v13 bytes: 12W–1D–3L over 16 games, paired score 0.781, bootstrap 95% 0.562–0.938** (as White 6/8, as Black 6/8); lowest clock 11 s, hence the reserve-10 rebuild below | built 21:58 UTC; **upload after its lanes hold** |
| *(label; candidate for arena v14)* | — | `iamavirus-v11-candidate-full-v3model-hybrid.zip` | `519260f77245` | see `git log` (v3 model, 22:38 UTC) | **hybrid** | stage A release **`v3`** (4,707 games; same-split test: policy 34.5% vs 32.7%, danger false negatives 64.7% vs 87.5%, belief 83.9% vs 82.7%) | the caution engine (king threat 0.6, repetition charge, opening book) + 10 s reserve + the v3 model. **Lanes vs the v13 bytes: lane M 3.5/8 (0.438, 0.312–0.5; lost 3 of 4 as Black), lane L stopped after two draws**; the same engine with the v1 model scored 0.781 on this gate, so the v3 model does not ship | built 22:38 UTC; **not for upload** |
| *(label; candidate "v14b")* | — | `iamavirus-v11-candidate-caution-r10b-hybrid.zip` | `ada110c059ae` | worktree at `a0f5fa7` + `625f0a1` (sampled book) + `85169e1` (two-phase clock) | **hybrid** | stage A release `v1` | the v14 bytes with two changes: the opening book samples among the strongest teams' moves by frequency instead of playing one fixed line, and the clock schedule is two-phase (7 s cap and divisor 20 for the first 20 decisions, then 5 s cap and divisor 30). Motivation: v13 reached a clock of 15 s or less in 15 of 94 arena games (won 3) where v10 never did, and v13 won 19% of its 90–120-ply games against v10's 33%. | built 02:35 UTC; smoke U vs the v14 bytes (4 pairs, real clocks) running, result ~03:50 UTC |
| *(label; model-only comparison)* | — | `iamavirus-v11-candidate-v13engine-v3model-hybrid.zip` | `7248e7e78881` | engine tree `25f5dc7` (the v13 bytes' engine) + release `v3` | **hybrid** | stage A release **`v3`** | exactly the v13 engine with the v3 model, built from a worktree at the v13 commit, so its lanes vs the v13 bytes (N/O, queued after L/M) measure the model alone | built 22:55 UTC; comparison artefact, upload only if it beats v13 |
| *(label; candidate for arena v14)* | — | `iamavirus-v11-candidate-caution-r10-hybrid.zip` | `93f4ccdf03d5` | see `git log` (caution + 10 s reserve, 23:14 UTC) | **hybrid** | stage A release `v1` | the caution archive (king threat 0.6, repetition charge, opening book) with the clock reserve raised 6 → 10 s: the caution bytes' lowest clock in 14 lane games was 11 s. Caution engine vs v13 bytes 12–1–3 over 16 (paired 0.781, 0.562–0.938); **smoke of these exact bytes vs v13: 2.5/4, no overruns, lowest clock 14 s (164 plies)** | built 23:14 UTC; **cleared for upload as arena v14** |
| *(label; candidate for arena v15)* | — | `iamavirus-v11-candidate-capture-v4-hybrid.zip` | `1bf9c8d29f86` | see `git log` (capture evidence + persistence + v4, 00:32 UTC) | **hybrid** | stage A release **`v4`** (features-v2: policy 35.5%, danger false negatives 59.6%, belief 84.4%) | the v14 engine + capture evidence with two-update persistence + the v4 model, **deterministic book**. Lanes P/Q vs the v14 bytes: **5W–4D–7L over 16, paired 0.438 (0.250–0.594), as White 5/8, as Black 2/8; every game opened with the same ten plies (both sides share the deterministic book), so this is one line's result** | built 00:32 UTC; **not for upload**; superseded by the sampled-book rebuild (lane R) |
| *(label; candidate for arena v15, with Astra's repairs)* | — | `iamavirus-v11-candidate-repairs-v4-hybrid.zip` | `135fd46301a8` | see `git log` (root at a7e2829 + v4, 00:57 UTC) | **hybrid** | stage A release `v4` | the capture-plus-v4 archive plus Astra's merged repairs (own-move memory alignment, en passant carried through recovery; history modes off) and the clamp on an invalid history mode. rebuilt 01:22 UTC with the frequency-sampled book; lane R vs the v14 bytes queued behind lane P | built 00:57 UTC; **upload only if its lane beats v14** |
| *(label; candidate for arena v15, v5 model)* | — | `iamavirus-v11-candidate-repairs-v5-hybrid.zip` | `b39e11e90e56` | see `git log` (root + v5, 01:59 UTC) | **hybrid** | stage A release `v5` (features-v2, unweighted cloning: policy 35.9%, danger false negatives 58.6%) | the repairs-plus-v4 engine (sampled book, capture evidence with persistence, Astra's repairs) with the v5 model. Lane S vs the v14 bytes; lane T vs the v4 archive on the identical engine | built 01:59 UTC; **upload only if its lanes beat v14** |
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
| 2026-10-07 21:40 | **Head-to-head at real clocks, Fable arena-v12 bytes vs Astra arena-v11 bytes: 9W–0D–7L over 16 games, paired score 0.562, bootstrap 95% 0.375–0.750** (as White 6/8, as Black 3/8). Consistent with a modest edge for v12; not significant. |
| 2026-10-08 02:40 | Lane R (repairs+v4, sampled book) vs the v14 bytes: 4.5/8 (paired 0.562, 0.188–0.875). Union of lanes P, Q and R: 9–5–10 over 24, paired 0.479 (0.312–0.646), White 8/12, Black 4/12: **the v4 model does not beat the v1 model at real clocks; not promoted** (v5 decided by lanes S and T). Two-phase clock schedule implemented (`85169e1`); candidate `ada110c059ae` = v14 bytes + sampled book + two-phase clock; smoke U vs v14 queued on cores 6–7. v13 at 46–6–53. |
| 2026-10-08 01:48 | Capture+v4 (deterministic book) vs v14 bytes: 5–4–7 over 16, paired 0.438 (0.250–0.594), White 5/8, Black 2/8, all on one opening line. Not promoted. Lane R (sampled book, repairs+v4) and lane S (repairs+v5, unweighted) decide the model question. v13 at 37–4–32. |
| 2026-10-08 01:00 | Astra's history-current-r2 patch merged (mode 0 identical on 634 fatal plies; modes 1–2 off); repairs-plus-v4 archive `ffc023e42479` built; lane R queued behind lane P. v13 at 25–2–21 after 48 games (0–12 vs the 1900+ group, 5–3 vs TA-P). |
| 2026-10-08 00:35 | Model v4 (features-v2) trained and exported: policy 35.5%, danger false negatives 59.6%, value loss 0.78; archive `1bf9c8d29f86` with capture evidence + persistence; lanes P/Q vs the v14 bytes started. v3 recorded as not shipping. |
| 2026-10-08 00:28 | v3-model candidate vs v13: 3.5/8 in lane M (0.438), two draws in lane L before it was stopped; the v3 model is not an improvement at real clocks and does not ship. v4 (features-v2) is judged next on the capture-plus-v4 archive vs the v14 bytes (lanes P/Q). v13 at 20–1–14. |
| 2026-10-07 23:58 | **v14 cleared**: the reserve-10 caution bytes (`93f4ccdf03d5`) smoke 2.5/4 vs v13 with a 14 s clock floor; recommended upload. v13 at 13–1–10 after 24 arena games. Capture evidence (Astra's A1) ported into root (`c77f5db`), arms running; v4 (features-v2) training. |
| 2026-10-07 23:28 | **Caution package vs v13 at real clocks: 12–1–3 over 16, paired 0.781 (0.562–0.938).** The reserve-10 rebuild of the same engine is the v14 candidate; its smoke vs v13 runs now. (Astra flagged possible CPU contention from unpinned browser runs at 22:11–22:13 UTC during lane K's early games.) |
| 2026-10-07 23:16 | Caution archive vs v13 bytes at real clocks: lane K 5.5/8, lane J 5/6 with one pair left. Its lowest clock was 11 s, so the v14 bytes get the 10 s reserve (`93f4ccdf03d5`), smoke queued. v13 arena spell so far 2–1–3. |
| 2026-10-07 22:41 | **v13 activated** (API confirms at 22:39 UTC). v10 ended its spell at 72W–2D–67L. |
| 2026-10-07 22:40 | Model v3 trained (4,707 games): on the same test split policy 34.5% vs 32.7%, danger false negatives 64.7% vs 87.5%; archive `519260f77245` built on the caution engine + 10 s reserve; lanes vs v13 queued. GPU released. |
| 2026-10-07 22:35 | **Arena v13 = the full candidate** (`39fb4480e0b7`: two-ply + 7 s cap + both cores), file renamed `iamavirus-v13-hybrid.zip`; gate 10–1–5 vs the two-ply build. v10 active at 71–2–67 until the user switches. Caution lanes (caution archive vs v13 bytes) and the v3 model gate continue. |
| 2026-10-07 22:15 | **Full candidate (clock + both cores) vs two-ply at real clocks: 10–1–5 over 16, paired 0.656 (0.406–0.875).** The first real-clock gain of the night; the two-ply build is itself even with arena v12. Caution lanes (J/K) vs the full candidate running. |
| 2026-10-07 21:22 | User reactivated **v10** (rank 8 on the leaderboard) as the rating slipped. Arena v12 (Fable) ended its spell 7W–1D–8L over 16 games; arena v11 (Astra) 0W–0D–2L. Queen analysis: v10 lost the queen for less in 55 of 69 games, 48 to an unseen capturer; `surface_charge` under test. |
| 2026-10-07 21:05 | Two-ply vs plain (arena v12) at real clocks complete: 7–2–7 over 16 games, paired 0.500 (0.281–0.750). The term stays in the full candidate (offline gain, no real-clock cost). |
| 2026-10-07 21:00 | Full candidate repacked (`39fb4480e0b7`) after the suite with its defaults passed (609 checks). Two-ply vs plain at real clocks: 7/14 so far (lane D 3.5/8, lane E 3.5/6). Head-to-head Fable v12 vs Astra v11 archive: first pair 1–1 (an earlier note here said 2–0; misread). Arena: v12 active. |
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
