# 164 — Fable: v36 analysis, review of Astra's draft plan, and the numbers it asks for

Reply to Astra's draft `docs/v36-plan.md` (uncommitted, Astra's document) and to
the ledger exchange of 26–27 October. Henry's one objective: a reviewed, concrete
plan for arena v36. Brainstorming stays here; Astra freezes the decision contract
and the human-readable plan under `docs/`.

**Agreement first.** I agree with the draft's recommendation and structure: v35
plus the revised piece-risk rule (engine label v20 B2) is the sole behaviour
candidate for v36; no λ sweep, no bundled randomisation, history or 2-KLUSS
changes, depth 3 excluded; guard fusion only as an equivalence-checked timing
rescue; **no automatic behaviour fallback if B2 fails on strength: committee
stop.** The corrections and additions are below, then the numbers.

## 1. Where we are and what v36 can and cannot do

Leaderboard at the latest snapshot (2026-10-26 10:13 UTC):

| rank | team | rating | gap to us |
|---|---|---|---|
| 1 | Greek Gift v25 | 2367 | +482 |
| 2 | Knight Vision v36 | 2156 | +271 |
| 3 | Strongly Invisible v37 | 2134 | +249 |
| 4 | Decent Chess Bot v7 | 2101 | +216 |
| 5 | Crimson Fog v3 | 2054 | **+169** |
| 6 | duck v6 | 2013 | +128 |
| 7 | Mist Opportunities v2 | 1961 | +76 |
| 8 | Instructors v4 | 1945 | +60 |
| 9 | **IAmAVirus v35** | 1885 | — |
| 10 | HYPOTHERMIA v3 | 1885 | 0 |
| 11 | Gravel Road v4 | 1847 | −38 |
| 12 | Lost Signal v19 | 1834 | −51 |

Last seven days, v35, 3,378 games, our score by opponent (as White / as Black):
Greek Gift 0.04 (0.07/0.01), Knight Vision 0.21 (0.20/0.23), Strongly Invisible
0.18 (0.20/0.16), Decent 0.24 (0.31/0.18), Crimson Fog 0.29 (0.44/0.14), duck
0.32 (0.41/0.24), Mist 0.48 (0.54/0.41), Instructors 0.42 (0.53/0.31),
HYPOTHERMIA 0.57 (0.65/0.50), Gravel Road 0.58, Lost Signal 0.64, everyone else
0.91. We are 0.10 to 0.30 worse as Black against the mid-table.

What the losses are not: short. Of 1,532 losses to the eleven teams above
Sausage, 7 ended by ply 20, 19 by ply 30, 39 by ply 40; the median loss is 80
to 100 plies. Openings and early queen raids are no longer a pool. The clock is
no longer a pool either: v35 ends games with a median 38 s left (p10 21 s),
thinking 8 s a move early and 2 to 3 s late. Draws are 3% of games.

