# What Greek Gift does better, and what the replays cannot tell us

Astra, 2026-10-09. User-requested extension of the current-repository review.

**Greek Gift's observable advantage is strong king pressure combined with good
material discipline and conversion.** It does not lead every tactical category,
and public replays cannot reveal its private algorithm. The evidence supports
copying capabilities, not asserting it uses a particular neural model, search
depth or belief architecture.

## Comparison design

The live leaderboard read during this review put Greek Gift at **2190.96**,
Knight Vision at **2137.89**, duck at **1930.87**, Instructors at **1890.00**, and
us at **1620.68**. Our active arena v21 uses v20's identical archive bytes.

I compared **649 games** from the local validated replay collection, selecting
current versions: Greek Gift v16, Knight Vision v29, Decent Chess Bot v4,
Strongly Invisible v35, duck v5, Instructors v4, and IAmAVirus v20/v21.
The common opponents are TA A v5, S v3 and P v5. For each team, take the newest
up to 20 games in each opponent/color cell through the fixed completion cutoff
**2026-10-09 14:39:52 UTC**. Average per-game rates within each cell, then give
the six cells equal weight. This limits opponent and color mix effects.

There are 120 Greek Gift games and 58 of ours in that panel. It is a descriptive
sample, not a randomized experiment: dates, positions, game lengths and opening
mix still differ. Phase comparisons condition on games reaching that phase.
Rates of attacks describe opportunity as well as ability. The two-ply material
loss tag is a proxy, and includes deliberate sacrifices.

Reproducer: [`compare_team_skills.py`](../astra-submissions/tools/compare_team_skills.py).
Full version filters, game IDs, replay hashes, phase counts and summaries:
[`greek-gift-panel.json`](../astra-submissions/analysis/top-six-review-20261009/greek-gift-panel.json).
This is development analysis, not a new sealed test set.

## The categorical capability gap

All rates below are per 100 own moves, except average visible squares and lead
conversion. Lead conversion uses raw game counts, not the standardized rates.

| Capability | Greek Gift | Us | What this suggests we should learn |
|---|---:|---:|---|
| Create king threats | 5.00 | 2.43 | Turn board activity into pressure on plausible king locations |
| Create king threats from unseen attackers | 3.24 | 1.51 | Threaten while concealing the attacker, then continue after the escape |
| Use the queen in the enemy half | 4.52 | 1.33 | Find safe attacking routes; our queen is rarely an offensive asset |
| Long-range slider captures (distance at least 3) | 6.86 | 3.92 | Coordinate files/diagonals with hidden-piece tracking |
| Capture from an unseen origin | 13.62 | 10.15 | Concealment should produce successful captures, not just hidden pieces |
| Net material loss of 3+ over the short exchange window | 1.06 | 1.69 | Attack without routinely paying for it in material |
| Walk a major/minor piece into an unseen attack | 1.49 | 2.10 | Improve destination risk estimates before quiet moves |
| Average visible squares before deciding | 36.40 | 33.22 | Preserve useful active pieces and visibility as the game develops |
| Wins after a sustained 3-point material lead | **105 / 106** | **28 / 42** | Keep winning positions stable and finish the king hunt |

The main separation appears in the **middlegame**. In plies 30–69, Greek Gift
creates **9.47 king threats / 100 moves** versus our **1.92**; unseen threats
are **6.68 vs 0.96**. Opening visibility is almost identical: **37.14 vs 36.72**
squares. By the middlegame it is **37.30 vs 34.31**, and in games reaching the
late phase **32.93 vs 25.96**. That pattern is consistent with stronger activity
and piece preservation. It does not prove a separate scouting algorithm.

This changes the priority from simply surviving the opening to maintaining an
effective attack and information after the first exchanges. It also argues
against adding a generic aggression bonus: Fable already measured a strike
bonus that improved a tactical exam without earning a match win-rate gain.

## Does it have something the other leaders lack?

**Not a categorically unique tactic established by these data.** On the common
TA panel, Knight Vision has slightly more overall king threats (5.09 vs 5.00),
Strongly Invisible has more unseen threats (3.83 vs 3.24), and multiple leaders
have greater queen activity or visibility. The differences among the leaders
are subtler than our gap to them.

Direct encounters provide a better view of Greek Gift's particular strength.
These use all locally available games between the stated current versions
through the cutoff, not an arena census:

| Opponent | Greek Gift W–D–L | Score |
|---|---:|---:|
| duck v5 | 87–9–24 / 120 | 76.3% |
| Instructors v4 | 209–17–43 / 269 | 80.9% |
| Knight Vision v29 | 70–4–50 / 124 | 58.1% |
| Decent Chess Bot v4 | 35–2–25 / 62 | 58.1% |
| Strongly Invisible v35 | 25–3–11 / 39 | 67.9% |

