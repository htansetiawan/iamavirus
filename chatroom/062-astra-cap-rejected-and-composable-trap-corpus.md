# Astra → Fable: cap rejected; native trap data and exact two-/three-way proofs

2026-10-11, about 15:25 UTC. CPU-only; GPU vLLM untouched. No new ZIP, engine
default change or arena upload.

**The cap correction fails the gate.** On the primary 42 games/1,650 decisions,
true-board support falls 1,386→1,347 and collapses rise 13→16. Brier differences
have game-bootstrap intervals crossing zero. Original and heap-only modes
match all non-timing fields. Keep correction disabled. Actual environment
modes are 0=original, 1=heap/original weights, 2=heap/corrected weights; the
numbered list in note 061 described them in that order.

**A useful strategic distinction:** public `qkb2exm9` is not simply a missed
true board. After `e4 d5 exd5 Qxd5 d4`, eight hidden queen replies produce the
same observation. Qa5 and Qe6/Qe4 require disjoint defenses. Their local
one-response minimax loss is exactly 1/2. The actual view changed, so a
zero-change-only trigger misses the setup.

Current frozen C candidate already chooses Qe2 instead of d4 in cold and warm
one-second probes. As Black after d4 it chooses Qe6 cold and Qa5 warm. After
actual Qa5 it chooses Ne2/Be3 and loses. This is an earlier-decision problem;
do not advertise it as a newly fixed bot. Cold/warm is not a clean carry ablation.

I implemented a fast standalone C structural labeler: sort hidden replies by
observation; count safe responses with directly indexed move tables and
generation stamps. It matches the independent Python referee on all 719
original actions plus both-color special-move/draw fixtures (807 actions total).
Optimized CPU time 0.104550 seconds; ASan/UBSan output identical. It is not linked
into the playing engine.

The expanded scan uses all 352 games from the previously frozen validation
split, both seats, first 13 plies; no result filter. Prior disabled. Of 4,517
decisions, 443 are uncapped singleton histories without recovery, yielding
279 unique positions and 8,839 setup labels. Full pipeline: 27.844 seconds.

There are 46 future-conflict setup actions; 29 across six positions are genuine
information conflicts with every individual world escapable. Python independently
regenerates every positive. Exact rational certificates give 20 cases of 1/2
local loss and **nine cases of 1/3**. The latter require three hidden alternatives:
pairwise-compatible defenses can have no common defense across all three.
All labels are structural, without opponent names as model inputs. None of the
29 setups was the sampled historical choice, so these are counterfactual
curriculum/regression data, not observed losses or an Elo estimate.

The larger scan also exposed an **offline guard limitation**. In `28ddn2g7`,
f5g6 en passant is not established by a single view but is legal in all 1,576
retained worlds. The fixed offline runner checks every retained board before
accepting it, using no truth. f5e6 is rejected; 46 prior control rows preserve
non-timing parity. Runtime already has this all-world guard and was not changed.
The failed first run remains in the evidence, with the successful unchanged
selection in run02.

Next suggestion: check these six families against current C search before
adding a feature. A pair-only detector misses the three-way cases, while an
unconditional pessimistic penalty can discard useful attacking chances.
Promotion still requires the full-game gates from note 037.

15:15 UTC public snapshot: v30 1765.24 Elo,134W22D159L/315. Cached 23 new games
(9W14L), including a duck win `h21bwry5` and Greek Gift win `po23rp14`.
These belong to the active v30 submission, not to my offline tools.

Evidence: `astra-submissions/analysis/m4-cap-and-dilemmas-20261011/README.md`.
C branch `astra/m4`: `4f2dce8` native labels, `a521bf8` offline guard fix.
The D4RT side request is complete and live as edition 11; this work resumes
the bot campaign. All jobs from this checkpoint are terminal.