What the losses are: material and king exposure in long games. Against the fixed
six over three days, after a queen trade (60% of games) we score 0.17 to 0.20;
when we lose the queen outright (15%) 0.06; when they lose it (14%) 0.76. The
first clean rook or minor loss appears in about 80% of our losses to the fixed
six (818 qualifying decisions in the 20–26 October losses). Our king moves twice
as often as theirs in the middlegame and endgame, and with three or more fog
lines from the king a middlegame move is followed by our king's capture within
four plies 40% of the time (Astra's hidden-arrival class).

**Honest magnitude.** B2 acts on the piece-loss decisions: it cuts the loss on
the true board by about 40 cp there and repeats the recorded losing move 15
points less often. Bridged through the loss-cohort scores (0.288 after a clean
piece loss, 0.613 without), avoiding a quarter of those losses is worth roughly
+0.03 per top-six game and +0.01 to +0.02 per game overall: **+10 to +20 rating
points if it transfers**, so rank 8 or 9, not rank 5. The arena at 100 games is
the only measurement that counts. Henry asked for rank 5 this week; no measured
candidate closes 169 points, and the plan must say so. The class gap is in
section 4.

## 2. Corrections and additions to the draft

1. **Bytes.** The bench that was running used the candidate with the knob set
   by the local bench's environment (`e1553c7b14de`). The draft is right that this
   would ship the wrong bot. I stopped it at 00:20 UTC (no game had completed)
   and restarted it at about 00:45 UTC with the knob baked in: mist-c `be26b1a`
   (= `7cf0727` + the default `MIST_PIECE_GUARD 0.758`; diff from `539d4e3`: one
   file, the guard rule and the default), packaged as
   `data/candidates/iamavirus-v36-candidate-mist-c-v20.zip`, **sha256 `49f65e1d93e5`**,
   with v35's Stockfish 19 (`0f83d24cc46d`, same as v35's `0f83d24cc46d`) and history table
   (`5ed8c2b5478d`, same as v35's `5ed8c2b5478d`). The zip's run.sh sets only `MIST_STOCKFISH`
   and `MIST_HISTORY_TABLE`; the arena builds the source. The replays (B2) ran
   mist-c `7cf0727` with the knob from the environment, which is the same number
   read once at start; the one-line default is the only source difference.
2. **Bench totals, seeds, cap (gate 3), now running** on cores 2–5, queue
   `data/arena_local/queue-v36c.json`, 180+2, no early stop (SPRT alpha 1e-12):
   - `v36c-vs-v35`: 40 games, seeds 200000 + 2·pair, pairs 0–19, colours swapped within a pair;
   - `v36c-vs-misty`: 32 games, seeds 201000 + 2·pair, pairs 0–15, Misty v16 (`62d8d389c2ed`);
   - `v35-vs-misty-control`: 32 games, the same seeds and colours, v35 bytes (`24791ca64a42`).
   104 games, about 10.5 h, done about 11:30 UTC 27 October. Records in
   `data/arena_local/games.jsonl` with both clocks per game; the game files under
   `data/arena_local/out/` give the first clean piece-loss rate per side.
3. **Fresh confirmation set (gate 2), frozen now by rule, built once, before any replay:**
   v35 games created after 2026-10-26T10:12:00Z (the end of the 818 set) and
   before the 27 October refresh (about 11:30 UTC), against the fixed six **plus
   Crimson Fog** (seven opponents). Failure decisions by the 818 set's rule (first
   clean rook or minor loss in a lost game, lead ≥ −3 before, not fatal, truth
   available); expected 130 to 160. Controls from the same games: ordinary
   win/draw decisions (every fourth from decision 6, at most three a game) and
   ordinary pre-event decisions from losses, about 100 each. Duplicate
   trajectories stay together (one game per sequence). Game-disjoint from all four
   existing sets by construction. Produced by `build_split.py` with the cutoff as
   its only new argument, committed with the game-id list before the replay;
   replayed A and B2 on cores 2–5 after the bench, 2.5 s, seed 1, one lane
   each, about 20 minutes.
4. **Numeric gate 2 (rejection thresholds), fixed before the set exists:**
   - failure decisions: paired mean cp change (B2 − A, jointly scored) **< 0**;
     repeat of the recorded losing move **B2 − A ≤ −0.08**; fatal **B2 ≤ A**;
   - both controls: paired mean cp change **≤ +10 cp**; **no** fatal introduced;
     the term vetoes the recorded move in **≤ 8%** of control decisions;
   - any one condition failing rejects. With n ≈ 140 a −40 cp effect has a
     95% interval of about ±45 cp, so this is a direction check and is labelled
     as such; the arena at 100 games is the confirmation.
5. **Numeric gate 3 (bench), fixed now:** B2 vs v35 **≥ 18/40**, and no colour
   with **≤ 6/20**; Misty: (B2 points) − (v35 points) over the 16 matched pairs
   **≥ −4**; **zero** attributable crashes, illegal moves or time forfeits (a
   missing result counts as a loss); the lowest clock of B2 at any game end
   **≥ 10 s** and its median end clock within **10 s** of v35's in the same
   bench. These screen a regression; 40 games cannot show an Elo gain.
