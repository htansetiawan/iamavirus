# Tactical-intent prior and belief-state ablations: retain controls

**Neither candidate is promoted.** The new tactical prior passes mathematical
and native parity checks but fails the sequential posterior gate. A belief-only
state adapter preserves the other heads exactly, yet its apparent enemy-piece
gain is outweighed by worse occupancy calibration and, for attention, worse
conditional localization. No engine default, archive or arena version changed.

## Hierarchical tactical prior

The 26-feature fitted control remains the within-group model. Candidate moves
are partitioned, in priority order, into check, capture/promotion and quiet.
Seven learned group-context corrections adjust the probability assigned to
each group. Features are group identities, log group sizes and group-average
forward displacement/centralization. This preserves relative odds within each
group. Setting the corrections to zero reproduces the baseline exactly.

The implementation learns a conditional-logit gate over group mass, using the
baseline group probabilities as offsets. Runtime logits can equivalently add
the learned correction to each member of its group. It adds linear passes over
already computed features; it does not add a search, new visibility queries or
a player-name lookup. Like the existing prior, it conditions on a hypothesized
full state, not an information-set-consistent actor policy.

Training: **1,686 games / 109,301 moves**, same frozen corpus and base weights
as the previous visibility-prior experiment. Validation: **352 games / 22,757
moves**. Today's diagnostic losses were not training data. The already inspected
legacy test split was not reused as a fresh confirmation test.

| Validation measure | Control | Intent gate |
| --- | ---: | ---: |
| Move NLL | 2.710019 | 2.707027 |
| Conditional move NLL when the observation is unchanged | 2.503533 | 2.502239 |
| Hidden-check Brier, all moves | 0.012926 | 0.012892 |
| Hidden-check Brier, unchanged observation | 0.011772 | 0.011478 |

The small likelihood gain is positive under game bootstrap. The all-move
hidden-check Brier difference is inconclusive; the unchanged-observation
reduction is 0.000295, interval [0.000120, 0.000478]. This initial screen alone
does not establish a better posterior or playing strength.

Native C and Python probability calculations agree across **688,479 actions**
at all 22,757 validation positions, for both zero and fitted gates. Maximum
absolute log-probability difference is 1.586e-6 against a declared 1e-5 limit.
Unit tests recover known class frequencies, verify zero-gate identity and
preserve within-group odds, including states with missing groups.

### Sequential gate: reject promotion

Historical own moves and observations are forced. Cap 10,000, seed 41, unchanged
full prior below that cap. Two existing development cohorts contain 43 games;
one added diagnostic game is excluded from the primary 42-game table. The
zero-gate binary matches **every non-timing field** of the prior control on
all 1,680 decisions. Both arms preserve the independently checked rule labels.

| Primary 42 games / 1,650 decisions | Control | Intent gate |
| --- | ---: | ---: |
| True state present | 1,386 | 1,379 |
| Belief collapses | 13 | 17 |
| Hidden-attack Brier | 0.0141242 | 0.0140315 |
| Historical fatal-move Brier | 0.0099352 | 0.0099885 |
| Belief-update CPU seconds | 42.526 | 42.901 |

The paired Brier and support intervals cross zero, while collapses increase.
There is no affirmative evidence to advance to clocked matches. Keep the model
and reproducer as a rejected experiment; do not tune it on the Greek Gift
fixture. These reused development cohorts are not a fresh confirmatory sample.

## Current features-v2: what recurrence actually contributes

Models are the original, hash-verified 6,000-update CNN and small-attention
checkpoints trained on 3,766 games, source revision `09fd15f`. Both evaluations
cover 64 held-out games / 5,179 decisions. Frozen source, native rules, validation
shard and checkpoint hashes are recorded in each output. No GPU or test shard
was used. The intervention is applied at inference, with no retraining.

First, reset all GRU state before each observation while retaining explicit
last-seen/age features. In attention, this improves enemy-only NLL from 1.1310
to 0.9417, but worsens policy NLL from 2.4657 to 2.5005 and danger Brier from
0.03303 to 0.04250. The CNN's enemy-only metric also improves, with worse
danger. Thus removing recurrence globally is not supported.

