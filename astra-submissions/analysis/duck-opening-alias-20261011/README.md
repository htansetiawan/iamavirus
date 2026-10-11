# Duck opening: incompatible escapes behind the same observation

Astra, 2026-10-11. These are offline referee oracles and C conformance checks,
not a new playing policy or an Elo estimate.

## What the two public games establish

Arena games `9pl31sez` and `burzt1so` are IAmAVirus **arena v30** as White
against duck v5. Both end after exactly the same moves:

```
1. e4 d5 2. exd5 Qxd5 3. d4 Qa5 4. Be3?? 0–1
```

The cached full boards, both observations at every ply, legal moves and final
result were reconstructed with the official referee. The two games have
**one unique board-observation/own-action history** through the fatal decision;
they are repeated evidence of one family, not two independent tactical cases.
Clocks are excluded from that history signature.

At White's fourth decision, Qa5 attacks e1 through b4, c3 and d2. All those
intervening squares are empty, and the queen's square is hidden. Seven legal
replies survive on that actual board. However, replaying *alternative legal
Black moves from the recorded preceding board* produces eight destinations
with exactly the same White observation:

```
Qd8, Qd7, Qe6, Qd6, Qc6, Qf5, Qa5, Qe4
```

These are only a subset of history-consistent states; we did not reconstruct
the full belief or assign opponent probabilities. The queen's departure from
d5 changes the observation. Its hidden destination is ambiguous; this is
not a claim that the opponent caused no visible change.

| Hidden attack | Safe next White moves |
| --- | --- |
| Qa5, diagonal into e1 | Nc3, Nd2, b4, Bd2, c3, Qd2, Ke2 |
| Qe4 or Qe6, file into e1 | Be3, Qe2, Kd2, Be2, Ne2 |

The two sets are disjoint. Every world individually has an escape, but a
deterministic strategy receiving this observation cannot guarantee survival
against both. For any randomized reply, at least one of these two worlds has
survival probability at most 1/2: the probabilities of two disjoint escape
sets sum to at most one. That is a worst-case bound, not a measured duck rate.

This also cautions against blindly minimizing unweighted immediate risk:
Be3 survives **7/8** of these worlds; Nc3 survives **6/8**. A uniform-count rule
can prefer the move duck actually defeats. Eight equally enumerated worlds
are not evidence that duck chooses them equally often.

## Move the decision earlier

The next oracle enumerated **all 29 legal third moves**, every legal Black
reply, then White's immediate responses. Black replies are grouped by the
observation White would receive. One common safe response must exist within
each group; different responses selected separately for hidden worlds do not
constitute an executable strategy.

- **d3 and d4** each produce a group with incompatible escapes, although
  every individual world has a surviving reply.
- **Ke2** permits a physically forced loss at this horizon.
- The other **26 moves**, including Nc3 and Be2, permit a safe response for
  every nonterminal observation group from this recorded starting board.

Nc3 develops a piece and interposes on the diagonal; Be2 closes the e-file.
This does not rank all 26 remaining moves, prove they are safe on every
history-consistent starting board, or establish long-term strength. It
isolates an earlier information problem that inspecting only the fatal move
would miss.

## Implemented C component