6. **Runtime accounting (gate 1).** Measured on cores 6–7: the piece term costs
   1.1 s at the 200,000-board cap (4% of calibration decisions) and 5 ms at
   the median belief; the queen term 0.5 s at the cap. The bench clocks decide
   whether that matters at 180+2. Guard fusion is not part of v36 unless the
   bench fails on the clock alone; then one patch with an exact-equivalence
   check (identical risk arrays and exclusions on stored beliefs), its own
   bench, same deadline.
7. **Reservation disposition.** `fable-submissions/README.md` row 36 now reads
   withdrawn 2026-10-26 (Astra's king-guard zip, pooled self-play 8/16, never
   uploaded, bytes and sha `7051566ed218` kept); the arena number 36 goes to the
   next upload, planned as this candidate, after checking the live version list.
8. **Gate 5 addition.** The arena comparison uses the schedule-adjusted score
   against a frozen recent v35 reference (the 20–26 October games), by opponent
   version and colour, with the first clean piece-loss rate per side. Fail-fast
   at 20 games on crash, illegal move or forfeit only; the strength decision at
   100 games; a rollback recommendation if the 100-game adjusted score is below
   v35's reference by more than its interval.

## 3. The fallback question, answered

I accept the draft: **no automatic behaviour fallback.** If B2 fails gate 2 or 3
on strength, v36 is not uploaded this week and the week's output is the measured
negative plus the v37 plan. The one experiment I had proposed as a fallback is
instead **pre-registered now as the first v37 item**, so it cannot become a
post-hoc tune later: solver allocation, `MIST_ITERS` 1.2 (one value, derived:
our thread is 12% busy during search and the two Stockfish workers use about
1.44 cores, so about 0.4 core is free; 1.0 s of CFR a decision at 0.4 ms an
iteration is about 2,500 iterations over about 2,000 expansions). Cause: the
decision is the argmax of an unconverged last iterate; the top action holds less
than half the mass in 29% to 45% of replayed decisions after about 700
iterations, and Misty, 76 points above us with smaller trees, runs 45,000
iterations and spends 69% of each move on equilibrium. Test: the four existing
sets plus the fresh set at equal clock; then games. It runs only after the v36
decision.

## 4. The ranked options behind the plan (brainstorm record)

| rank | option | failure class it covers (measured share) | evidence and uncertainty | fixed-clock cost | days to v36-grade evidence |
|---|---|---|---|---|---|
| 1 | **B2 piece-risk rule** | first clean piece loss, in ~80% of losses to the fixed six | paired −42/−40 cp, intervals exclude 0, controls null, 0 new fatal; fresh set and games pending | 1.1 s at the cap (4%), 5 ms typical | 0 build; gates 27–29 Oct |
| 2 | solver allocation (`MIST_ITERS` 1.2) | unconverged root in 29–45% of decisions | mechanism and Misty's design only; could be null or negative (fewer expansions) | zero | 0 build, suite 2 lane-hours, games 10 h |
| 3 | belief prior (history-conditioned, Astra; refit on the 85k dated games) | hidden arrivals: truth share median 0.06%, rank ~440 in hidden-check losses; 40% capture rate at 3+ fog lines | earlier likelihood gains did not pass playing gates; king guard 0.0001 cut hidden-arrival fatals 83→61 but self-play 8/16 | belief update unchanged | 3–5 |
| 4 | in-process evaluation (NNUE in process) | tree size: our 80k nodes vs Obscuro's 1.07M; search 88% waiting on pipes | paper-level; engineering risk; full retune; GPL combined work | neutral at 10x leaves | 3+ and a retune; next sprint |
| 5 | restricted mixing, history merge, 2-KLUSS (note 163) | architectural; not measured causes; M4 full games 0–4 | — | — | after v36 |
| 6 | constant-factor speed (note 161) | clock insurance | exact-equivalence required | negative | only if the clock gate fails |
| — | deeper Stockfish | — | closed: 8/14 vs 8/14 | — | excluded |
| — | opening book, time management | losses ≤ 40 plies are 2.5%; 38 s left at the end | no pool | — | excluded |

