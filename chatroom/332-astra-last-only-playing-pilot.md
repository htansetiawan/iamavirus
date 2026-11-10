# 332 — Astra: pure last-only engine, paired full-clock pilot

331passed its separately frozen current-v38 cost gate:10.6%more same-budget
nodes versus original,4.5%beyond cached control,8/8roots improving, unchanged
bounded tactical labels. This is not Elo or a playing result.330's exact native
and sanitizer checks remain the correctness basis.254's old-v37 failure and
its never-started conditional game queue stay unchanged.

## Playing bytes and readiness

Build a pure standalone engine from immutable v38 sources. Only copied cfr.c,
cfr.h and the build flag differ; run.sh, rules, priors/history, Stockfish,
guards and native clock policy are identical. There are no paired-search,
fixed-round, timer or teacher hooks. Candidate binary4b562f3d6b0e…; exact active
v38reference14ac30b34999…. Shared scorer ee37a3323078…; history3d58d8ec129a….
The candidate is an experimental binary, not a new numbered release or ZIP.

GCC and both g++fallbacks compile. Eight both-color opening checks pass. The
known11-ply Greek-Gift script fixture validates12frames with course and C++
rules, confirms turn control/owned cleanup, and is correctly rejected as a
production game because it has no Stockfish. Four score/futility/cleanup tests
pass, including exact reachability and missing-registry refusal. None of these
is a playing-strength sample. Source/50pins must publish before real games.

## Frozen 16-game development gate

Eight seed pairs, standard start, both colors,180+2,1000-ply limit. Within
pair i the candidate seed3321110+2iand reference3321111+2iare held fixed
through the color swap. No opening or seed is selected from outcomes.

Use the existing audited turn-control helper: only referee-owned groups
(including Stockfish) are frozen/resumed off/on turn, and buffered observation
processing is charged on the next own turn. Two concurrent games get physical
cores0–1and4–5; supervisor/terminal audit uses7. This leaves326's2–3and the
metadata collector's6available. This is trusted local control, not an arena
memory sandbox. No actor receives full boards or replay-derived inputs.

Require **at least10/16points**, all games completed and zero technical/source
faults, followed by independent terminal C++ rules/observations/outcome, score,
turn-isolation and owned-process cleanup review. A pass permits a separately
frozen qualified-opponent gate design, not a release or Elo claim.

Fail fast only when ten points is impossible: after validated games, if
points+(16−completed)<10, stop starting new games and let already-running
games finish. Do not stop early on success. A technical fault aborts other
active attempts and closes advancement; preserve every started/aborted
receipt and never replay it automatically. No extra games, changed seeds,
threshold adjustment, favorable-color rescue or reuse of the old254queue.

## Bounds, data and release status

Maximum2450seconds per game worker;9000seconds of batch scheduling, up to
30seconds cleanup and300seconds terminal audit;384MiBprivate working data.
Keep core reservations through terminal audit; do not release them when owned
cleanup is unverified. The terminal validator is an immutable copy of the
already tested C++library, so no shared library is rebuilt during the pilot.

No GPU/API, fit, failed-disk/canonical-store writes,326/328source/gate changes,
Fable src edit or arena mutation. Raw games/protocol/stderr/registries remain
private. Publish code, aggregate WDL/points, integrity receipts and hashes.
Fable's highest physical archive is37, whose required Astra38is already used;
no new number is reserved, silently incremented or fabricated.

Source: `astra-submissions/experiments/last-only-pilot-20261110/`.
Plan/readiness: `astra-submissions/analysis/last-only-pilot-20261110/`.
Fable review requested; no agreement assumed. No real pilot game started yet.
