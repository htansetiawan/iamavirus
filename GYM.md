# The IAmAVirus gym and local arena — specification v1

*Written 2026-10-08 22:00 UTC at the user's direction: "spec out the world-class gym and sim locally first, build it, spend R&D time on it first — the best university before sending the kids to the real world." Owner: Fable. Status: approved direction, M1 in progress.*

## 0. Purpose and the one success criterion

The gym exists to answer, before any upload, three questions about a candidate: **will it score better in the arena than the current version, by how much, and why.** It is also where the bot learns: the same opponents, openings and exams feed training.

The gym is only worth trusting if it is **predictive**: its verdicts on versions we have already played in the arena must match their arena records. Every component below is judged by that, not by how plausible it looks.

## 1. What today taught us (measured, not assumed)

| lesson | evidence |
| --- | --- |
| Single-capability exams miss trade-offs | The strike bonus raised the strike exam from 41% to 55% and cost games (0.562 → 1.0 when removed, in local lanes) |
| A runner that differs from the referee can lie | Local runner: v16d 16–0 vs v15; official referee: 12–3–9 over 24 (odds of 16/16 at 0.56 ≈ 1e-4) |
| Small lanes cannot decide | 24 games: 95% interval ±0.17 in score; a 5-point edge needs ~400 games |
| Self-play misses what strong opponents punish | v10 → v13/v14 halved activity, TA Baseline P went 14–0–2 → 17–2–13, while our lanes said the change was fine |
| The rules are right | Our C++ rules vs the course referee: 0 mismatches in 19,994 views and legal-move sets over 300 random games |
| Information, not compute or model size, is the ceiling | Full information 80% vs 41% on strikes; 8× compute: no change; 8.5M–21.7M models: +1 point |

## 2. Requirements

- **R1 Fidelity.** Rules identical to the referee (met); protocol, clocks, process limits and packaging identical (archives exactly as uploaded, run by the course referee); anything that deviates (oracle views) must be calibrated against the referee.
- **R2 Predictive validity.** On the panel of past versions (v5, v10, v12, v13, v14, v15, then v16), the gym's predicted arena score per opponent class (top six, TA baselines, weaker bots) matches the arena record within the arena's own sampling error, and the gym ranks the versions in the arena's order (rank correlation ≥ 0.8).
- **R3 Throughput.** ≥ 700 real-clock games per day on this machine (8 cores, 4 games at a time), more with a validated fast time control and more machines.
- **R4 Statistical power.** Every candidate-vs-baseline decision uses colour-swapped pairs on a shared opening suite and a sequential test (SPRT) that stops when the answer is clear at 95% confidence; no verdicts from fewer than the test requires.
- **R5 Diagnostics.** For every candidate, automatically: taxonomy fingerprint in games, decision exams with capability flags *and* perfect-information regret, partial-oracle ablations on demand.
- **R6 Reproducibility.** Frozen opening suites and corpora with hashes, recorded seeds, binary and model hashes, every result in an append-only ledger with its full configuration.
- **R7 Training interface.** The zoo, openings and exams are callable from the learning code (self-play league, curricula built from exam positions).

## 3. Architecture

### 3.1 The local arena (simulator)

**What the arena actually does** (course README, "Runtime limits"): builds and games run in a gVisor sandbox; **2 physical cores / 4 hardware threads**, shared by both bots of a game; **the opponent is paused on your turn**; 4 GiB memory per bot; 64 processes; 768 MiB writable workspace and 128 MiB `/tmp` in RAM; 5-minute build; 15-second initialization before the clock starts; 10-second sandbox setup; OpenMP/OpenBLAS/MKL default to one thread. The referee's sandbox path holds a paused bot's observations (at most two) and delivers them at its turn, with the deadline counted from before their delivery.

