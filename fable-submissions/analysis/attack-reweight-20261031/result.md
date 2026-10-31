# Re-weighting the belief toward fog-attack worlds: offline test, negative

31 October 2026. The one change proposed after the hazard calibration of 30 October was to
multiply every world's weight by exp(lambda x a(w)), a(w) being the number of our knights,
bishops, rooks and queens attacked in world w by an enemy piece standing on a square we cannot
see, before the search draws its 32 worlds. The test asked two things of it on the same 300 v35
games (12,174 decisions, 239,815 candidate piece moves): do the belief's fog-hazard estimates
become calibrated in the 1 to 30% range, and does the true board's weight rise on the 166
decisions that lost a piece to an unseen capturer. It does neither. Calibration is unchanged at
lambda <= 1 and worse above; the truth's share on the loss decisions stays flat and its share
over all decisions falls. The hook is not worth building and no games are warranted.

Tool: mist-c `tools/hazard_calib.c` with `MIST_ATTACK_BOOST=0.5,1,1.5,2,3` (main 3f5eb1d, sweep
commit dc9327a) and `tools/hazard_reweight.py`. Two counts were swept: `all` as defined
above and `und`, counting only attacked pieces no piece of ours defends. The boost multiplies
both the fitted weights exp(logw / 2) and the sharp weights exp(logw) the search samples by.
Every table in `tables.md`; raw rows (167 MB, 60 added columns and one line per decision) at
`{storage}/iamavirus-data/hazard/reweight/`.

## Baseline check

The lambda = 0 columns of the new run reproduce the 30 October file byte for byte in all
277,812 candidate, material and reply lines (the run was split over four cores by game; the
belief's random state is per game, so the split cannot change a row). The 30 October file has
one extra line, a reply label at ply 1 of game 0rx45aqa carrying the previous game's view,
because the tool did not reset its view flag at a game boundary; such lines can only occur at
plies 1 and 2 and are never read by the analysis. The flag is now reset. The headline numbers
reproduce exactly: played moves, attacked-and-undefended event, fitted weighting realised
4.1x / 2.5x / 1.8x / 1.1x the prediction in the 1-3%, 3-10%, 10-30% and 30%+ bins, sharp
7.5x / 4.2x / 2.2x / 1.0x, Brier 0.0258 and 0.0277, 166 loss decisions with a median truth
share of 0.0019.

## Calibration under the boost (played moves, destination attacked from the fog and undefended)

Realised rate divided by the mean prediction, per bin, and the Brier score. A calibrated bin
reads 1.0.

| boost | fitted 1-3% | 3-10% | 10-30% | 30%+ | Brier | sharp 1-3% | 3-10% | 10-30% | 30%+ | Brier |
|---|---|---|---|---|---|---|---|---|---|---|
| none | 4.1 | 2.5 | 1.8 | 1.1 | 0.0258 | 7.5 | 4.2 | 2.2 | 1.0 | 0.0277 |
| all, 0.5 | 3.3 | 2.4 | 1.7 | 1.1 | 0.0258 | 7.7 | 4.3 | 2.1 | 1.0 | 0.0278 |
| all, 1 | 3.8 | 2.2 | 1.8 | 1.1 | 0.0260 | 8.4 | 4.2 | 2.0 | 1.0 | 0.0278 |
| all, 1.5 | 3.7 | 2.5 | 1.7 | 1.1 | 0.0263 | 7.8 | 4.4 | 2.0 | 1.0 | 0.0280 |
| all, 2 | 4.2 | 2.5 | 1.7 | 1.1 | 0.0269 | 6.9 | 4.4 | 2.1 | 1.0 | 0.0283 |
| all, 3 | 4.4 | 3.0 | 1.6 | 1.1 | 0.0285 | 6.5 | 4.5 | 2.1 | 1.0 | 0.0293 |
| und, 0.5 | 4.0 | 2.4 | 1.8 | 1.1 | 0.0258 | 7.4 | 4.4 | 2.1 | 1.0 | 0.0278 |
| und, 1 | 4.0 | 2.3 | 1.8 | 1.1 | 0.0259 | 7.4 | 4.4 | 2.1 | 1.0 | 0.0278 |
| und, 2 | 4.2 | 2.5 | 1.8 | 1.1 | 0.0262 | 7.2 | 4.4 | 2.1 | 1.0 | 0.0280 |
| und, 3 | 4.4 | 2.7 | 1.7 | 1.1 | 0.0267 | 7.6 | 4.1 | 2.2 | 1.0 | 0.0285 |

No lambda brings the three low bins within 1.3x of calibrated; none moves them by more than
noise. The Brier score worsens monotonically from lambda 1. The same holds for the plain
attacked event, the clean-loss event, plies 1 to 30 and all candidates (`tables.md`).

## The true board's weight under the boost

Geometric mean of the truth's share of P (over the decisions where it is in P: 11,935 of
12,174; 163 of the 166 losses), the median, and the median rank (1 + worlds weighted above it).

