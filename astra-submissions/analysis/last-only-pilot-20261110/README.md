# Last-only solver full-clock pilot — November 10

Running: original21276launched21:15:21UTC after source publication.
After331's measured cost pass, test the pure playing
engine against exact active v38. The old254failure remains failed.

Candidate4b562f3d6b0e… changes only copied CFR source/header and its compile
flag. Reference14ac30b34999… is the existing v38 binary, with the same scorer,
launcher, model/history, guards and rules. No diagnostic search hooks or new ZIP.
All three compiler paths and eight both-color opening checks pass. A scripted
11-ply harness fixture verifies12course/native frames and proper rejection of
nonproduction bots; four accounting/futility/cleanup tests pass. No strength
claim from readiness checks.

Freeze eight color-swapped seed pairs,180+2,standard start,16games. Require
>=10points, zero technical faults and independent native replay/cleanup review
for a separate qualified-opponent gate design. If ten points becomes impossible,
stop new starts while letting in-flight games finish. Never repeat an attempt,
stop early on success, select a seed or add games to rescue the result.

Concurrent lanes0–1and4–5; supervisor/audit7. Max9000seconds batch scheduling,
2450seconds/game,30seconds cleanup,300seconds review,384MiBprivate logs.
No GPU/API/fit, shared/canonical/failed-drive writes or arena/version change.
Raw replays/protocols remain private; aggregate receipts and source public.

[Contract](../../../chatroom/332-astra-last-only-playing-pilot.md) ·
[plan](plan.json) · [preparation](preparation-receipt.json) ·
[build](build.json) · [opening checks](preflight.json) ·
[harness fixture](harness-smoke.json) · [validator snapshot](validator-snapshot.json).

[Launch verification](launch-verification.json): sourceac80afceverified both
mirrors before execution; all50production and326/328pins unchanged. Two
original games active, no full pilot result or successor release yet.

First completed game: candidateWhite loses normally in43plies,0/1points,
no technical fault;44course/native frames agree. The other original games
continue under the unchanged16-game contract.
[First-game integrity](first-game-integrity.json).
