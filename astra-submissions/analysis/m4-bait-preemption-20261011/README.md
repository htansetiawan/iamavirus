# King preemption versus the protected queen fork

This offline audit takes a useful step backward from the fatal move in public
game **4bkwxxng**: Instructors v4 (White) versus IAmAVirus v30 (Black). It
replays the game with the course Fog of War referee and tests one
counterfactual king move at the earlier decision. It is a tactical label for
this position, not an arena-strength result or an engine patch.

At ply 53, after White's Nd5 and before Black's `...Qg6`, the referee position
is:

```text
3r1k2/p4ppp/1p1n1q2/3N1b2/8/4Q3/PP3PBP/4R1K1 b - - 1 27
```

Black's queen on f6 and rook on d8 are visible to Black. White's queen on e3
and Black's king on f8 are both hidden in the opponent's current observation.
The hidden queen can later move to e7, where it attacks the f8 king and d8
rook together. This is a history and belief problem: a one-frame detector
cannot see the queen on e3 at the earlier decision.

The actual move `...Qg6` leaves this fork available. After `Qe7`, Black has 37
pseudo-legal replies; only `...Kg8` avoids immediate king capture on the next
ply. After `...Kg8 Qxd8`, only `...Ne8` avoids immediate loss. Then `Qxe8`
leaves 27 Black replies, all of which end in a White win under the referee's
king-capture rule. The arena bot instead played `...Kxe7`, which loses at once.

The earlier counterfactual `...Kg8` changes the same `Qe7` idea into an
ordinary queen exchange: Black can answer `...Qxe7`, and `Rxe7` leaves a
nonterminal position. After `Qe7` in that branch, 40 of 41 Black replies avoid
immediate loss. This does not prove that `...Kg8` wins or is best; it proves
that the observed forced queen trap was preventable one move earlier.

## Composable lesson

When the opponent's queen may be hidden, track whether it can reach a square
that attacks both the king and a major piece. If the king has a safe
preemptive square, compare it before making a quiet queen move or accepting a
protected capture. Treat this as a candidate motif with a belief condition,
not an unconditional “put the king on g8” rule. The game does not validate a
new generic king-safety bonus.

All counts are exact one-ply survival checks over the enumerated true-board
move set. The certificate is retrospective full-information analysis of one
replay; it does not establish a common strategy over every board in the live
belief. “Avoids immediate loss” is narrower than “safe for the rest of the
game.”

## Reproduction

```sh
/home/henrytan/git/fow-starter/.venv/bin/python \
  astra-submissions/tools/m4_bait_preemption.py \
  --game /media/henrytan/seagate/iamavirus/astra/m4-support-loss-20261011/bait/game.json \
  --kit /media/henrytan/seagate/iamavirus/astra/m4-support-loss-20261011/bait/verified/kit \
  --out astra-submissions/analysis/m4-bait-preemption-20261011/proof.json
```

The compact JSON proof records every reply in the three critical positions,
observations at the start of the branch, legal-destination visibility, source
hashes, and the referee outcomes. The unchanged input replay and report are
also retained on the user-authorized Seagate drive at
`/media/henrytan/seagate/iamavirus/astra/m4-bait-preemption-20261011/`.