| boost | all: share | median | rank | losses: share | median | rank |
|---|---|---|---|---|---|---|
| none | 0.00378 | 0.00832 | 15 | 0.00098 | 0.00191 | 46 |
| all, 0.5 | 0.00378 | 0.00819 | 15 | 0.00102 | 0.00191 | 47 |
| all, 1 | 0.00373 | 0.00799 | 15 | 0.00104 | 0.00194 | 47 |
| all, 1.5 | 0.00363 | 0.00772 | 15 | 0.00104 | 0.00179 | 54 |
| all, 2 | 0.00347 | 0.00715 | 15 | 0.00101 | 0.00124 | 58 |
| all, 3 | 0.00301 | 0.00591 | 16 | 0.00089 | 0.00093 | 73 |
| und, 1 | 0.00378 | 0.00832 | 15 | 0.00098 | 0.00191 | 47 |
| und, 2 | 0.00375 | 0.00818 | 15 | 0.00097 | 0.00158 | 51 |
| und, 3 | 0.00369 | 0.00792 | 15 | 0.00093 | 0.00153 | 57 |

The best case for the losses is +6% in geometric mean at lambda 1 (0.00098 to 0.00104) with
the median rank one place worse; the target was a material rise toward the 0.2 share the
sharpness curve needs. Over all decisions the share only falls.

## Why it cannot work: the loss worlds are not fog-attack worlds

a(w) is a property of the position before our move. On the true board a fog-attacked piece
exists in 2,142 of the 12,174 decisions (18%) and in 47 of the 166 loss decisions (28%). The
belief's expectation of a is close to the truth on average (0.177 against 0.194 over all
decisions; 0.229 against 0.325 on the losses). So the boost splits the decisions in two:

| decisions | truth has a fog-attacked piece | boost none | all, 1 | all, 2 | all, 3 |
|---|---|---|---|---|---|
| all (12,174) | yes, 2,142 | 0.00428 | 0.00582 | 0.00700 | 0.00756 |
| all | no, 10,032 | 0.00367 | 0.00339 | 0.00298 | 0.00247 |
| losses (166) | yes, 47 | 0.00086 | 0.00133 | 0.00182 | 0.00221 |
| losses | no, 119 | 0.00103 | 0.00094 | 0.00080 | 0.00062 |

Where the true board has an attacked piece the boost does what it should (the truth's share
up 2.6x at lambda 3 on those losses). But in 119 of the 166 losses the true board has none:
the capturer only comes to bear on the square our piece moves to, and in those decisions every
boosted world is a wrong world, so the truth loses weight (at lambda 1: share up in 38 losses,
down in 61, unchanged in 67). The two halves cancel. The 30 October under-confidence is a
per-move fact about the destination square after the move, not a per-state fact the draw can
be tilted toward; a state-level multiplier has nothing to grip.

## Reading

1. The proposed change fails its offline test on both criteria. No engine hook, no games.
2. The miss on the loss decisions is the placement of the hidden attacker, not the amount of
   hidden attack. A correction has to act on the worlds that attack a candidate's destination,
   which is the per-candidate hazard estimate the guards already use and whose one-exchange
   label cannot separate a loss from a trade (30 October). That closes the re-weighting route.
3. What remains on the belief side is making the opponent model put the pieces where they are
   (the discriminator line, parked, and opponent-specific models), or more worlds at the same
   weight, which raised coverage without weight in the 29 October measurements.
4. Had the test passed, the game version was one line: the same multiplier applied to the
   weights `belief_sample` draws from in `src/main.c`, before the 32-world draw, under an
   environment knob, then the 100-game protocol. It is recorded here so it is not rebuilt.

Files: `tables.md` (the full sweep, 184 lines), mist-c `tools/hazard_calib.c` (MIST_ATTACK_BOOST, main 3f5eb1d),
`tools/hazard_reweight.py`; raw rows `{storage}/iamavirus-data/hazard/reweight/reweight-300.tsv`
and the analysis `reweight-300.md` beside it; run 376 s wall on four cores (2 to 5, released).

## Follow-up: destination coverage

Same day, same 300 games, same tool (mist-c main 4c17ee3). Since the losses are about the
square our piece moves to, the feature was made about squares: `dest` = the number of distinct
destination squares of our legal moves (from the view, so the same set in every world) that an
unseen enemy piece attacks in world w; `cover` = the number of squares anywhere on the board
unseen enemy pieces attack; `destn` = dest divided by the number of destination squares. Boost
exp(lambda x a(w)), lambda 0.05 to 0.5 for the counts and 1 to 3 for destn. The lambda = 0
rows again match the 30 October file byte for byte (the diff is 148 stale-view reply labels
at plies 1 and 2 that the old tool emitted at game boundaries, never read).

The feature does separate the true board from the belief's mass on the losses: a(truth) is
above the belief's sharp expectation of a in 120 of the 166 loss decisions for dest (72%; 55%
of all decisions), 115 for cover (69%), 119 for destn (72%). Mean dest on the true board is
9.52 against an expected 8.62 on the losses (7.70 against 7.47 overall).

