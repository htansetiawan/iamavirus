# Loss anatomy from the replays: Crimson Fog, and where our points go

30 October 2026. Method: every arena replay carries the true board and both players'
observations at every ply, plus the clocks. Replaying them with that log answers questions no
bench can: what the opponent saw, what it did, how long it thought, and where our games are
decided. Scripts here (`classify_losses.py`, the one-off passes are quoted in the chatroom
ledger) run over the compact store at `{storage}/iamavirus-data/derived/games-compact-20261029.jsonl.gz`
and the raw replays under `data/raw/games/`. Single decisions are re-run through the engine with
mist-c `tools/replay_arena.py` (the protocol input our side saw, our earlier moves forced, the
truth's share in the belief logged).

## Crimson Fog

Rank 4 at 2050 on 30 October (2,882 games), up from nothing on 24 October. Four versions, every
one at a 0.61 to 0.65 score; v4 since 26 October, 1,164 games, 0.631. A fixed-budget search
bot: 3.6 s per move at the median, 2.9 to 3.9 s between the 10th and 90th percentile, 3.7 s on
its first three moves, so no opening book. Repeats its reply to an identical history 40% of
the time (the least deterministic strong bot). As White 1.d4 (305 of 547), then e4, c3, c4;
as Black ...d5 against most things. Against us it is 52/76 under v4 and 115/168 against v35
overall, but the colours differ: **32-6 as White against our Black, 20-18 as Black**. Greek Gift
beats it 86.5/98; Knight Vision 73.5/110.

How it beats our Black (game `98ncgsz2`, 36 plies, replayed with both views): after 1.d4 c6
2.e4 Nf6 3.c3 d6 4.Bd3, it kept the light bishop on the b1-h7 diagonal, retreated it to c2
out of our sight at ply 31, brought the queen to e4 at ply 33 (we saw the queen), and played
Qxh7 at ply 35 with the unseen bishop covering h7. Our 34...Bd7-c6 ignored the battery; the
engine re-run on that decision (mist-c main, piece guard off, 2 seeds) plays 34...g6 both
times, with the true board at rank 1108 of 18,830 worlds in its belief (share 0.0002). The
belief did not hold the bishop on c2; the search still found g6 from the visible queen.

## Where v35's points go (7,198 arena games, score 0.520)

Black 0.477, White 0.562. Points below a half by opponent and colour, the worst first:

| opponent | as Black | as White |
|---|---|---|
| Strongly Invisible | 0.162 (263) | 0.291 (263) |
| Greek Gift | 0.051 (167) | 0.102 (167) |
| Decent Chess Bot | 0.219 (288) | 0.365 (288) |
| Knight Vision | 0.222 (254) | 0.258 (254) |
| duck | 0.258 (277) | 0.405 (278) |
| Instructors | 0.326 (278) | 0.5 |
| Crimson Fog | 0.155 (84) | 0.5 (84) |

## The final blow is a formality

All 3,362 v35 losses end by the rule: our move left the king capturable. The capturer was a
rook in 45% and a queen in 40% of them, unseen at our decision in 93%, its square unseen in
our last four decisions in 61%. But at that moment we were already down 5 or more points of
material in 81% of the losses (median 11), and 97% had been 3 or more down earlier, at a
median ply of 25 in games of median length 86. The king-capture pattern (back rank, open
files) is how lost games end, not why they are lost. An "exposure rule" for the king would
address the 12% of losses that were still level at the end.

## The games are decided before ply 30, and we are the ones who bleed

Material trajectory on 500-game samples per bot, each against its own arena opponents:

| bot (current version) | net material at ply 30, mean | down 3+ by ply 30 | up 3+ by ply 30 | score when level at 30 | score when down 3+ at 30 |
|---|---|---|---|---|---|
| IAmAVirus v35 | +0.14 | **17%** | 17% | 0.52 | 0.25 |
| Crimson Fog v4 | +0.62 | 10% | 19% | 0.62 | 0.33 |
| Decent Chess Bot v7 | +1.11 | 5% | 21% | 0.59 | 0.46 |
| Knight Vision v36 | +0.96 | 6% | 18% | 0.62 | 0.48 |
| Strongly Invisible v41 | +0.60 | 7% | 13% | 0.64 | 0.50 |
| Greek Gift v25 | +0.63 | 3% | 12% | 0.88 | 0.88 |
| Instructors v4 | +0.90 | 11% | 20% | 0.47 | 0.21 |
| duck v6 | +0.64 | 9% | 16% | 0.51 | 0.26 |

We fall 3+ behind by ply 30 two to three times as often as the top bots, and we win no more
often when ahead or level. The opponent mix differs by rating, which flatters the top bots a
little; it does not explain a 17% against 5 to 10%.

Why we bleed. In the first 30 plies we move a piece worth 3 or more onto a square attacked by
an enemy piece we cannot see **1.95 times a game**; the top bots 1.31 (KV) to 1.56 (SI, CF).
Risky captures alone: 1.22 a game against 0.71 to 0.98. The punishment rate is the same for
everyone (60 to 66% of such moves lose the piece next ply), so the opponents are not sharper
at punishing; we walk into the fog more often. Every bot's first 3+ loss happens at ply 17 to
22 and is half the time an exchange; ours comes earliest (ply 17) and is a clean loss 54% of
the time.

v23 (bitboards + fitted model) in the 122 local games against v35: risky moves 1.93 a game,
the same as v35's 1.93 in the same games; down 3+ by ply 30 19% against 15%. The fitted model
does not change this behaviour, which matches its 0.525.

## Opening choices, from our own record

Within one opponent line our reply varies by seed, so the record is a natural experiment:

| after | our move: score (games) | spread |
|---|---|---|
| 1.d4 Nf6 (White) | c3 0.671 (129), Qd2 0.623 (57), c4 0.613 (40), Nc3 0.564 (227), a4 0.552 (58) | +0.12 |
| 1.d4 Nc6 (White) | Qd2 0.700 (40), a4 0.575 (53), Nc3 0.523 (174), c3 0.469 (81) | +0.23 |
| 1.d4 c6 (White) | a4 0.500 (40), c3 0.432 (96), Qd2 0.418 (55), Nc3 0.396 (178) | +0.10 |
| 1.d4 c6 2.Nc3 d5 3.Bf4 (Black) | e6 0.411 (56), Nf6 0.285 (135), Bf5 0.270 (63) | +0.14 |
| 1.d4 (Black) | c6 0.348 (1399), Nc6 0.311 (616) | +0.04 |

Spreads of 0.10 to 0.23 on 40 to 230 games are one to two standard errors each and the
opponent mix within a line is not controlled; a book that follows the better-scoring branch
is a cheap, low-risk gain of perhaps 10 to 20 Elo, to be checked opponent-adjusted before use.

## What this means for 2000 this week

Current 1922 (rank 7); 2000 needs about +0.11 a game against the field, or less with the
rating's own ±40 swings. The measured gap is early material discipline, not the endgame and
not the king: 17% against 5 to 10% down by ply 30, driven by 30 to 50% more piece moves into
fog-attacked squares. The v20 piece guard aimed at this and lost in play because its risk
estimate came from the belief, which holds the unseen attacker at a tiny share; the belief
work of the last two days shows that share will not rise by modelling. So the input to the
guards has to come from elsewhere:

1. **Calibrate the belief's hazard against the record.** For every early piece move in our
   arena games, compute the belief's own probability that the destination is attacked from the
   fog (replayed with mist-c's trace tools) and compare with the truth (13% of our early piece
   moves land on fog-attacked squares, 1.95 a game). If the belief says 3% where the truth is
   13%, a calibration map on that estimate, not a new rule, is what the piece and queen guards
   need. Measurable offline in a day; the target metric is the risky-move rate and the
   down-3+-by-30 rate on held-out arena games, both computable without playing a game.
2. **An opening book from our record**, opponent-adjusted, for the first two to three moves.
3. **Track the two metrics daily on the arena replays** (risky moves a game, down 3+ by 30) as
   the proxy for any change; they move with hundreds of games where Elo needs thousands.
4. Arena trial of any change under the 20-game fail-fast rule; the local bench against our own
   bytes has now misled twice and cannot see a +40 Elo change.

Files: `classify_losses.py`, `v35-losses.json` (3,362 rows with the final blow, material at the end,
first 3+-behind ply), this file. Replay helper: mist-c `tools/replay_arena.py` (56d9614).

## Addendum (30 October, 16:30Z): matched opponents, compensation-conditioned

Astra's two cautions applied: (1) the bots are compared on games against the same six
opponents (Instructors, duck, Mist, HYPOTHERMIA, Gravel Road, Lost Signal), 400-game samples
each; (2) a fog-risky move counts as **uncompensated** only if our net material is down 2 or
more two plies later, so exchanges and sound sacrifices are separated out.

| bot | score vs these six | down 3+ by ply 30 | fog-risky piece moves a game (plies <= 30) | of which uncompensated | compensated or sound |
|---|---|---|---|---|---|
| IAmAVirus v35 | 0.489 | **14%** | 1.90 | **0.15** | 1.74 |
| Crimson Fog v4 | 0.711 | 8% | 1.49 | 0.05 | 1.44 |
| Decent Chess Bot v7 | 0.726 | 5% | 1.46 | 0.04 | 1.42 |
| Strongly Invisible v41 | 0.775 | 9% | 1.58 | 0.04 | 1.55 |
| Knight Vision v36 | 0.748 | 4% | 1.25 | 0.03 | 1.22 |
| Greek Gift v25 | 0.932 | 4% | 1.36 | 0.03 | 1.33 |

The conditioning sharpens the finding rather than dissolving it: the top bots move into the
fog nearly as often as we do, but theirs are exchanges or covered; ours lose material
uncompensated three to five times as often (0.15 a game against 0.03 to 0.05). That one event
class accounts for most of our 14% early-deficit rate against the same opponents. The
metrics apply to games a candidate actually plays (arena or proxy games), not to replays of
old games, as Astra noted; for diagnosis of v35 the historical record is the right data.

## Addendum 2 (30 October, 17:30Z): Astra is right about Black, and it is bigger than the sample

Astra found on 124 recent v35 games that our Black has better material at ply 30 than our
White yet scores lower. On 1,200-game samples per colour of v35 against the top nine
(Strongly Invisible, Greek Gift, Decent, Knight Vision, duck, Instructors, Crimson Fog, Mist,
HYPOTHERMIA):

| our colour | score | material at ply 30, mean | down 3+ at 30 | up 3+ at 30 | score when up 3+ | score when level | score when down 3+ | lost from ahead (>= +1 at 30) |
|---|---|---|---|---|---|---|---|---|
| White | 0.415 | -0.68 | 19% | 7% | 0.807 (83) | 0.410 (887) | 0.291 (230) | 6% of games |
| Black | 0.275 | -0.36 | 14% | 11% | **0.449** (127) | 0.283 (904) | 0.107 (169) | **15% of games** |

As White we convert a three-point lead at ply 30 into a win four times in five. As Black we
lose more than half of those games, and we lose from ahead in 15% of all games against these
opponents (median length 84 plies, down 11 points by the end, the king finishing on h8, h7,
g8, g7 or h6). Early material explains the White side's deficit (19% down by ply 30) and only
part of Black's; Black's problem is a collapse from ahead over the middlegame, which the
final-blow squares say is a king hunt on the kingside. In our own self-play the colour gap is
small (White 0.53 to 0.57 over the last 222 local games), so this is specific to how the
strong bots play White against our Black, not a colour bug in the engine.

Two mechanisms, two fixes: the hazard-calibrated guards for the early bleed (both colours,
White especially), and for Black a consolidation problem when ahead that no guard addresses:
the search has no notion of simplifying or keeping the king out of fog lines when it is
winning. Next measurement: in the 179 Black losses from ahead, the ply at which the lead was
lost and what took it (a replay pass), before any design.

## Addendum 3 (30 October, 22:30Z): Addendum 2 corrected

The Black-conversion gap in Addendum 2 was an artifact of measuring the lead at frame 30, where
Black has just moved and a capture is often about to be recaptured; White's frame-30 lead is
measured after the opponent's reply. On a stable lead (net >= +3 at frames 30, 31 and 32)
Black converts 0.780 (41 games) and White 0.829 (76 games), and Black loses from a stable lead
in 0.6% of games against White's 1.0%. Black's deficit is reaching the lead half as often,
which is the early-material bleed, not a collapse from ahead. The kingside king squares at the
end are how lost games finish, as Section "The final blow" says. Full lane in
`fable-submissions/analysis/black-conversion-20261030/result.md`.
