# Astra experiment: infer en passant from the observation signal

2026-10-25. This is a move-generation correctness experiment against the
read-only v35 archive. It is not packaged, submitted, or an Elo claim.

## Finding

The v35 `view_moves` helper adds an en-passant action only when the adjacent
captured pawn is not attacked by any of our pieces. That misses a legal capture
when the pawn is already visible for another reason, even though the empty
capture destination is visible because en passant is available. The archived
referee confirms that the destination is added to the observation for a
pseudo-legal en-passant move, and that UCI input is accepted only if it is
pseudo-legal in the true position (`FowBoard.parse_uci`).

The bot first builds its safe `allowed` list with `view_moves`. At final move
validation, it accepts a move missing from that list only when the belief is
not overflowed and the move is legal in every belief board. With an overflowed
belief, an otherwise valid move omitted by `view_moves` is replaced by a move
from the allowed list. The omission therefore matters most when belief support
is capped or fallback logic uses this list; exact-belief decisions have an
additional legality check.

## Candidate change

The patch records the destinations already visible through ordinary legal
moves from the observation. It infers an en-passant action when the adjacent
enemy pawn is visible, the destination is visible and empty, and no ordinary
move could have revealed that destination. This is conservative: an unknown
intermediate square can prevent inference, but cannot create a false action.
The original captured-pawn visibility inference remains in place.

The patch is [belief-ep-observation.patch](belief-ep-observation.patch). It is
applied only to a temporary extraction of the v35 archive by
[`run_audit.py`](run_audit.py); the Fable archive is never modified. The audit
fixture reproduces v35's old `view_moves` and compares it to the patched
function on identical sampled positions.

## Result

Command: `python3 astra-submissions/analysis/ep-target-inference-20261025/run_audit.py --games 2500 --seed 1332956945`

| Measure | Result |
|---|---:|
| Random legal playouts / positions | 2,500 / 264,896 |
| True legal en-passant actions | 1,195 |
| Omitted by v35 `view_moves` | 655 |
| Recovered by patch | 554 / 655 (84.6%) |
| Still omitted | 101 |
| Baseline extra illegal candidates | 0 |
| Patched extra illegal candidates | 0 |

Of the 1,195 en-passant opportunities, removing the right while holding the
board fixed left the **current observation** unchanged in 101 cases and changed
it in 1,094. This does not determine whether the complete observation/action
history distinguishes those 101 cases; the engine tracks history and a full
belief. The random legal playout distribution is a rules probe, not a sample
of arena policy decisions. Zero false additions in this finite fixture is not
a proof over all positions.

The patched v35 archive builds successfully with its included `build.sh` and
GCC. Patched binary SHA-256:
`9a174cbd966f14b296896a233eb90a9f041c484eb2305d4fe7114377012d3d9e`.
The input v35 ZIP SHA-256 is
`24791ca64a429f5ae931466ce3c1af36c6974e1295203e99a00a991976955b4c`.

An archive-based exact-replay check is reproducible with:

```sh
python3 astra-submissions/analysis/ep-target-inference-20261025/check_replay_ep.py
```

It extracts v35 into a temporary directory, compiles the original and patched
`view_moves`, reconstructs castling rights from each replay prefix, and checks
the six recorded pre-move observations. Baseline availability was 2/6; patched
availability was 6/6. Per-game results are preserved in
`replay-case-check.json`. This confirms action availability on those six
observations; it is not a game-strength test.

## Decision-path pilot

The replay-prefix decision probe is reproducible with:

```sh
python3 astra-submissions/analysis/ep-target-inference-20261025/compare_ep_decisions.py \
  --seeds 20261025 20261026 20261027 20261028 20261029 --search-seconds 0.25
```

It compiles the original archive and a patched copy, feeds each bot the replay's
observation on every ply (clock only on its turns), forces only its earlier
recorded moves, and lets both versions choose at the target decision. Across
six positions and five seeds, the chosen move differed in 5/30 comparisons, all
at `8wef0oiw` ply 64. Original v35 chose `g4g3` 5/5 times and rejected `g4h3` at
final view-list validation; patched v35 chose `g4h3` 5/5 times. Of the other
three omitted-move positions, two did not select the EP action and one was
already recoverable through exact-belief legality. The recorded `g4h3` line is from
Instructors' win over Strongly Invisible, and the subsequent recorded line
preserves a passed pawn that advances toward the king. This is a useful,
repeatable tactical action change, but replaying the historical continuation
does not prove the alternative caused the win or that the patch raises Elo.
Raw output is in `decision-comparison-5seeds.json`.

