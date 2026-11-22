# Rehearsal: search and inference in Fog of War chess

*A modular speaking outline for human review, November 11 UTC. Five minutes
is a draft scaffold; the allotted time and final format remain unconfirmed.
All numbers below are dated evidence, not a live arena reading.*

[TOC]

## A one-minute opening

“Our bot plays chess from a private, incomplete view. It must reason about
where the opponent's pieces might be and what the opponent knows about ours.
The course referee ends a game when a move leaves its mover's king capturable,
including attacks the player cannot see.

“We implemented a C inference-and-search engine using ingredients from Obscuro.
It retains weighted possible boards, builds a small local game tree, scores
its frontier with Stockfish and updates strategies with counterfactual regret
minimization. The final move is the largest-probability root action.

“Our clearest engineering result is faster frontier scoring. Our clearest
experimental lesson is that better replay inference did not imply better
play. The main architectural limitation we will illustrate is that knowing
the board ourselves does not resolve what the opponent knows.”

## Five-minute route through the evidence

| Time | Show | Explain |
| --- | --- | --- |
| 0:00–0:40 | The private-view win in [two games](presentation-cases.html) | Black sees a rook but not its queen support. Taking the rook leaves its king capturable. The replay shows hidden support, not proof of our engine's intent to bluff. |
| 0:40–1:35 | The pipeline in [overview](presentation-20261203.html) | View → weighted boards → root screen and world sample → growing tree → Stockfish → CFR → action. Distinguish retained boards, search worlds and future nodes. |
| 1:35–2:30 | [One decision](presentation-move.html) | Fourteen possibilities reduce to one. The initial best Stockfish child is Nf3; after outer search, e3 has 53.15% strategy share and is selected. That percentage is not a win forecast. |
| 2:30–3:35 | The two experimental stories below | Component speed, inference quality and playing strength are separate measurements. |
| 3:35–4:35 | [Who knows what?](presentation-knowledge.html) | Bf4 and Nc3 histories give Black identical observations. One known board for White still leaves opponent uncertainty. Legal compatibility alone does not supply a probability. |
| 4:35–5:00 | The contribution and limits | Native implementation, replay pipeline, measured scorer speedup and verified experiments. Full paper re-solving and a qualified learned FoW frontier value remain absent. |

The opening can stand alone; it is not an extra minute added to this route.
For a shorter slot, use the opening and one experiment. For a longer slot,
add the numerical regret update and discuss the information-set example.
Keep detailed table counts in the appendix.

## Two experiment stories to tell accurately

**Faster scoring.** V38 measures **1.57–1.68× scoring throughput** and about
**38% more equal-time nodes** on its fixed panel. The scorer changes numerical
values; it is an approximation. Development play scores 11W–1D–4L against
v37, while the Misty gate fails. Henry separately authorizes the arena trial.
The later **620-game** record is **339W–27D–254L, 56.9% raw score**. After
the first 127 games, historical same-opponent comparisons are approximately
level with v37. That does not establish a lasting Elo gain.
[Release](https://github.com/htansetiawan/iamavirus/blob/main/astra-submissions/v38-release.md)
· [Dated arena follow-up](https://github.com/htansetiawan/iamavirus/blob/main/fable-submissions/analysis/v38-arena-20261108/result.md).

**Better inference, failed playing pilot.** A fixed compact prior passes its
later 63-trajectory inference confirmation, with **+0.47277 nats** in truth
log share. Only two observer games are ours. Its complete-engine pilot then
stops at **1W–8L** under the predeclared futility rule; seven legs remain
unplayed. All **901 frames** pass independent rules checks. We reject that
configuration. We have not proved that every learned prior must fail, or
isolated a single cause of these losses.
[Confirmation](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/355-astra-compact-mass-confirmation.md)
· [Playing pilot](https://github.com/htansetiawan/iamavirus/blob/main/chatroom/357-astra-confirmed-prior-playing-pilot.md).

## Short answers for questions

**Are there always 200,000 boards and 32 searches?** No. The first number is
a cap. With Stockfish, normally there are 32 weighted world draws inside one search; with
32 or fewer retained worlds, all enter with normalized weights.

**What does Stockfish see?** Both sides of one hypothetical complete board.
It scores frontier children with a short search. It never receives the arena's
hidden true board as privileged input.

**What is the current mixture?** Action probabilities in this decision's
local tree. Regret compares each action with that mixture, then adjusts it.
It is not a mixture of moves from old arena games.

**Is this deep RL?** V38 uses offline-fitted move likelihoods, a frozen count
table and search-time regret updates. The historical CNN–GRU/PPO policy is
retired. Borrowed Stockfish NNUE is a separate pretrained evaluator.

**Does collecting games update the bot?** No. A new fit or history rebuild
must be evaluated and packaged. The deployed coefficients and table remain
fixed between uploads. Retrospective taxonomy labels diagnose behavior.

**Does CFR give us a Nash guarantee?** Not for this complete agent. Its
finite, evolving local game, approximate values, guards and final argmax
do not inherit an unqualified full-game guarantee. See the corrected
[course map](course-map.html).

**What persists?** Belief and front-end history persist between turns.
The FoW tree and regrets are discarded. Stockfish workers can retain their
own search cache; that is not a carried FoW strategy.

**Why not immediately add the alternative hidden history?** Membership is
not policy reach. A usable extension needs justified weights, continuation
values and re-solving constraints. Earlier M4/ancestry tests remain negative.

## The human-review checkpoint

Review the three central claims: measured engineering speed, a negative
inference-to-playing result, and the missing opponent-information construction.
Decide which demonstration best communicates them and rehearse explanations
without code. This outline is not approval to start another autonomous
strength campaign. No new candidate or training run is scheduled here.
