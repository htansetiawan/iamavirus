# History recovery: better average belief, unresolved tactical tail

The first complete port experiment does **not** justify an arena release.
History reconstruction improves retention of the true board and hidden-square
Brier, but sometimes removes the last hypothesis warning of a fatal move.
This is a useful negative result: average belief quality and tactical coverage
must be measured separately.

## Frozen comparison

The runtime is based on the immutable Fable arena-v13 archive, SHA256
`39fb4480e0b7ceaaf1746ca5fc783d65d8247d936190edfbc76a13fc667da1d5`.
The probe SHA256 is
`9a1ab62e870a9d2ae3b7c909a3f0d86242183ded1ee6980daa17e2771b2e6e2f`.
This binary has transactional RNG rollback but predates the en passant fix.
Modes 0/1/2 mean original filtering with own-move memory repairs, strict
observation/survival filtering, and strict filtering plus history recovery.
Priors 1/2 are the archived hand-written and learned move priors.

All 3,804 runs completed: 634 losing seats × three modes × two priors, seed 777,
2,048 particles. Each arm sees 54,116 observation updates and 1,736,715 hidden
square labels. Truth and recorded opponent actions are used only for generating
observations and offline scoring; the filter receives actor views and own moves.
All 823 mode-2 runs with no successful history rescue exactly match their mode-1
partners on population metrics. The earlier pilot failed this invariant and is
retained separately.

## Results

| Prior / mode | True board retained | Hidden Brier ↓ | Random rebuilds | Fatal recorded moves assigned zero risk ↓ |
| --- | ---: | ---: | ---: | ---: |
| Hand / 0 | 31.55% | 0.25724 | 1,471 | 33 / 634 |
| Hand / 1 | 31.49% | 0.25740 | 1,518 | 39 / 634 |
| Hand / 2 | 34.71% | 0.24849 | 1,160 | 49 / 634 |
| Learned / 0 | 39.06% | 0.23672 | 1,220 | 24 / 634 |
| Learned / 1 | 38.94% | 0.23718 | 1,225 | 29 / 634 |
| Learned / 2 | 41.56% | 0.22847 | 914 | 33 / 634 |

Learned-prior mode 1 → 2 improves retention by 2.63 percentage points (paired
whole-game bootstrap 95% interval 1.78 to 3.58) and Brier by −0.00871 (−0.01141
to −0.00623). The log-loss change −0.01054 has an interval crossing zero
(−0.03735 to 0.01455). Of the fatal recorded choices, eight previously assigned
zero risk gain a warning, while twelve lose their last warning. These are
forced-history diagnoses; they do not establish what the engine would choose.

The learned prior itself looks better than the hand prior on this corpus,
including terminal recognition, but possible overlap with its training data and
loss-based seat selection prevent a held-out strength claim.

## Duck and the TA baselines

| Opponent | Seats | Learned strict → history retention | Hidden Brier | Fatal choices given zero risk |
| --- | ---: | ---: | ---: | ---: |
| duck | 47 | 53.28% → 58.84% | 0.20668 → 0.19362 | 2 → 1 |
| TA Baseline A | 11 | 34.28% → 38.57% | 0.27263 → 0.25909 | 0 → 0 |
| TA Baseline S | 25 | 65.43% → 69.21% | 0.18146 → 0.16505 | 1 → 2 |

Duck is promising within this retrospective sample, but the small TA samples
and opposite tactical directions make an opponent-wide claim premature.

## Concrete rule defect and repair

At Black's view after ply 63 of `y06kx1q2`, White just played `b2b4` and Black
can capture `a4b3` en passant. Random reconstruction discarded the en passant
target. In two arms it exhausted all 65,536 proposals, matched none of the
views, and considered the actual capture illegal in all 2,048 particles.
Adding more particles cannot reconstruct missing rule metadata.

Strict recovery now carries an en passant target inferred from actor views,
or known from our own double push. The 24-run replay regression includes all
three modes, both priors and seeds 1/2/3/777. All 16 strict/history cases now
match the view and permit the actual capture in every particle. The two formerly
failing cases need only 2,048 proposals with no rejection. The focused suite
passes 2,229 checks. See the [receipt](port-ep-fix/correctness.json).

The corrected four-arm full run is recorded at
`/media/henrytan/seagate/iamavirus/astra/belief/history-v2-ep-corpus-r1-20261008/`.
Its results must stay separate from the table above. A first launch used an
incorrect binary filename and stopped before running any probes; its preparation
directory is `history-v2-ep-corpus-20261008` and contains no experiment results.

## Next decision

Post-hoc inspection of the twelve newly missed learned-prior fatalities shows
the concentration problem directly. In eleven, the most recent history rescue
contained no copy of the true board; eight rescues returned only one distinct
state. For `3o8ctsy9`, terminal diversity falls from 2,044 boards under strict
filtering to nine under history recovery, and the real hidden queen disappears
from support. Some reconstructions are certified as legal histories from the
opening yet are still wrong about the actual game. Certification is a
consistency property, not calibrated certainty. These selected cases motivate
the next experiment; they do not estimate a population-wide failure rate. See
[the retained diagnostic](port-tail-before-ep.json).

Keep history recovery experimental. After the corrected corpus finishes,
inspect the newly missed threats and test actual chosen actions on those
complete histories. Recovery needs calibrated uncertainty or preserved tactical
support if coherent histories become too concentrated; simply increasing the
penalty on an absent attacker cannot help. A compact learned representation
has the same burden: improve actionable uncertainty, not just reconstruction.

The analysis uses 10,000 paired bootstrap draws clustered by whole game, with
no multiplicity adjustment. It is exploratory, one filter seed, a selected
losing corpus, and CPU timing on a shared machine. No Elo or deployment gain is
inferred. Machine-readable details are in
[port-corpus-before-ep.json](port-corpus-before-ep.json).
