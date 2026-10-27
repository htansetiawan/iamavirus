# 168 — Fable: the capture helpers were blind to the king; corrected in mist-c dd89907, outside r3

27 October 2026, 06:50 UTC. Answers Henry's question (why r3 loses more than
v35 against Misty, bug?) and Astra's note 167 and ledger requests. The r3
candidate, its zip (5cdbb9caf8a3) and the running queue stay frozen.

## What I verified in the source

Astra's finding is right. `best_capture_net` in `src/main.c` makes each enemy
capture of our rook, bishop or knight and prices it as material, without
asking `mover_left_king_capturable` afterwards. A king taking a defended piece,
or a pinned piece taking, leaves the enemy king to be taken on the next ply:
the referee ends the game in our favour, yet the helper charged the piece.
`queen_risks` (v14, in v35) and `material_risk` (off by default) had the same
accounting. On the bench board (v36r3-vs-misty pair 0 as White, decision 28)
Rb1-d1 defends the rook d7 whose only attacker is the king e8; the piece term
put Rd1 at risk 1.0 and vetoed it, and the engine played Rxb7.

Two mechanisms Astra asked me to check:

- **Guard time and search budget.** The guards run after the budget is
  computed and before the search, so their time adds to the decision's clock
  and never shortens the search (as in v35 for the king and queen guards).
  r3's end clocks as Black against v35 are 0 to 14 s below v35's as White
  (lowest 19.7 s, above the 10 s threshold); nodes per decision are level with
  v35's at the same phase (Astra's counts). No throughput collapse.
- **Hard exclusions and sacrifices.** The rule leaves out every move whose
  combined risk is more than 0.02 above the least among v35's survivors; with
  λ 0.758 that is a piece risk 0.026 above the least. It is a one-ply material
  veto: a move that hangs a rook or minor for three or more net on a few
  percent of P is out whatever it gains two plies later. That is B2 as
  designed and calibrated (controls: 5% false veto of recorded moves). The
  bench says the control evidence did not transfer to self-play as Black (1
  of 12 against v35 at the 72-game snapshot). How much of that is the defect
  and how much the one-ply blindness is still open; the corrected build's
  paired replays on the four sets answer the first part, a bench the rest.

## The correction (mist-c `dd89907`, not in r3)

One predicate, applied in all three capture helpers: after making the enemy's
hypothetical capture, skip it when `mover_left_king_capturable` says we could
take the king. Shared semantics, so the queen's world is the same event for
`queen_risks` and for the piece term's exclusion. This is a change of the
capture-event semantics, including v35's queen term, not a piece-only fix.

Why not the piece helper alone: Astra's corner. Our defended queen arriving
next to the king, with a knight standing where the king can take it safely,
gives queen 1 (Kxd7 under the old queen helper) plus piece 1 (Kxf8 under the
new one) on a single world. Fixed together it is queen 0, piece 1.

Fixtures in `tests/test_rule.c` (`terminal_tests`, both colours, in `make
test`): the bench board (Rd1 1.0 → 0, Rc1 stays 1.0 because the rook is then
undefended, Rxb7 0; v35's rule keeps Rd1 and the piece rule now keeps it too);
a pinned knight taking an undefended bishop (0) against the free knight (1.0);
the pinned knight taking the queen is no queen's world, so a rook hanging
elsewhere is the piece term's event (queen 0, piece 1); Astra's double-count
corner (queen 0, piece 1, one event on the world) against the undefended
queen (queen 1). All four terminal checks failed on the unfixed helper in both
colours with the controls passing; all pass after the fix. Three existing
risk worlds needed a pawn on g7 or h7: our queen or rook already attacked the
king there, which made every enemy capture suicidal under the new accounting.

`make test` was still running `test_belief` when this note was written; the
push of dd89907 follows its pass (a ledger line will say so).

## What it means for v36

- r3 is not promotable: a confirmed defect in its deployed rule, and gate 3
  cannot reach H ≥ 18/40 from 8.5/26 at 06:30 UTC. The bench runs to its end
  for the record (78 of 104 started, 0 failed); the fresh set is still built
  once after the 11:30 UTC refresh and r3's gate 2 runs on it as planned, so
  the contract closes with numbers.
- A corrected candidate is a new scope: v35's queen term changes too, so it
  is "v35 with terminal-aware capture events + the piece term", with its own
  bytes, gate 1, paired replays of A (piece term off, which is v35 with the
  corrected queen term) and B on the four frozen sets plus the 11:30 set as
  development evidence, and its own bench; r3's games are not pooled with it.
  Its fresh gate needs a later window. Astra's item 4 (posterior effects,
  compensation after the fix) is part of those replays.
- Belief versus guard: all seven Misty losses end with a hidden attacker and
  r3 already behind (Astra). The guard's share of that is what the paired
  replays measure; the belief's share is the history-merge audit from note
  163, unchanged in rank.

No new lane starts before the bench cores are free and the plan is agreed at
the 20:00 UTC checkpoint.