**Fidelity check, 2026-10-08:** our lane tool (`learning/compare_archives.py`) runs `referee.py --trusted-local`, where the waiting bot is not paused and receives observations at once. A same-seed test of the v16d and v15 archives scored 5/8 with observations held and the waiting bot idle (the arena's behaviour) and 5/8 with immediate delivery, and the runner seeded like the lane tool reproduced the official lane at those seeds exactly (same openings, same 5/8). For our bots, which do no work between turns, the two protocols are equivalent and the lane tool is faithful. An earlier 16/16 from the runner did not replicate: the same binaries, settings and seeding (13 of 16 openings identical) scored 10/16 on the current runner, and every faithful setup agrees on about 0.6 for v16d vs v15 (official lane tool 0.562 over 24, current runner 0.625 over 32). The 16/16 stays unexplained; the runner has since changed (the side not to move is now frozen, sessions are separate), and machine load during runs was not controlled. **Rule: games run on dedicated cores; training, downloads and builds are pinned to other cores or wait.** The runner now pauses the side not to move with SIGSTOP, so it stays faithful for opponents that do compute between turns. This machine has 8 physical cores and no hyper-threading, so a local core pair has two hardware threads where the arena has four; per-move node counts in arena logs, when available, calibrate that difference.

- **Referee:** the course referee (`~/git/fow-starter/referee.py`, run locally, never vendored), in `--trusted-local` mode, for every game that decides anything. Our runner (`learning/ceiling_match.py`) only for what the referee cannot do — feeding a side the true board — and only after it reproduces referee results on identical pairings (calibration test, §4 V2).
- **Scheduler (`learning/arena_local.py`, M1):** a queue of matchups (candidate × opponent × target games), assigning core pairs, playing colour-swapped pairs from the opening suite, appending every game to `data/arena_local/games.jsonl`, and stopping a matchup by SPRT. Resumable; survives restarts.
- **Opening suite (M1):** 200 opening prefixes of 8–12 plies taken from real arena games (balanced across the strongest teams' openings and ours), each played once per colour per pairing, so paired games share positions and the deterministic-book problem cannot recur.
- **Time controls:** the arena control (180 s + 2 s) for decisions; a fast screening control (60 s + 1 s) only after its rankings are shown to match arena-control rankings on the panel.

### 3.2 The opponent zoo (the faculty)

- **Tier 0 — our own archives:** v5, v10, v12, v13, v14, v15 and every candidate, exact bytes.
- **Tier 1 — scripted styles:** random, greedy capturer, cautious king-safety, queen raider, fog router: cheap probes for specific weaknesses.
- **Tier 2 — replicas of real opponents:** a behaviour-cloned policy per arena team (the top six, the three TA baselines, Apricot Squad, baseline.py), trained on that team's games (700–1,300 each) with our network, played with a light search. A replica is admitted to the zoo only when (a) it predicts its team's held-out moves well, (b) its taxonomy fingerprint is close to the team's, and (c) **our past versions score against the replica what they scored against the real team in the arena** (§4 V4).
- **Tier 3 — exploiters (later):** agents trained against our current best to find its weaknesses before the arena does.

### 3.3 Exams (the assessments)

- **Decision exams at arena fidelity** (`learning/gym_replay.py`: the real bot binary, hybrid, packaged model, modeled clock): strike, route, giveaway, fatal (634), queen-loss (228), broad-top and broad-us (300 ordinary decisions each).
- **Scoring:** capability flags (strike found, giveaway, queen en prise, king lost) and **perfect-information regret** (`build/oracle_regret`: value of the best move minus value of the chosen move on the true board, node-limited search, fog off), so every trade-off is priced in one number; blunder rate = regret ≥ 300 cp.
- **Ablations:** partial oracles (reveal king / sliders / knights and pawns), candidate injection, compute and breadth sweeps.
- **Fingerprints:** the move taxonomy (`learning/move_taxonomy.py`) on every candidate's games, against the winner profile of note 015.

### 3.4 Rating model

Bradley–Terry ratings over all local games; anchored to the arena by the past versions; output: each candidate's predicted arena rating and predicted score per opponent class, with intervals. An upload is recommended only when the predicted gain over the current version is positive with ≥ 90% confidence.

### 3.5 Training hooks

The zoo and the opening suite drive self-play leagues; exam positions become curricula; the exams are the training metrics (no more generic policy accuracy, which never translated into strength).

### 3.6 Data (the real asset)

- **Mirror the arena.** The public listing holds 93,805 games (2026-10-08 22:25 UTC); we had 5,337. `learning.ingest --all` downloads them newest first at one request per second (the client's floor), validating every replay frame by frame against our rules; mismatches are quarantined, never patched. First 30,000 overnight, the rest the following day, then a daily incremental sync.
- **What the data feeds:** per-team replica training (each top team has thousands of games, not hundreds), the move taxonomy and fingerprints, the exam corpora (cut again from the larger pool), the opening suite, opponent-move models for the belief (level-2), and the rating model's priors.
- **Dataset v6 (04:11 UTC, 2026-10-09):** 25,070 validated games → 40,120 training episodes (20,060 games), 1,470,454 training decisions, five times dataset v4; game-disjoint validation (2,506 games) and test (2,504 games) splits; manifest `data/manifests/v6.json` (content `2b894fb16833`); feature cache 7.8 GB at `/media/henrytan/seagate/iamavirus/feature-cache/v6`, built in 6 minutes.
- **Versions matter:** listings carry each side's submission version, so replicas can be trained on a team's recent versions only, and our panel can be matched to the opponent versions it actually faced.

### 3.7 Training infrastructure on the GPU

- **Feature cache:** each position's input planes computed once and kept on the GPU (float16), so training is bound by the GPU rather than by Python feature building on a busy CPU (the replica run used 18% of the GPU).
- **Batched self-play:** many simulated games at once with networks evaluated in GPU batches, for reinforcement learning and for training zoo opponents. Evaluation games of our own bot stay on the CPU, two cores each, as in the arena.

### 3.8 Reinforcement learning, on a date (user asked "when is later", 2026-10-09 05:00 UTC)

Imitation copies what strong players show; RL can discover what they never show explicitly (going to look for a hidden king). Three prerequisites, from `reports/Deep RL for Fog of War chess.md`, then the run:

| when | step | done when |
| --- | --- | --- |
| Oct 9 — **done 05:00 UTC** | **True-board critic** (`learning/critic.py`, memo experiment 1, first step): a training-only value network that sees the true board | met: held-out MSE 0.608 vs 0.94 (always 0) on 183,856 positions; explained variance 0.355; winner of decisive games 76.8% (`checkpoints/critic-vs/best.pt`) |
| Oct 9–10 — **environment done 05:15 UTC** | **Batched simulator** (memo experiment 5): N games stepped in one C++ call (`batch_env.cc`, `learning/batch_env.py`), features from the bot's own C++ tracker, GPU batch inference | environment alone: **204,440 decisions/s** on one thread (rules + input planes, random play; Python simulator ≈ 800); planes identical to `features.py` (684 events, worst difference 0.0, `tools/batch_env_parity.py`); next: end-to-end with the network in the loop, target ≥ 2×10⁴ |
| Oct 10 | **First RL run:** PPO with the memo's regularisation (reverse-KL step control plus a KL pull to the imitation policy, MMD style) and the true-board critic; league = our past versions + the validated TA Baseline P replica + self-play snapshots | the gym grades every checkpoint: exams, then SPRT against v17 in hybrid mode |
| Oct 11 onward | scale with the simulator; target the belief side too (opponent-move model, scouting) | gym-predicted gain ≥ 90% before any upload |

The network never picks moves unaided in the arena (memo risk 5); an RL policy enters through the hybrid's candidate rows.

## 4. Validation plan (before the gym is trusted)

- **V1 Rules fidelity** — done: 0 mismatches in 19,994 checks.
- **V2 Runner fidelity** — identical pairings on the referee and on our runner must agree within their intervals; until they do, the runner is used for oracle experiments only. In progress: the v16d archives replayed through the runner.
- **V3 Past-version panel** — local round robin of v5, v10, v12, v13, v14, v15 against the zoo at the arena control; compare predicted with recorded arena scores per opponent class and the arena ranking.
- **V4 Replica validity** — per replica: held-out move accuracy, fingerprint distance, and our past versions' local scores against it vs their arena records against the real team.
- **V5 Prospective test** — before the next upload, write down the gym's prediction for it; after its first 50 arena games, compare. The gym's track record is kept in `GYM.md` §7.

## 5. Milestones

- **M1 (tonight):** scheduler with SPRT on the course referee; opening suite; runner calibration (V2); regret exams on all corpora for v15 and v16d.
- **M2 (day 2):** past-version panel and rating model; validity report V3.
- **M3 (days 2–3):** replicas of TA Baseline P/A/S, duck, Greek Gift, Knight Vision, Decent Chess Bot, Strongly Invisible, Instructors (GPU); validity V4.
- **M4:** iterate v16/v17 inside the gym; upload only on a ≥ 90% predicted gain; V5 on every upload.

## 6. Throughput and power

A real-clock game averages about 8 minutes (≈100 plies at ≈5 s per move); four at a time on 8 cores gives ≈30 games per hour, ≈700 per day. Detecting a 5-point score difference at 95% takes ≈400 games without pairing, fewer with paired openings and SPRT; screening at 60 s + 1 s roughly triples throughput once validated. More machines multiply all of this; the scheduler is written to add workers.

**Measured on the scheduler's SPRT** (`learning/arena_local.py`: H0 = +0 Elo, H1 = +35 Elo, α = β = 0.05, minimum 20 games, variance shrunk to 0.22 over 20 pseudo-games; 400 simulated runs per row, ~6% draws, capped at 1,000 games):

| true difference | accepts "A stronger" | median games | 90th percentile |
| --- | --- | --- | --- |
| −35 Elo | 0% | 157 | 295 |
| 0 Elo | 5.2% | 405 | 950 |
| +17 Elo | 33.5% | 635 | 1,000 |
| +35 Elo | 83.5% | 398 | 1,000 |
| +70 Elo | 100% | 165 | 326 |

At ≈30 real-clock games per hour on this machine, a +35 Elo question takes about 13 hours and a +70 Elo question about 5.5 hours. The levers, in order: a fast screening control validated against the arena control (×3), paired opening suites (lower variance), more machines (×n), and candidates with larger effects (the ceiling program's job).

## 7. Track record

| date | candidate | gym prediction | arena result |
| --- | --- | --- | --- |
| 2026-10-09 04:40 UTC (registered before upload) | **arena v17** = v16d, `iamavirus-v17-hybrid.zip` (`721cc7e9727f`): v15 + seen-gift charge on quiet moves + king sighting + 8,192 particles, 16 hypotheses, 16 rows | Head to head vs the v15 bytes 0.598 over 56 games on faithful setups (≈ +69 Elo in self-play); gym exams: strikes 55% vs 41%, giveaway repeats 21% vs 25%, king left capturable on our fatal positions 40% vs 43%. Self-play gains usually shrink against other opponents, so: **arena score rate over its first 50 games 0.47 (range 0.41–0.53) against v15's 0.431 over 570**; vs the TA baselines +0.05 over v15; vs the top six unchanged (near 0); vs Apricot Squad and baseline.py unchanged (near 1). TA Baseline P specifically: from the validated replica, result pending (v15 scored 0.635 against it). | *(pending)* |

## 8. Validation log

- **V1 rules fidelity (2026-10-08):** pass — 0 mismatches in 19,994 views and legal-move sets over 300 random games; and every ingested arena replay (11,000+) is replayed frame by frame by our rules before acceptance.
- **V2 runner fidelity (2026-10-08):** pass — at the official lane's seeds the runner reproduced the lane's openings and score (5/8 = 5/8); held vs immediate observations made no difference (5/8 each); an earlier 16/16 did not replicate (10/16).
- **V4 replica validity, TA Baseline P (network-only replica, 16 games per version):** style pass — captures 23.9 vs 25.5 per 100 moves, long strikes 5.4 vs 5.6, fog routes 14.8 vs 16.0, king threats 3.1 vs 3.1, unseen king threats 0.8 vs 1.0, giveaways 2.5 vs 3.4, walk-ins 4.2 vs 3.7, king moves 7.6 vs 10.7. Strength partial — our versions score v10 0.625, v13 0.438, v14 0.531, v15 0.531 against the replica vs 0.875, 0.594, 0.542, 0.577 against the real bot: v10 correctly on top, the replica about 0.1 stronger than the real bot, the rest of the order within the ±0.2 intervals of 16 games. **Extended to 48 games per version (02:45 UTC, 2026-10-09; ledger `data/arena_local/games.jsonl`): v10 0.677 ±0.13, v13 0.615 ±0.13, v14 0.562 ±0.14, v15 0.635 ±0.13 against the replica vs 0.875, 0.594, 0.542, 0.577 against the real bot; mean absolute error 0.07, rank correlation 0.8, v10 on top. TA Baseline P replica (network-only) admitted to the zoo.** TA Baseline A replica, network-only, 16 games per version: v10 0.750, v13 0.750, v14 0.500, v15 0.438 vs 0.433, 0.357, 0.375, 0.429 in the arena — far too weak; **not admitted**. Reading: TA Baseline P behaves like a policy (a network replica captures it), TA Baseline A like a search bot (a network alone cannot). Rule for the zoo: a replica plays the way its team does — network-only for policy-like teams, our search guided by the replica network (hybrid) for searching teams. Hybrid replicas of TA Baseline A, TA Baseline S, duck and Greek Gift are in calibration (`queue-v4-hybrid-replicas.json`). Held-out move prediction for all nine replicas: TA-A 57.8%, TA-P 56.4%, TA-S 41.3%, duck 40.9%, Decent 38.8%, Greek Gift 38.6%, Knight Vision 38.0%, Strongly Invisible 33.4%, Instructors 31.2% top-1 (general model: 48.2 / 46.8 / 36.6 / 39.6 / 36.5 / 37.3 / 36.2 / 32.6 / 29.9).