Played moves, destination attacked from the fog and undefended: realised over predicted per
bin, and the Brier score. The truth's share is the geometric mean over the decisions where it
is in P; rank = 1 + worlds weighted above it.

| boost | fitted 1-3% / 3-10% / 10-30% / 30%+ | Brier | sharp 1-3% / 3-10% / 10-30% / 30%+ | Brier | all: share, rank | losses: share, rank |
|---|---|---|---|---|---|---|
| none | 4.1 / 2.5 / 1.8 / 1.1 | 0.0258 | 7.5 / 4.2 / 2.2 / 1.0 | 0.0277 | 0.00378, 15 | 0.00098, 46 |
| dest 0.05 | 3.4 / 2.3 / 1.7 / 1.1 | 0.0255 | 7.6 / 4.0 / 2.1 / 1.0 | 0.0275 | 0.00381, 15 | 0.00102, 44 |
| dest 0.1 | 3.1 / 2.2 / 1.7 / 1.1 | 0.0253 | 7.7 / 4.0 / 2.1 / 1.0 | 0.0273 | 0.00383, 14 | 0.00106, 46 |
| dest 0.2 | 2.4 / 2.1 / 1.6 / 1.1 | 0.0249 | 7.9 / 3.7 / 2.0 / 1.0 | 0.0270 | 0.00383, 14 | 0.00113, 48 |
| dest 0.3 | 1.5 / 2.0 / 1.6 / 1.1 | 0.0248 | 7.7 / 3.5 / 1.9 / 1.0 | 0.0268 | 0.00377, 14 | 0.00118, 48 |
| dest 0.5 | 1.3 / 2.0 / 1.5 / 1.0 | 0.0253 | 8.6 / 3.3 / 1.8 / 1.0 | 0.0266 | 0.00348, 15 | 0.00121, 39 |
| cover 0.05 | 3.1 / 2.3 / 1.7 / 1.1 | 0.0256 | 6.8 / 4.2 / 2.0 / 1.0 | 0.0276 | 0.00382, 14 | 0.00103, 45 |
| cover 0.1 | 3.2 / 2.1 / 1.7 / 1.1 | 0.0254 | 6.8 / 4.1 / 2.0 / 1.0 | 0.0274 | 0.00383, 14 | 0.00107, 44 |
| cover 0.2 | 3.1 / 2.1 / 1.7 / 1.1 | 0.0252 | 5.8 / 4.3 / 1.9 / 1.0 | 0.0273 | 0.00372, 14 | 0.00113, 48 |
| cover 0.3 | 3.5 / 2.3 / 1.5 / 1.1 | 0.0253 | 7.1 / 4.1 / 1.8 / 1.0 | 0.0272 | 0.00349, 14 | 0.00113, 40 |
| cover 0.5 | 5.7 / 2.3 / 1.5 / 1.0 | 0.0263 | 4.9 / 4.1 / 1.7 / 1.0 | 0.0273 | 0.00277, 14 | 0.00102, 50 |
| destn 1 | 3.4 / 2.3 / 1.7 / 1.1 | 0.0255 | 7.6 / 4.1 / 2.0 / 1.0 | 0.0276 | 0.00380, 15 | 0.00102, 45 |
| destn 2 | 3.3 / 2.1 / 1.7 / 1.1 | 0.0253 | 8.0 / 4.1 / 2.0 / 1.0 | 0.0274 | 0.00381, 15 | 0.00106, 46 |
| destn 3 | 3.0 / 2.1 / 1.7 / 1.1 | 0.0252 | 7.9 / 4.1 / 1.9 / 1.0 | 0.0273 | 0.00380, 14 | 0.00109, 48 |

The split that explains the net: on the 120 losses where the truth is above the expected
dest, its share goes 0.00092 to 0.00141 at lambda 0.3 (0.00173 at 0.5, up in 112 of 120); on
the other 46 it goes 0.00116 to 0.00074 (0.00048 at 0.5). cover does the same with a worse
tail (lambda 0.5 costs 27% of the overall share); destn is dest diluted. The low bins at 1 to
3% hold 123 to 158 played moves, so the 1.3x to 1.5x readings there carry about 4 events each.
On all candidates dest 0.2 is calibrated under the fitted weighting (1.6 / 1.1 / 0.9 / 1.0)
and dest 0.3 to 0.5 overshoots the top bins (0.9 / 0.8); the played-move 30%+ bin stays at
1.0 to 1.1 throughout.

Verdict: the square feature is the right direction and behaves like a calibration under the
fitted weighting (dest 0.3 takes the 1-3% bin from 4.1x to 1.5x and the Brier from 0.0258 to
0.0248, and lifts the truth where it is above expectation), but the net on the loss decisions
is a 20% rise in a share that needs to rise 170-fold, and under the sharp weighting the search
draws by the low bins stay 3.5x to 8x off. It is not the single evidence-backed change for a
game lane; a dest term at lambda 0.2 is at most a free, mildly positive ingredient to carry
into a later candidate, recorded here so it is not re-derived.