## Cached top-opponent replay census

I scanned the local public replay cache for the leading teams, then verified
candidate EP coordinates against the true before/after replay boards. Of
123,251 cached games matching the top-opponent name filter, 91,972 included a
diagonal pawn move on an EP rank; board-transition checks identified 8,056
actual EP actions across 7,827 games.

| Measure | v35 | Patched |
|---|---:|---:|
| Actual EP actions present in `view_moves` | 3,329 / 8,056 | 7,431 / 8,056 |
| Actual EP actions omitted | 4,727 (58.7%) | 625 (7.8%) |
| Baseline omissions recovered | — | 4,102 / 4,727 (86.8%) |

The omission appeared in winning, losing, and drawn replay seats: among the
8,056 EP actions, the mover eventually won 5,398 times (2,842 omissions
recovered), lost 2,359 times (1,115 recovered), and drew 299 times (145
recovered). This supports a broad action-coverage defect; it does not show that
the omissions caused those outcomes.

Selected counts by moving top bot:

| Bot | EP actions | v35 omitted | Patch recovers | Still omitted |
|---|---:|---:|---:|---:|
| Strongly Invisible | 1,806 | 1,166 | 1,020 | 146 |
| Instructors | 1,550 | 942 | 840 | 102 |
| Knight Vision | 1,331 | 765 | 646 | 119 |
| Decent Chess Bot | 631 | 348 | 320 | 28 |
| Greek Gift | 426 | 262 | 221 | 41 |
| duck | 380 | 251 | 205 | 46 |

The 8,056 derived event rows preserve game ID, side, ply, action, observation,
result, and original/patched availability in
`top-opponent-ep-action-coverage.jsonl`; aggregate counts are in
`top-opponent-ep-coverage-summary.json`. This is cached public replay data; the
analysis did not query the API. The six exact replay cases and the seeded
random legal-playout audit separately check the inference logic. The corpus
probe only tests whether each recorded true EP action is present; it is not a
full false-positive audit, and 625 actions remain absent from the current-view
candidate list.

### Full legal-move-set replay audit

To check both omissions and false additions, I replayed `view_moves` against
the true board at every frame of those same games. This compares the
observation-derived candidate set with the referee engine's pseudo-legal move
set at each position, including all moves that were available but not chosen.
The archive-based audit is reproducible with:

```sh
python3 astra-submissions/analysis/ep-target-inference-20261025/audit_replay_move_sets.py \
  --out astra-submissions/analysis/ep-target-inference-20261025/top-opponent-replay-move-set-audit.jsonl.gz
```

| Measure | v35 | Observation patch | Observation + history |
|---|---:|---:|---:|
| Replay games / positions | 7,827 / 737,730 | same | same |
| Positions with an EP right | 54,213 | same | same |
| False candidate moves | 0 | 0 | 0 |
| Missed legal EP moves | 5,179 | 657 | 438 |
| Missed non-EP moves | 0 | 0 | 0 |

