# Toward 2000: credible opponents and a diagnosis we can act on

> **Correction, 31 October:** the separate Black-conversion mechanism proposed
> below was not supported by the follow-up. At frame 30 Black has just moved;
> many apparent material leads are captures awaiting White's recapture. Requiring
> a three-point lead to persist through frames 30–32 gives conversion scores of
> **78.0% for Black (41 games) and 82.9% for White (76)**. This does not establish
> the large conversion deficit previously reported. See the
> [completed diagnosis](../../../fable-submissions/analysis/black-conversion-20261030/result.md).
> The earlier statistics and plan below are retained as the historical record,
> not the current prioritization. The best-supported next target is hidden-attacker
> probability and sampling coverage; a calibrated search change still needs to
> be implemented and tested. The proxy-calibration results remain unchanged.

Astra, 30 October 2026. Arena v35 remains the control. No arena submission or
activation was made. The standing at the start of this work was **1922 Elo**;
2000 is the target, not an achieved or forecast result.

## What we need to improve

The new evidence supports **two separate failure mechanisms**:

1. **Uncompensated early piece losses.** Fable's updated comparison on a common
   opponent set finds v35 loses material after fog-exposed moves more often than
   the leading bots. Count net loss after a reply, not just whether a piece was
   captured. Captures include ordinary trades.
2. **Failure to convert Black's advantages.** In our frozen recent reference
   games, Black has better mean material at ply 30 but a lower score than White.
   Fable checked a larger sample: with a lead of at least three points at ply 30,
   White scored 80.7% in 83 games, Black 44.9% in 127. This is an association to
   investigate, not proof that a particular king-safety rule will fix it.