The implemented `CurrentEventBelief` adapter instead uses a fresh current-event
GRU calculation for the belief head while preserving the original recurrent
state for policy, danger and value. It reuses the spatial features. Sequential
tests and every non-belief per-game metric match the original exactly. The
compressed-latent contract is explicitly rejected by the adapter.

**That mechanical separation does not make the changed belief head better.**
Enemy-only NLL conditions on squares already known to contain an enemy in the
offline labels. Increasing piece probabilities everywhere can improve that
metric while harming the full posterior. The following decomposition catches
this failure. “Location NLL” normalizes each piece type's predicted mass over
the currently hidden squares, then scores the true hidden locations; it removes
a uniform occupancy boost. It is a diagnostic, not a joint board likelihood.

| Attention belief metric | Full recurrence | Current-event belief |
| --- | ---: | ---: |
| NLL across **all** hidden squares | 0.48590 | 0.52236 |
| NLL on hidden enemy squares only | 1.13100 | 0.94167 |
| NLL on hidden empty squares | 0.20258 | 0.33819 |
| Binary occupancy Brier | 0.10707 | 0.11859 |
| Predicted hidden occupancy | 29.55% | 37.96% |
| Conditional piece-type NLL | 0.46046 | 0.47218 |
| Conditional location NLL | 1.98255 | 2.00405 |

Actual hidden occupancy is **30.52%** (49,330 of 161,649 squares). Attention's
location NLL worsens by 0.02150, interval [0.01548, 0.02755]; all-hidden NLL
worsens by 0.03645, [0.03124, 0.04159]. The adapter mostly inflates occupancy,
and does not establish more accurate piece localization.

CNN behaves similarly but less strongly: all-hidden NLL 0.48742→0.49400,
predicted occupancy 30.75%→33.84%, occupancy Brier 0.10295→0.10496.
Its location NLL change is inconclusive, −0.000164 [−0.002124, 0.001788].
Keep full recurrence in both models. This corrects the earlier interpretation
that enemy-only improvements by themselves diagnose faulty belief memory.

All interventions compare CPU against CPU. Attention's ordinary CPU/GPU
aggregate differences are below 6e-8. CNN has a small device-dependent argmax
change (one hidden-knight recall event, 0.000238); its policy NLL differs by
9.2e-6. These differences do not explain the large paired intervention effects.
Bootstrap intervals resample games, not seeds; validation has been reused.

New metrics have independent tests: a uniform boost to occupancy cannot improve
conditional type/location metrics, visible squares never enter the location
normalizer, and enemy NLL decomposes into occupancy and conditional type terms.

## New public data, independently reconstructed

Snapshot at 16:44:01 UTC: active arena **v30**, Elo **1772.7383**,
**153W–24D–173L / 350 games**. Duck is 1905.3901. These are the existing arena
submission's results, not either experiment above.

Cached **28 additional games: 17W–1D–10L**. The independent referee validates
all **2,095 frames**, both observations, legal moves and terminal outcomes.
All ten losses have at least one physically surviving final move; seven final
errors move the king, three advance a pawn while under hidden attack. Every
terminal attacker was hidden before the fatal action. These are hindsight
labels and do not prove the actor could identify the safe move.

Nine losses were already behind in material. The isolated Instructors fixture
`4bkwxxng` is different: +100 centipawns, a visible queen on e7, and Kf8xe7
walks into an unseen rook on e1 and knight on d5. Kf8–g8 is the sole true-board
survival. Retain it as a protected-bait fixture, separately from late material-
down losses. Today's data has not been used to fit these candidates.

## Artifacts and next gate

`inventory.json` contains hashes for 88 retained artifacts, including compressed
raw replays, per-game predictions, native source snapshots, exact baseline
parity evidence and comparison reports. Large original outputs remain under
Seagate's `m4-intent-prior-20261011`, `memory-v2-20261011` and
`m4-fresh-20261011-1644` directories.

Keep the richer occupancy/type/location diagnostics in future model selection.
Before another prior fit, investigate sequential support loss directly; marginal
action likelihood has now failed to predict posterior improvement twice. No
real-clock resources or release number are spent on these rejected candidates.
