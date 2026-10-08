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

## 7. Track record

| date | candidate | gym prediction | arena result |
| --- | --- | --- | --- |
| *(first entry at the next upload)* | | | |