The observation patch makes 4,522 additional legal EP actions available. The
history extension adds a second proof from consecutive views: the prior
same-side observation shows an enemy pawn on its home square and its transit
and landing squares empty; after the opponent's one move, that pawn is visible
on the landing square. The referee sends a view after each ply, so the bot has
this immediate before/after pair. This extends the candidate set by 1,337
actions in the corpus; all 1,337 correspond to true EP rights. Of these, 219
were absent from the observation-only list. The combined helper therefore
makes 4,741 additional legal EP moves available (91.5% of v35's omissions),
with zero false candidates observed in all 737,730 positions. It still misses
438 legal EP actions. The compiled helper result is in
`top-opponent-replay-history-move-audit.summary.json`; the observation-only
position rows remain in `top-opponent-replay-move-set-audit.jsonl.gz`.

On the 8,056 actual EP actions played in those games, the observation patch
left 625 unexposed; the history proof covers 210 more and leaves 415. The
joined action rows and by-team/outcome summary are
`top-opponent-ep-history-event-coverage.jsonl` and
`top-opponent-ep-history-event-coverage.summary.json`. These are finite
replay/action-coverage results, not a strength or Elo estimate. Zero false
candidates in this corpus is strong finite evidence, not proof over all
possible positions.

The candidate implementation is reproducible without editing Fable's ZIP:

```sh
python3 astra-submissions/analysis/ep-target-inference-20261025/apply_ep_history_candidate.py \
  --source-root /tmp/iamavirus-v35-ep-history
bash /tmp/iamavirus-v35-ep-history/build.sh
```

`audit_ep_history_engine.py` extracts the untouched v35 archive to a temporary
directory, applies the current-view and history changes, compiles the helper,
and checks every replay position against the true board. It is the source of
the compiled-helper counts above.

The full v35-derived candidate also built and completed a 20-ply local
referee protocol smoke against `baseline.py` at 3+0. There was no illegal move,
forfeit, or process failure; the referee stopped at the configured move limit.
Replay: `protocol-smoke-20plies.json` (24,644 bytes). This is a protocol smoke,
not a strength comparison.

The full-clock strength gate is a resumable, color-swapped 20-pair comparison
against unchanged v35. Its runner writes a manifest after every game and saves
each replay separately:

```sh
taskset -c 4,5 /home/henrytan/git/fow-starter/.venv/bin/python \
  astra-submissions/analysis/ep-target-inference-20261025/run_ep_history_paired_gate.py \
  --candidate /tmp/iamavirus-v35-ep-history \
  --baseline /tmp/iamavirus-v35-ep-history-base \
  --referee /home/henrytan/git/fow-starter/referee.py \
  --out astra-submissions/analysis/ep-target-inference-20261025/v35-ep-history-paired-20pairs-seed20261080.json \
  --pairs 20 --seed 20261080
```

The match pair owns cores 4–5 while the separate king-guard screen owns 6–7.
Neither screen uses the GPU.

To regenerate the corpus event set, first create the cached top-team filename
list and the cheaper diagonal-pawn prefilter, then run the two scripts:

```sh
rg -l --glob replay.json '"(white|black)"\s*:\s*"(Greek Gift|Instructors|Knight Vision|Decent Chess Bot|Strongly Invisible|duck|TA Baseline [ASP])"' data/raw/games > /tmp/top-team-games.txt
xargs -d '\n' -n 250 rg -l --no-messages --glob replay.json -e '"move"\s*:\s*"(a5b6|b5a6|b5c6|c5b6|c5d6|d5c6|d5e6|e5d6|e5f6|f5e6|f5g6|g5f6|g5h6|h5g6|a4b3|b4a3|b4c3|c4b3|c4d3|d4c3|d4e3|e4d3|e4f3|f4e3|f4g3|g4f3|g4h3|h4g3)"' < /tmp/top-team-games.txt | sort -u > /tmp/top-team-diagonal-pawn-games.txt
python3 astra-submissions/analysis/ep-target-inference-20261025/scan_top_opponent_ep.py --files /tmp/top-team-diagonal-pawn-games.txt --out /tmp/top-team-ep-events.jsonl
python3 astra-submissions/analysis/ep-target-inference-20261025/check_ep_event_corpus.py --events /tmp/top-team-ep-events.jsonl --out /tmp/top-team-ep-coverage.jsonl
```

## Multiagent implication and next gate

This is a concrete example of why move generation belongs to the information
model: a move's availability can depend on an en-passant right that may not be
obvious from one observation. `gtcfr.c` expands each sampled world with
`generate_moves` on its full board. Its information-set map keys on the acting
player's observation/action-history hash, then handles a same-key action-count
mismatch by creating a separate information set. That is a possible strategy
fusion path if the *full* acting-player histories do not reveal the right. This
random-position audit does not prove that such full histories occur in the
actual tree; construct and test those histories before claiming a CFR defect.

Next, test patch integration against exact referee positions and archive
protocol, then run a bounded full-clock paired gate only after the existing
v35/v36 king-guard run frees cores. Also add an exact-belief case where all
boards agree on en-passant legality and an overflowed-belief case where the
observation/history proves it. Keep guard and EP arms separate so any result
remains attributable.

No release ZIP was changed and no arena version was reserved for this idea.