See [Fable's analysis and follow-ups](../../../fable-submissions/analysis/black-losses-20261030/result.md).
The agreed next diagnosis locates the first lasting reversal in matched Black
leads, then separates an absent true board, too little weight on it, omission
from sampled worlds, and a search/frontier-value failure. Those imply different
fixes. Another generic risk penalty would skip that distinction.

An approximately 78-point strength gain corresponds to about 61% expected score
against a stationary 1922 opponent under the Elo model. Henry's earlier 80%
head-to-head target is a much stronger challenge (about 241 Elo); this work does
not silently replace that promotion requirement. A transient rating crossing
2000 is also different from sustained performance against the reference panel.

## What was built and measured today

**Current, validated data.** We froze the latest 1,000 Instructors v4 games and
1,000 duck v6 games: 1,950 unique games from 27–30 October, including their games
against other teams. We reused 1,824 cached replays and downloaded 126 missing
ones through the paced public GET API. Every recorded board and both views were
validated against the local rules implementation; no failures or actor-derived
move-set mismatches survived preparation.

**Separated training and test games.** Identical full move sequences are grouped
together and groups split chronologically. Only the reference player's seat is
used as an imitation target. Final train/validation/test counts are
1,398/296/308 episodes and 60,607/12,654/13,818 decisions. The collector's original
70/15/15 game labels are superseded by this duplicate-group split. Truth supplies
offline labels and scoring; the actor consumes its permitted observation history.

**Small model refresh, not an engine upgrade.** Existing CNN/GRU opponent policies
were fine-tuned for three epochs, selected by validation policy likelihood, then
evaluated once on the untouched test set. The two refresh/export runs completed
in about six minutes. GPU work has finished. The deployed mist-c engine was not
trained or changed.

| Held-out move prediction | Old policy | Refreshed policy |
|---|---:|---:|
| Instructors accuracy, 7,921 decisions | 31.60% | 32.39% |
| Instructors negative log likelihood | 2.356 | 2.314 |
| duck accuracy, 5,897 decisions | 36.14% | 37.56% |
| duck negative log likelihood | 2.230 | 2.147 |

Lower negative log likelihood is better. ONNX export parity passed for both
models. These modest improvements do **not** establish opponent fidelity in a
game. The auxiliary danger/value heads were not the training objective; their
outputs are not newly calibrated safety estimates.

**Exact-archive replay comparison.** We selected 24 decisions from eight held-out
v35 games, balanced across reference team and our colour, at three game stages.
We replayed the full permitted history through frozen arena-v35, rejected-r4,
and mist-c-v23 archives, then repeated v35. Each received the same recorded clock
and forced earlier own moves, on an exclusive core pair.

All 96 decisions completed legally, with no immediate fatal choice. Identical
v35 runs nevertheless chose different moves in **3/24** cases: timed belief
thinning/search introduces a measurable noise floor. Fog-exposed piece moves
were v35 **2**, r4 **2**, mist-c-v23 **3**, repeated v35 **3**. This small diagnostic
cannot rank the candidates' playing strength.

A recorded opponent reply is accepted only if its complete observation history
remains unchanged and the reply is legal. Changed opponent views censored 4–6
of the 24 continuations per variant. Continuing the original PGN after an
arbitrary changed move would fabricate an opponent that cannot respond.

**Responsive games.** The refreshed policies were packaged with our frozen
hybrid-era search wrapper, with the opening book disabled. These are explicitly
*learned hybrid proxies*, not Instructors' or duck's executable bots. The pilot
uses two colour-swapped pairs per proxy against exact v35, fixed seeds, the
official local referee, and 180+2. Initialization must prove ONNX loaded and the
hybrid mode is active; silent C++ fallback invalidates the test. All eight games
finished normally with no protocol errors or inference failures in retained
diagnostics. Every resulting frame was validated against the rules.

| v35 against | Pilot W–D–L | Pilot score | Authentic recent score |
|---|---:|---:|---:|
| Instructors hybrid proxy | 3–0–1 | 75% | 44.9% (68 games) |
| duck hybrid proxy | 4–0–0 | 100% | 41.1% (56 games) |

**Decision: do not admit these hybrid proxies as arena-strength promotion
tests.** Eight games are too few to estimate their strength precisely, but they
have not reproduced even the control's difficulty against the real opponents.
They remain labelled experimental stress opponents. No candidate-versus-proxy
win rate will be advertised as an Elo gain. Full results are in
`proxy-summary.json`, `proxy-games.json` and `calibration-readout.json`.

One instructive failure is `duck-pair0-white`: the proxy led by nine material
points at ply 30 and still lost. At its final decision, its neural policy gave
`f8e7` about 79% probability and `f8g8` about 8%; the legacy search chose `f8g8`.
True-board scoring confirms `f8e7` was legal and nonfatal, while `f8g8` lost
immediately. Thus policy prediction accuracy does not describe the hybrid's
actual decision rule. Failure of this configuration should not be reported as
proof that a model-only proxy cannot work. That would require a separate test;
the present experiment is capped at eight games.

## What a useful benchmark must reproduce

The frozen authentic v35 results are:

| Reference | Games | W–D–L | Score | White score | Black score |
|---|---:|---:|---:|---:|---:|
| Instructors v4 | 68 | 29–3–36 | 44.9% | 52.9% | 36.8% |
| duck v6 | 56 | 21–4–31 | 41.1% | 48.2% | 33.9% |

Across these games, 239 early piece moves landed on a square attacked from the
fog. Of the 168 captured on the next reply, only **77** lost net material across
our move and the reply. A raw capture-rate penalty would therefore mislabel many
trades. Allowing our next move for a recapture reduces the count with a remaining
loss of at least two points to **27 events** across the 124 games. Even this
longer horizon can miss a combination or a sound sacrifice. Definitions and
both horizons are retained in the readout; actual game results remain primary.

Benchmark admission has three distinct levels:

1. **Decision diagnostic:** observation-correct replay, terminal and legality
   checks, trade-aware risk labels, and repeated controls. It identifies concrete
   mistakes; it does not produce a counterfactual whole-game win rate.
2. **Responsive stress opponent:** a model must respond legally after deviations.
   Before treating it as an arena-strength proxy, test its score, colour gap,
   openings, tactical behaviour and rankings of historical candidates. Matching
   one aggregate score can happen for the wrong reasons. Eight games are only a
   cheap initial screen, insufficient to certify it.
3. **Arena confirmation:** compare new-version results on the same reference
   versions and colour mix, with uncertainty and the broader opponent panel.
   Direct play against v35 remains necessary evidence, but one matchup cannot
   detect every intransitive weakness.

In particular, r4 is a poor performer in the **overall** observed arena pool,
but it has only four recorded games against each current reference (2W–2L each).
It is not an established negative control for each individual opponent. A proxy
should not be tuned to manufacture that ordering. Likewise, mist-c-v23's
52W–1D–47L confirmation against v35 fails the strong promotion target, but a
100-game result near 50% does not rule out every modest improvement.

## Reproduction and ownership

All new code is in `astra-submissions/tools/`; no deployed engine source was
edited. Large data, checkpoints, exports, builds and replays are on the authorized
external disk:

```
/media/henrytan/seagate1/iamavirus-data/astra/reference-proxy-20261030
```

Pipeline: `collect_reference_replays.py` → `prepare_reference_models.py` →
`fit_reference_models.py`; in parallel, `reference_replay_gate.py`; then
`calibrate_reference_proxies.py` → `reference_proxy_readout.py`.
Use the repository `.venv/bin/python`. Training/preparation uses cores 0–1;
timed tests use exclusive pairs 2–3 and 4–5, reserved in `chatroom/cores.json`.
Local bots share a pair rather than using the arena's process suspension, so
absolute timing remains a calibration limitation. Each full game has a 15-minute
wall cap; failed attempts are recorded separately, never scored as losses.

`collection-summary.json`, `dataset-manifest.json`, `model-evaluation.json`,
`replay-pins.json`, `replay-summary.json` and `proxy-pins.json` record the inputs,
immutable archive/model hashes and measurements. The compressed final game index
holds all game IDs, hashes and split assignments. Large artifacts are referenced
by external paths rather than committed to Git.

The first replay attempt used Python threads and failed native-rule validation
during simultaneous initialization. That entire attempt was retained separately
and discarded from results. Process-isolated lanes passed; the likely shared
initialization race was reported to Fable. No claim of an arena-engine rules bug
is made. Unit tests cover valid/censored continuations, immediate terminal loss,
illegal moves, hidden versus visible attackers, pawn attacks, and equal trades.

The next human review should assess a concrete candidate tied to one of the two
failure mechanisms, its control comparisons, and the remaining uncertainty—not
promote another architecture merely because its offline loss decreased.

## Next review: one bounded candidate, evidence before another long bench

| Owner | Deliverable | What changes the decision |
|---|---|---|
| Fable | Trade-stratified hazard calibration on **all** candidate piece moves; actual reply-loss labels only for the move really played | Separate zero estimates (missing support or missed worlds) from wrongly scaled nonzero risk. A monotone probability map cannot recover an attacker absent from every world. |
| Fable | Matched Black wins/losses from a material lead; first lasting reversal, truth presence/weight/sample inclusion | Choose the faulty component from the evidence rather than adding another universal penalty. |
| Astra | Independent review of that proposed change and a frozen regression comparison; repeated controls where timing matters | Reject leakage, illegal counterfactual replies, or apparent gains smaller than repeat noise before a long run. |
| Joint, then human review | One clearly specified candidate, exact bytes, predicted effect, bounded test and stop rule | Wins against v35 and authentic reference evidence remain decisive; diagnostic improvements alone do not earn promotion. |

These are review deliverables for the next 24-hour checkpoint, not a promise
that an unattended job will continue indefinitely. The current proxy pilot is
bounded at eight games. It does not authorize another training sweep, arena
upload, or replacement of Instructors/HYPOTHERMIA as the minimum references.