Published in `htansetiawan/mist-c`, branch `astra/m4`, commit
[`9fb3d30`](https://github.com/htansetiawan/mist-c/commit/9fb3d302552236cdc3845d3cc478a8a07dfb4622):

- `src/m4escape.c/.h`: bounded hash table keyed by own history, exact view,
  side and own castling rights; sorted escape-set intersection per group.
- `tools/escape_probe.c`: offline stdin adapter for complete-board tests.
- `tests/test_m4_escape.c`: disjoint escapes, color reflection, history/rights
  separation, duplicates/order invariance, physical loss and capacity handling.
- `docs/M4_ESCAPE.md`: contract, complexity, limitations and integration path.

No model or Stockfish is required. Storage is bounded; expected lookup is
O(1), move ordering O(A log A), and intersection O(A), with at most 256 moves.
Capacity failure marks the audit incomplete. Caller-provided history must
preserve perfect recall; hidden move names must not separate indistinguishable
states. Historical repetition terminals must be filtered by the caller.

**C agrees with the independent Python referee on all 1,307 nonterminal
successor boards in 537 observation groups across the 29 candidates.** Unit,
AddressSanitizer, UndefinedBehaviorSanitizer and LeakSanitizer checks pass.
This is conformance for the specified family, not performance or strength.

The component is **not linked into the playing engine**. The active M4 gate
still uses executable SHA256
`1afb58d207a6bc4f292909d4575d5ca1b4179448f297942f1c8a10ca72baa191`,
from source a97a1d5. Fable's active engine files were not changed.

## Artifacts and reproduction

- `cases.json`: both validated public replays' history signatures, observation
  alias class and immediate escape labels; source hashes retained.
- `earlier-all-summary.json`: complete candidate summary plus conflict/forced
  groups, with paths/hashes for the full world listings on Seagate.
- `c-referee-conformance.json`: C/referee comparison and binary/source hashes.
- `public-protocol-provenance.json`: cached replay plus newly fetched, public,
  complete 33-event protocol for `9pl31sez`. No private diagnostics are used.

The exploratory three-move report and full all-move report live under:

```
/media/henrytan/seagate/iamavirus/astra/m4-gate-20261011/duck-openings/
```

```sh
/home/henrytan/git/fow-starter/.venv/bin/python \
  astra-submissions/tools/replay_alias_audit.py \
  data/raw/games/9pl31sez/replay.json data/raw/games/burzt1so/replay.json \
  --ply 6 --side white --out /tmp/duck-alias.json

/home/henrytan/git/fow-starter/.venv/bin/python \
  astra-submissions/tools/replay_information_traps.py \
  data/raw/games/9pl31sez/replay.json --ply 4 --side white \
  --out /tmp/duck-earlier.json

/home/henrytan/git/fow-starter/.venv/bin/python \
  astra-submissions/tools/check_escape_sets.py \
  data/raw/games/9pl31sez/replay.json /tmp/duck-earlier.json \
  --binary /tmp/mist-c-astra-m4/build/escape_probe --out /tmp/duck-c-check.json
```

## Next measured use

The **16-decision cold/warm probe completed** at 08:49:26 UTC. Its frozen
manifest and full receipt snapshot are in `prefix-pair-final.json`; process
logs remain on Seagate. All prefixes and chosen moves validate, with no
reported M4 overruns or Stockfish request failures.

| Decision | Cold internal | Warm internal | Cold Stockfish | Warm Stockfish |
| --- | --- | --- | --- | --- |
| Third, before historical d4 | Be2 / Be2 | Nc3 / Nc3 | Qe2 / Qe2 | Qe2 / Be2 |
| Fourth, after historical Qa5 | Ne2 / Ne2 | Ne2 / Ne2 | Be3 / Be3 | Be3 / Be3 |

Each cell lists seeds 11/12. All third-decision choices are among the 26
moves with a shared safe reply in each tested future observation group.
All fourth-decision choices lose to the actual Qa5. The belief then contains
all eight possible queen destinations, including the true board with
posterior mass .12344; root truth is present in every run. This is not a
missing-attacker failure.

Warm search carries one root at decision three. At decision four it falls
back because the forced historical d4 had zero own reach in the previous
blueprint. These are searched **forced prefixes**, not on-policy games.
Consequently the result does not show that carry would fail following the
moves M4 actually wanted to play. It demonstrates why forced-prefix results
must retain the carry/fallback diagnostics.

For a later runtime experiment, the C primitive can label unresolved future
information sets for expansion priority, or provide a training target for
an observation-history representation. The policy must receive belief/search
states only. A true-board oracle label is never a forward model input.
Adding a universal penalty or a named-player opening override would need
separate evidence; neither was implemented here.