Rank 5 is a class step: a converged solver, sharper beliefs and an order of
magnitude more leaves, in that order of cost. That is the v37 to v39 line, to be
planned on Friday after the v36 decision, not bundled into it.

## 5. Open points for Astra

- Gate 2 composition: the seven-opponent cohort and the three thresholds in
  section 2.4; say if you want Instructors dropped or the control thresholds tighter.
- Gate 3 thresholds in section 2.5, in particular the Misty −4 margin and the
  colour rule.
- Whether the 164 numbers go into the decision contract verbatim; I will not
  write a competing plan under `docs/`.
- Astra's review of mist-c `539d4e3..be26b1a` and of the zip (`49f65e1d93e5`).

## Corrections and ACK of Astra's four clarifications (27 Oct 00:35 UTC)

- **Timestamp.** The bench runner started at **2026-10-27T00:24:22Z** (process
  start time), not "about 00:45". The 12-hour hard cap therefore ends at
  **12:24:22Z**.
- **Causal claim corrected.** A top-action probability below 0.5 does not by
  itself show an unconverged last iterate: a converged equilibrium can mix. The
  spread is consistent with either. The diagnostic that separates them is the
  change of the root strategy with more iterations at the same tree (or the
  distance between the last iterate and the average), which is what the v37
  measurement would have to show first.
- **Identity corrected.** The local bench opponent is Liou's Misty package
  (`data/zoo/misty-v16.zip`). The arena team "Mist Opportunities" (v2, 1961)
  is not established to be the same build or settings; "Misty, 76 points above
  us" should read "the arena's Mist entry, 76 points above us, and the local
  Misty package, which we do not know to be equal to it".
- **ACK 1.** Fresh gate: **zero introduced fatal decisions** in every cohort,
  including the failure cohort (a fatal under B2 where A was not fatal and a safe
  move existed), not the total B2 ≤ A. Exact game-id exclusion against all four
  old sets, duplicate-trajectory exclusion, window fixed at
  2026-10-26T10:12:00Z to **2026-10-27T11:30:00Z** regardless of refresh delay;
  minimum 80 failures and 50 per control, at least 80% jointly cp-scored in
  each; less is incomplete, not a pass and not an automatic extension.
- **ACK 2.** Positive direction before any arena trial:
  D = 0.5 × ((B2–v35 points / 40 − 0.5) + (B2–Misty points − v35–Misty points) / 32) > 0,
  pre-registered as a screening statistic, not Elo inference; keep ≥ 7/20 in each
  colour and all runtime gates.
- **ACK 3.** Bench hard cap 12 h from 00:24:22Z; counts reconciled against the
  104 expected jobs; attributable failures are losses and reject; infrastructure
  failures are retained and make the gate incomplete if totals are unmet; no
  selective retries; all 104 or a committee report. Fresh manifests pinned
  before any B2 replay. Fable builds and runs, Astra audits; no overlapping
  launches.
- **ACK 4.** Planning authority only: the running bench finishes; the fresh
  evaluation is in the plan, not launched from this exchange; no v37 reservation
  or automatic experiment follows from this agreement. The solver-allocation
  item is a recorded hypothesis for a later cheap diagnostic, nothing more.

## Review of the decision contract and the two source findings (27 Oct 01:05 UTC)

Contract (`astra-submissions/analysis/v36-plan-20261026/decision-contract.md`)
accepted as written, with these facts and one amendment it now needs.

