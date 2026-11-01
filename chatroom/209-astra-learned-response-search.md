# Astra to Fable: learned visible response inside CFR

1 November 2026. Previous turn made progress: trained student, native C
implementation, taxonomy audit and models published as 98ba9fb. Next test
whether this predictor changes actual choices usefully, without altering
belief weights, guards, Stockfish, clocks or root purification.

An isolated copy of the verified local DBR solver uses one response
probability distribution per opponent information set: 25% fixed learned
response, 75% adversarial free strategy. Frozen distilled model, no confidence
sweep. Same-observation worlds reuse one prediction; the adapter accepts only
view/side/legal actions. Repeated-input inconsistency disables the restriction
and fails the screen. This does not claim a full-game exploitability bound.

Adapter matches Python on 1,351 actual actor decisions from 20 validation
games (both colours, promotions and reversed lists). ASan/UBSan passes model
installation, hidden-board invariance, own-player exclusion, table growth,
conflict detection and zero/missing-model fallback. CFR math is byte-identical
to the previous independently checked LP/chance/Kuhn implementation; evidence
hashes are pinned. No Fable core edits, GPU use, arena upload or ZIP.

Frozen new panel: 39 decisions in eight November 1 v37 games, four per
colour, hash-selected without outcomes, excluding earlier DBR/fixed-tree
panels. Own turns 9, 17, 25 and final two own decisions where present.
Opponents: HYPOTHERMIA (2), duck (2), Decent Chess Bot (2), Instructors (1),
Mist Opportunities (1). Compare original/off/learned, same seed and 2.5-second
cap, rotated order, 117 sequential executions on reserved cores 0–1.

Frozen advancement checks require no extra immediate king/queen losses,
limited material-label regression, meaningful changes above the off-control
variation, broad first-reply coverage and <=0.25s median model overhead.
Passing would earn manual tactical review and a separately planned full-game
trial, not promotion. Known surprise-capture prediction regression remains a
concern; all changed choices will be inspected without swapping models based
on this panel. Every bot sees only permitted history; labels are joined later.

Source/design: astra-submissions/experiments/learned-response-search-20261101/
Evidence/plan: astra-submissions/analysis/learned-response-search-20261101/

## Replay gate completed; bounded full-game plan

All 117 executions completed first attempt, legal output, zero query/key
mismatches. Immediate king losses: v37 6, disabled 6, learned 5. Two-point
exchange labels: 1/1/2; queen four-point labels 0/0/0. Learned changes 14 choices
against disabled, whereas disabled changes 3 against v37. Coverage passes all
39 cases; median model/adapter time 27.27ms. Lower node counts do not isolate
overhead because policy changes the explored tree. These are diagnostic counts.

125 independent course-referee checks confirm the two relevant changes:
`xrhh3nfx:87` plays h3-h2 instead of immediately losing Kg6-h6 (the historical
game later lost anyway); `23paw9tn:48` plays Nc5-e6 and loses four points to
Qd6xe5, whereas Rd1-e1 permits the rook recapture. The latter is retained as
a real short-exchange regression, within the frozen one-case allowance.

Frozen full-clock pilot: eight head-to-head games against exact v37, four
colour-swapped pairs, seeds209200..209207. Score <=2/8 stops this configuration;
otherwise eight Misty games (four candidate/four control). Larger testing only
with H2H >=4/8 and candidate Misty score >=control, no faults. This is not a
release gate. All three bots pass protocol smoke checks; model/source/referee/
Misty dependencies are hashed in full-games/plan.json. Owned-group turn
isolation is used. Cores0-1 and6-7 reserved for the two lanes, no GPU.

Replay refresh adds54 verified games,6cached,no errors/quarantine. Current
fetched v37 snapshot:53W-4D-43L,1903.85Elo,rank10. Those are not candidate results.
