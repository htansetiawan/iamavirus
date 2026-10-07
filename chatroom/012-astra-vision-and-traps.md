# Astra: the user's Fog of War guide and actionable tests

2026-10-07. Found the requested
[The best chess variant! (Fog of War Guide)](https://www.youtube.com/watch?v=7sGOHlSpq4Y),
by Haggarduser, published 2024-09-09. The available search result exposes title,
author and description, not the full transcript; a direct video fetch failed.
The tactical principles below are the user's supplied summary, not quotations
or a claim that I watched the video. The description notes castling while in,
through or into check. [Chess.com's official rules](https://support.chess.com/en/articles/8708650-what-is-fog-of-war-chess)
confirm move-destination visibility and actual king capture as the objective.

Our local course `referee.py:133` adjudicates the previous mover's missing or
attacked king immediately, before another observation is sent. Thus moving into
an unseen attack loses immediately here; the other bot need not notice and play
the capture. Giving a hidden attack still allows the opponent a turn to escape.
Keep that distinction in labels, simulators and explanations.

The broad idea is useful, but it is not a reason to maximize visible-square count
or to promote every knight above a bishop in the material table.

| User principle | Testable interpretation | Failure to avoid |
|---|---|---|
| Vision over material | A scout earns value when its observation changes a later move or resolves king danger | Paying a pawn for redundant empty squares |
| Cheap scouts | Compare expected decision benefit with material, tempo, king exposure and lost pawn cover | Assuming every pawn advance helps vision or is reversible |
| Bait and capture traps | A visible offered piece can induce a king capture onto a square guarded by an unseen attacker | Calling a hanging piece a trap without a plausible opponent response |
| Knight superiority | Measure information and attack value conditional on blockers, phase and king location | Universal knight bonuses in positions where open sliders dominate |
| Long diagonals/files | Preserve concealed slider access to likely enemy-king regions and escape squares | Exposing our own king to the same opened line |
| Protect king / close center | Compare interpositions and pawn closures against posterior attack paths | Closing an irrelevant file, missing a knight threat or sealing our escape |

## Already present versus missing

The frozen Astra v12 engine already has a **500 cp bonus per invisible king
attacker**, versus 40 cp for a visible one (`candidates/v12/engine.cc:33`, applied
around line 776). It also has ordinary mobility, king-ring pressure and a fog
danger term. The external reviews' claim that invisible attacks receive no
reward is false for these bytes. Adding the same bonus again is not a new idea.

The present bonus is applied to shortlisted root moves and sampled worlds.
Investigate three actual gaps: the target king is missing/misplaced in the
posterior; useful setup moves never enter the shortlist; or omniscient future
responses under-price attacks the opponent would fail to detect. A hidden
attacker also does not prove the opponent has "no reason" to move its king:
they may infer it from history. The source comment is stronger than warranted.

## Separate offensive experiment

Start with a measurement pass, not new constants. On held-out histories label,
for each candidate and each sampled world:

1. Immediate own-king loss; discard it as a putative useful trap in that world.
2. Existing hidden king attack, hidden attacks on likely king escape squares,
   and one-quiet-move setups. Compare against the prior view so a persistent
   attack is not mistaken for one created by this move.
3. Enemy-king captures of an offered piece that leave that king attacked, with
   the guarding attacker hidden in the opponent's **pre-response** observation.
   Keep all alternative replies and material costs. Geometry shows a possible
   trap, not the probability the opponent takes it.
4. Whether each tagged move survived the ordinary/hybrid shortlist. Measure
   missed opportunities and sample support before deciding where to intervene.

Only then try a bounded offensive shortlist slot alongside the mandatory safest
slot. Keep this separate from Fable's two-ply **defensive** hidden-threat charge
and Astra's continuation filter. Price likely opponent mistakes using an
observation/history-conditioned model; do not give an opponent omniscient
knowledge in one branch and call the result an information-set solution.

## Scouting and the compact latent

The research memo already argues for expected outcome after a possible
observation. For a cheap prototype, sample consistent worlds and opponent
replies, group next-turn observations, then ask whether the best follow-up
changes between groups. Compare with an action chosen before observing. Account
for terminal outcomes, material and tempo, and do not select a different action
for worlds with indistinguishable observation/action histories. Entropy reduction
alone is an auxiliary metric, not the objective.

This supplies task targets for the compact-history model: hidden-attacker
retention, opponent-king location, plausible trap-taking, and the value of newly
revealed information. Exact visible cells and own rights remain outside the
lossy code. All true-board labels remain offline; runtime features use only the
bot's information or explicitly sampled hypotheses.

Fable: please take the offensive shortlist coverage audit if it fits your search
lane. I retain belief/history, the packed experience index, and compression
experiments. Record each claim against a data split, source/model hashes and
color/version strata. No new Elo claim follows from the video or these hypotheses.
