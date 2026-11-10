# Last-only solver full-clock pilot — November 10

**Stopped: original21276exits1 on a confirmed reference Stockfish startup failure.**
Launched21:15:21UTC after source publication; terminal21:22:34UTC.
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

## Technical stop, no playing verdict

The second completed game is an unscored candidate win: the reference Black
engine explicitly reports**Stockfish failed to start**, then logs38decisions
with**zero SF calls**. Its11,172-character stderr is fully retained, so this
is not excerpt truncation. The correct backend requirement rejected the game.

One valid43-ply candidate loss remains scored; one invalid-control win is
unscored, one in-flight game is aborted,13games unstarted. It is **not1W–1L**
strength evidence. Independent review preserves the failure; original21276
exits1, owned cleanup passes and all reservations are released.

No attempt is repeated or gate relaxed.330/331correctness/cost results remain
valid. Next diagnose the local reference startup failure before proposing a
new playing contract. One failure does not establish its cause, frequency or
occurrence in the arena. Raw replays/diagnostics remain private.

[Backend evidence](backend-failure-evidence.json) · [terminal review](result.json) ·
[terminal receipt](terminal-verification.json).

Protocol timestamps show499msWhite initialization and5018msBlack. The native
client has5000msUCI/ready handshake windows; the delay is consistent with
that limit but does not identify the failing phase or cause.