The smaller margins over the closest rivals have substantial sampling
uncertainty. A current rating lead is not proof of superiority in every matchup.

### Against duck: prevent its ambushes while applying more king pressure

In the **same 120 games**, color-balanced per-game rates:

- Greek Gift creates **5.65 king threats vs duck's 2.49**, and **2.77 unseen
  threats vs 0.93**.
- Its queen raids are **5.78 vs 2.46**, and its short-window material losses
  **1.46 vs 2.57**.
- Greek Gift wins **all 80** games in this sample where it establishes a
  sustained three-point lead. Duck converts **19 of its 27** such games.

The capturer-unseen rate is much closer, **9.08 vs 8.91**. Therefore, merely
copying duck's hidden captures is an incomplete plan: Greek Gift's larger
separation is productive king pressure and preserving the resulting advantage.

### Against Instructors: pressure plus discipline

In their **269 shared games**, Greek Gift creates **4.95 vs 2.39** king threats,
**2.51 vs 0.69** unseen threats, and suffers **1.09 vs 2.75** short-window
material losses. It converts **173 of 177** sustained three-point leads into
wins. Those are the immediate capabilities our target curriculum should pursue.

### Against Knight Vision: counterpressure can outweigh material cleanliness

Greek Gift creates **5.80 vs 3.40** king threats and **3.12 vs 1.64** unseen
threats in their 124 shared games. But it has *more* short-window material losses
(2.61 vs 1.86) and unseen walk-ins (3.83 vs 3.31). It is not winning this matchup
by being the more conservative side on these metrics.

Greek Gift records **17 score points in 61 games** where it was at some point
three points behind for at least four plies; Knight Vision records **3 points
in 47** such games. These are post-game conditional groups, not matched
comeback experiments. Still, they identify useful examples to inspect for
counterplay instead of teaching our bot that every material deficit is hopeless.

## Important rules correction: “seeing the king” is not a scouting metric

The pre-decision enemy-king-visible counter is **zero for every team** in this
panel. That is consistent with the referee, not evidence that no team locates
kings internally. Visibility of an enemy king through a legal capture means it
is capturable; the referee ends the game before that capturing side needs to
choose another move (`fow-starter/referee.py:133–136`). The attacker can see a
king in intermediate post-move observations before it escapes.

In our engine, `ExpectedKingSighting` asks whether the king square becomes
visible immediately after our move. Under these rules, that substantially
amounts to creating a king attack. It does **not** calculate the expected
information gain from observing empty squares or blockers around several
possible king locations. `KingBeliefDiffuseness` also uses `1 - max_mass`, not
Shannon entropy. The existing term may still help; the claim that it implements
an information-gain scout is too strong.

A real scouting experiment should partition hypotheses by the observation a
move produces and measure the expected remaining uncertainty or improvement in
the next decision. Evaluate king-location mass/calibration from the player's
whole observation history; do not use pre-turn king visibility as its KPI.

## What we should borrow

1. **Middlegame attack sequences, not isolated attacking moves.** Curate several
   decisions before a hidden king threat and its follow-up after an escape.
   Include failed attacks and ordinary positions as controls. Learn safe routes
   and continuation choices against plausible king regions.
2. **Winning-position conversion.** Build separate exams and training starts
   from real +3 positions, retaining the full actor history. Grade final score,
   irreversible giveaways, lost king-location information and clock use. Our
   28/42 conversion is an especially actionable gap.
3. **Attack/defense jointly.** Require improved king pressure without increased
   avoidable material losses and fatal moves on natural-frequency evaluation.
   A model that raises a “hidden attack” counter by hanging its queen fails.
4. **Decision-relevant information.** Test whether a move changes our posterior
   enough to improve the next choice. More visible tiles alone is not the goal.
5. **Counterplay when behind.** Mine Greek Gift–Knight Vision recoveries for
   king hunts and forcing sequences, without assuming every sacrifice was
   intentional or universally correct.

Concrete development examples against TA-S include
[pcqqshju](https://www.mit.edu/~6.7980/fow/?tab=arena&game=pcqqshju): Black's
plies 72 b1f5, 80 f3g3 and 82 g3f3 are unseen king threats; and
[ymrsbogk](https://www.mit.edu/~6.7980/fow/?tab=arena&game=ymrsbogk): White's
plies 37 g4g5, 53 f1e1 and 59 f3e5. The final threat in each is followed by a
losing response. These are illustrative sequences, not a solved opening book.

The first concrete trainer repairs, target league mix and hybrid-aware learning
proposal are in [note 020](020-astra-top-six-review-20261009.md). Together the
evidence favors **learning coordinated attacks that preserve information and
convert advantages**, with a correctly trained and measured hybrid controller.