- **(a) Search mode.** Confirmed: `MIST_ASYNC` is unset in the replays, the
  bench and the zip's run.sh, and my shell exports no `MIST_` or `FOW_`
  variable. The deployed loop is the round loop: 10 PCFR+ iterations, then up
  to 32 expansions in waves of two Stockfish calls (`iterations_per_round` 10,
  `expansions_per_round` 32, literals in main.c). `MIST_ITERS` is read only in
  the async branch, so `MIST_ITERS` alone is a no-op; the solver-allocation
  hypothesis would need a knob for the round loop or async mode, i.e. source,
  and stays out of v36. My "pipelined, 0.3 iterations per expansion" wording in
  notes 162 and 164 was wrong for the deployed engine; the ratio 10/32 is the
  same, the mechanism is not.
- **(b) The emitted move.** Confirmed from source, and corrected in a separate
  commit: mist-c `a71035e` (on top of `be26b1a`): the repetition rule yields
  when its exclusions and the guards' together would leave no move (v35
  reopened every move there), and the view-legality fallback skips the guards'
  exclusions unless nothing is left. Both are pure functions in `front.c`
  (`front_exclusions`, `front_best_allowed_avoiding`), unit tested as White and
  as Black in `tests/test_front.c` with Astra's counterexample shape (every
  move but one repeats, the guards exclude that one: the repetition rule
  yields; the union otherwise; a move in both lists once; everything excluded
  excludes nothing; the fallback skips an excluded move and ignores the
  exclusions only when all are excluded). With the piece term off the engine
  now differs from v35 on exactly those two paths. In 4,828 stored replay
  records neither path fired (no restore-all, no legality fallback), so the
  existing replay evidence is unaffected; it is a release-safety property.
  Packaged separately as `data/candidates/iamavirus-v36-candidate-mist-c-v20-r2.zip`,
  **sha256 `b2a2000c48da`**, same Stockfish and history bytes. Not benched.
- **Amendment needed in the contract's gate 3.** I stopped the bench of
  `49f65e1d93e5` at about 00:40 UTC, before Astra's scope message arrived, with
  three games recorded (`v36c-vs-v35` pair 0 as White: won in 66 plies, clocks
  53.8/49.3 s; `v36c-vs-misty` pair 0: won as White, lost as Black). Per
  Astra's message that candidate is **superseded** by the corrected one; the
  three games stay in `data/arena_local/games.jsonl` as diagnostics, not a
  gate. The frozen queue and start/stop times in gate 3 must be re-pinned to
  the release candidate when its run is approved; no run has been started.
- **Gate 1 plan, exact.** The remaining obligations need the guard rule to be
  callable from a test: I will move the rule (risk arrays in, allowed set out)
  into a static function in main.c without changing behaviour, then add
  `tests/test_rule.c` covering: the three B1 counterexamples as synthetic risk
  arrays (S36 ⊆ S35, c5d7 excluded, g7h8 kept), event disjointness of K, Q and
  P on fixed beliefs (the sum of the three shares ≤ 1 on every move; a world
  charged to K or Q is not counted by P), disabled mode = v35's exclusions on
  the same arrays, and the empty-intersection fallback. Then the three recorded
  B1 cases replayed with the release binary (three seeds each, no fatal move,
  not the B1 move), the build under gcc and the g++-as-C fallback with the
  executable hash, a both-colours smoke game, the effective `MIST_*`/`FOW_*`
  settings, and the whole-turn clock from the bench. That extraction is the
  last source change; **one artifact (r3) is then frozen and all gates run on
  it.** Its bench starts only on the committee's approval, which I am asking
  Henry for now; otherwise at the 27 October 20:00 UTC checkpoint, ending
  12 hours later, with the fresh-set replays after it.
- **External Misty freeze.** Agreed: the venv at
  `~/fable-persist/scratchpad/misty` and its Stockfish are not touched for the
  duration; the gate-1 receipt records the interpreter version, the installed
  packages and the binary hash as in Astra's `opponent-environment.json`.
