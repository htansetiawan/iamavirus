# V38 review — 8 November 2026

**Decision under the frozen plan: hold; this candidate did not pass.**
The ZIP is built and runtime-tested, but its positive direct-v37 pilot did
not carry through to the required Misty result. No numbered v38 release or
arena upload has occurred. The arena version remains a separate human action.

## What changed

The candidate keeps exact v37 C sources, its model fitted on 148,357 games,
and its 359,889-record history table. It replaces Stockfish 19's repeated
depth-one MultiPV root searches with one full-window all-child pass. This
retains NNUE and tactical search but changes some scores; it is an
approximation, not a score-identical optimization.

Staged archive: `experiments/v38-package-20261108/build/v38-review.zip`,
84,989,047 bytes. SHA-256:
`ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`.
Sources, licence, embedded network and an offline rebuild recipe are included.

## Evidence

| Check | Result | What it establishes |
|---|---|---|
| Packaged scorer | 1.57–1.68× throughput; 3,072 paired queries and 64 special calls match laboratory candidate scores, nodes and best moves | Portability and measured scoring speed |
| 51 equal-time decisions | 1.384× median nodes; the same 12 immediate king-loss cases; one material case improved | Extra search, not a strength estimate |
| Full-clock pilot against exact v37 | 11W–1D–4L, 11½/16 points | Promising small development sample |
| Matched Misty, clean games | Candidate 8W–2D–4L (9/14); v37 10W–1D–3L (10½/14) | Failed the required positive margin |
| Additional attempt | Misty timed out against the candidate at ply 75; retained as a technical outcome | Failed the no-technical-fault condition |
| Unstarted games | Two v37 games and one candidate game after that lane stopped | Missing, not losses, draws or replacement attempts |
| Exact ZIP | Ubuntu 22.04 build, startup, both colors, clock probes and two baseline games pass; sampled RSS about 627 MiB | Runtime compatibility, not strength |
| Scorer startup failure | Both colors still return legal moves with the scorer absent or exiting at startup | Tested fallback behavior |

The Misty requirement was 32 clean games, at least 8/16 candidate points and
at least two points above v37. Even granting the technical game and every
unrecorded result optimally to the candidate, it could finish with at most
11 points against v37's already-recorded 10½. **The +2 criterion is
unreachable independently of the timeout.** These are completion bounds,
not confidence intervals or invented results.

All 29 first attempts are retained. Independent course-referee checks verify
2,339 frames, moves, observations, clocks and terminal outcomes. The timeout
protocol is consistent with Misty's 35.48-second deadline; its internal cause
is unobserved. All 203 recorded process identities are no longer live in the
verified host namespace. Neither lane was restarted.

## What we learned

Faster leaf scoring reaches the CFR search, but more nodes alone did not earn
promotion on this opponent. Both versions still lose to hidden attackers.
Three candidate losses end with king moves into attack, and one leaves an
existing attack unanswered; one was already forced before the final move.
These are descriptions, not proof of a specific faulty model or a reason to
add another penalty. Two of the fourteen paired histories diverged first in
Misty's action, so matching seeds did not eliminate all opponent variability.

This small, interrupted local panel does not prove the candidate worse in the
arena. It also does not justify calling it an established improvement. The
direct-v37 pilot remains visible alongside the negative transfer result.

## Review decision

The current plan withholds publication. Fable has the exact ZIP hash, source,
receipts and failed-game transcript; an independent ZIP acceptance has not
arrived. There are two explicit choices for the requested review:

1. Keep this candidate withheld and agree a distinct next implementation.
   Do not tune it on these same games or repeat the failed panel until it passes.
2. Authorize a separately labelled **experimental arena candidate** using these
   same validated bytes. Retain the failed gate, make no improvement claim, and
   predeclare the arena withdrawal rule before upload. Fable's proposed rule
   is immediate inspection for an own technical failure and withdrawal around
   40% score at 48 games against the v37 reference pace of 54.3%, with opponent
   versions and mix reported. That is an operational risk limit, not a formal
   sequential significance test or a promise of 2000 Elo.

Option 2 changes the release decision, not the test result. No such exception
has been assumed, and no new experiment, GPU job or arena upload is launched
by this review.

Evidence: [pilot](analysis/sf-allchildren-20261102/full-games/README.md),
[stopped opponent audit](analysis/sf-opponent-20261108/README.md),
[loss patterns](analysis/sf-opponent-20261108/stopped-explanation.md),
[package validation](analysis/v38-package-20261108/zip-validation.json),
[startup-failure probe](analysis/v38-package-20261108/failure-probe.json).

## Subsequent benchmark-adapter audit — 8 November, 16:04 UTC

The frozen local Misty wrapper contained the known action-list defect from
chatroom note 028: it generated ordinary pseudo-legal moves from a board with
hidden squares empty. On the 29 first attempts it supplied incorrect move
sets on 398/1,158 Misty turns (153/556 in the v37 arm, 245/602 in the candidate
arm). This is a defect in our integration, not an established defect in Misty
or evidence about its arena implementation. Wrong offered actions do not
prove they were chosen or explain the score difference.

All scores, faults, missing games and the failed admission decision above
remain unchanged. This finding limits the external validity of that opponent
comparison; it does not establish that v38 is stronger, nor retroactively
make its gate pass. The measured scorer speed and direct-v37 pilot are separate.

A corrected, separate observation-tracker adapter passes all 1,157 completed
recorded turns through its actual protocol loop and two real Misty turns per
color. The unanswered timeout turn is included in the 1,158-turn helper audit
but cannot be replayed as a completed actor response. Native Rust acceleration
is installed and now pinned; its binary hash was omitted from the old gate
manifest. No new strength panel has been started. See the
[audit and receipts](analysis/obscuro-fidelity-20261108/README.md).
