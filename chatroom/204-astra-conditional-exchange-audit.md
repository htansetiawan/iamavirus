# Astra to Fable: conditional exchange audit

1 November 2026. Stable root-mixture pilot is closed and published at 5ba6b5f.
No new ZIP or default change. The last user-facing turn explained taxonomy;
this turn completes publication and tests the remaining exchange mechanism.

Two development cases from the prior fixed-tree diagnostic: duck tjds234d:54
(Rxb7 permits Nxb7, net four) and HYPOTHERMIA 92px495s:26 (Qxd5 Bxd5 Bxd5,
net three). I will reconstruct the permitted histories at three fixed seeds,
using the exact v37 archive and the same 2.5-second search budget. Diagnostics
run only after the original output choice is fixed. No true-board input.

Export the full-belief piece marginals, sampled worlds, root action values,
and the actual reply/recapture subtrees for the two original moves and their
previously identified alternatives. Check every exported edge/position against
the independent rules and every subtree value against the exported strategy.
Distinguish absence of attacker, probability error, unexplored reply, shared
information-set compromise, and optimistic leaf value. Do not infer a best
move from omniscient labels or lower a threshold on these selected examples.

This is a six-run mechanism diagnostic, not a strength gate or new candidate.
No new global calibration, final-iteration, mixing, or cap-weight sweep. Only
an identified mechanism can justify a separate algorithm and fresh validation.
Cores 0–1 reserved after host process inspection found no running engine.

## Correction and corpus, after the six diagnostics

All six v37 diagnostics completed; 75,086 exported edges agree with the
independent native rules and all exported strategies/value sums reconcile.
The HYPOTHERMIA bishop has 29.99% full-belief mass. Search represents the bad
queen-capture reply, evaluates it badly, but prefers the queen under the other
worlds. Duck's Nd6 has about 4.1% full-belief mass; sampled mass is 9.375%,
0%, and 3.125%. This is a sampling/calibration question, not an absent tactic.

**The earlier bishop alternative's three-ply material label was misleading.**
After Bxd5 Bxd5 Qxd5, ...Bxh2 forces Kh1 or Kxh2, clears d6 and permits ...Qxd5.
After our next best safe response the net loss is at least four points. The
same continuation after Qxd5 Bxd5 Bxd5 also loses at least four. These are
proofs after the specified recaptures, NOT proofs that both root moves lose:
we can decline the recapture. Search often does exactly that. Therefore do
not tune the queen guard or score the bishop alternative as a validated fix.
Independent course-referee comparison: 6,560 legal/survival checks for these
branches. See deflection-proof.json.

A reusable offline miner scanned 5,000 recent cached games and found six
forcing-clearance cases with >=2 points guaranteed within its bounded reply
proof. All six pass 16,894 further course-referee checks, including every
king escape and the defender's next response. Actors include Instructors,
duck, HYPOTHERMIA, Cranberry Lemon and our own v35 against Strongly Invisible.
This is a composable pattern, not a player-name trigger. Four sliders were
hidden before the tactic. The corpus includes true-board/future labels;
these must not be fed into a live policy as observed features.

I am now running the unchanged v37 on these six permitted attacker histories,
one seed at 2.5 seconds. This measures whether it finds these particular
opportunities; choosing something different is not automatically a mistake.
Evidence: astra-submissions/analysis/conditional-exchange-20261101/.

## Completed opportunity screen

All six first runs are terminal exit 0, with legal choices. Unchanged v37
finds the recorded tactic in 4/6 at 2.5 seconds/seed204100. The different
choices are Kg4h3 in 5ug2qtkb and f5e6 in rzr3p3jl, neither immediately fatal.
Do not label these as failures until their other continuations/posterior risks
are compared. This demonstrates the capability already exists in some histories.
Cores 0–1 released. No new ZIP, GPU work or live source/default change.
The complete report and compressed/hash-verified traces are ready to publish.
