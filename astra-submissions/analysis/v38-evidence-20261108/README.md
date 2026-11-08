# V38: what the evidence supports

This is a review of completed development evidence, not a new experiment or
a change to the frozen Misty gate. The candidate retains v37's belief model,
guards, search algorithm, root selection and history data. It changes the
external Stockfish 19 depth-1 MultiPV scorer to score all children in one
full-window root pass. This is faster but approximate: some leaf scores change.

## The speed reaches the solver

The earlier cost profile attributed 82.194% of search wall time to Stockfish
calls. The packaged scorer is 1.57–1.68x faster on the frozen panels. In a
fixed-work serial model, that predicts about 1.42–1.50x whole-search throughput:

`speedup = 1 / ((1 - 0.82194) + 0.82194 / scorer_speedup)`.

That is a cost model, not an Elo estimate, and actual trees change. The 51
paired decisions use the same belief, legal-action mask, sampled worlds and
2.5-second search budget, with fresh scorer workers for each arm. Their median
node ratio is **1.38365**, solver-iteration ratio **1.38372**, and elapsed-time
ratio **1.00025**. The gain reaches regret updates and tree exploration.

Fifteen decisions change. The immediate-loss diagnostic is unchanged on
**exactly the same 12 cases**: zero fixed and zero newly broken. Among the
39 cases with an assessed material probe in both arms, one two-point loss is
fixed and none introduced (`zhjr2fp8`, ply 49, `f7g7` → `f7g6`). Material probes
are unassessed on the 12 fatal cases; missing labels are not treated as safe.

## What happened in the 16-game pilot

The audited 180+2 pilot is 11W–1D–4L against exact v37. Every candidate win
ends with the opponent's king exposed to an attacker whose square was hidden
in that opponent's observation immediately before its losing move. Eight end
with a king move into attack (two are captures); two expose the king by moving
another piece; one leaves an existing attack unanswered. Four of the eleven
are already unavoidable on the true board by the opponent's final decision.

This describes how the games ended. It does **not** prove the scorer learned
traps or that extra nodes caused the win rate; the evaluator approximation
also changes. Four color-pairs favor the candidate and four tie. Sixteen
games remain a small development sample.

The candidate's four losses are instructive:

| Pilot game | Final move | What happened | Safe responses on the true board |
|---|---|---|---:|
| p0, candidate Black | `g8f8` | King returns to a file attacked by an unseen queen on f6 | 15 |
| p1, candidate White | `h2h4` | King on g2 remains attacked by an unseen rook on a2 | 5 |
| p2, candidate White | `a2a3` | Visible rook h1 attacks king h2; the final position is already forced | 0 |
| p6, candidate Black | `g8f8` | King stays on the rank attacked by an unseen queen on e8 | 1 (`g8h7`) |

The two Black losses involve king movement between nearby squares while a
hidden queen changes or retains its attacking line. This is a composable
pattern worth retaining in the regression corpus. The visible-rook loss must
be studied earlier than the last move; calling that last move a missed escape
would be wrong. True-board safe replies are offline labels, not information
the bot was given. None of these observations changes this candidate.

## Release decision and measurement limits

The exact portable ZIP has passed compatibility checks. The separate matched
Misty comparison and Fable's independent ZIP review remain pending. Preserve
its original pass/fail threshold and all first attempts.

The Misty requirement is a **positive margin**: candidate score at least 8/16
and at least two points above v37. It is not a statistical non-inferiority
test. For example, if v37 scores 15/16, even a perfect candidate cannot pass.
That ceiling is a limitation of the chosen test, not a reason to silently
change it. A failed gate would block automatic promotion under the current
plan; it would not by itself prove the candidate weaker in the arena. Any
different release decision would need an explicit, evidence-based review,
with the failed result still visible.

Inputs, hashes, terminal moves, attacker visibility and safe-response lists
are in `evidence.json`; `evidence-v0.json` retains the first description before
adding the forced-loss check. The unmodified course referee reconstructs the
terminal positions. Source: `experiments/v38-evidence-20261108/analyze.py`.
