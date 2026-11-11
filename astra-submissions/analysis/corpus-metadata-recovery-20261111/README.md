# Original corpus: dates recovered, team-attribution defect identified

November 11 UTC. All **164** undated corpus imports now have separately
verified public replay responses. The canonical raw replays, accepted journal,
existing episode shards and their splits are unchanged.

| Check | Result |
| --- | ---: |
| Planned / retrieved / identity-matched games | 164 / 164 / 164 |
| Positions with identical ply, move, true board and both views | 14,228 |
| Historical played versions recovered | 328 |
| API clock pairs now cached | 14,228 |
| Games actually involving IAmAVirus | 28 |
| Games incorrectly attributed to IAmAVirus by the importer | 136 |
| Synthetic name-as-player-ID fields replaced in the supplement | 328 |

All games completed on **October 7**, between 03:39:49 and 06:03:57 UTC.
Original nanosecond timestamps remain in the saved responses and supplement.
Every selected corpus seat lost; this is an intentionally selected tactical
benchmark, not a representative sample of either the arena or our results.

## Cause and concrete example

[`harness/corpus_download.py`](../../../harness/corpus_download.py) stores
an arbitrary selected seat, its opponent's name and the moves. It omits the
selected player's identity. [`learning/ingest.py`](../../../learning/ingest.py)
nevertheless names that seat IAmAVirus and uses team names as player IDs.
That inference is unsupported by the corpus format.

For `13r3tgga`, the imported label is Knight Vision–IAmAVirus. The public
response identifies **Knight Vision v26–TA Baseline P v5**. All 45 recorded
positions, moves, observations and the result agree. For `1b8luqb3`, the real
players are **duck v4–Greek Gift v16**, rather than IAmAVirus–Greek Gift.
The other player's recorded name matches in all 164 games.

The boards, moves and result direction survived the import. Team attribution
and IDs need correction. The 136 false attributions are about 0.058% of the
233,482-game snapshot; this finding does not explain our Elo gap or prove
that a particular deployed fit used these records.

## Execution and saved evidence

Original session **61530** exits zero after **204.49 seconds**, within its
900-second cap. It made 167 HTTP attempts for 164 successful responses,
downloaded 4,091,778 bytes and released core 6. The fixed first-three pilot
passed; no restart or replacement cohort was used.

The collector requires exact ID, result, complete move hash, frame count and
every recorded board/view. Independent verification also compares the original
corpus lines, checks all source/response hashes, reviews timezone and played
version fields, and confirms finite API clock pairs. This is a provenance
comparison with saved records, not a fresh rules or clock-consumption audit.

Private reusable cache:
`data/astra-spool/corpus-metadata-recovery-20261111/`:

- `originals/` and `sources.json`: frozen accepted source bytes and identity.
- `responses/`: exact API response bytes.
- `receipts.jsonl`: URL, fetch time, attempts, content hash and identity result.
- `supplement.json`: historical dates, versions, real IDs and names, rules and
  clock configuration, bound to both original and response hashes.
- `attribution-corrections.json`: each selected seat's original and real team.

No `CurrentVersion` field is consumed. A missing played version would remain
missing; these 328 historical values happen to be available.

## How to use this finding

For a **future separately identified generation**, explicitly overlay the
verified metadata or use the matched API copies for these 164 games. Keep the
original source hash and the augmentation hash in that generation's provenance.
That can remove the known missing-date fallback and correct team filters.
No existing split becomes chronological merely because this sidecar exists.
Do not move already-used examples to a new fold and call them unseen.

The [isolated importer patch](../corpus-attribution-fix-20261111/README.md)
prevents future name invention when importing this incomplete format. It does
not silently rewrite an accepted record or reconstruct an unknown identity.
Fable still needs to review shared integration and any future export.

[Plan](plan.json) · [Contract preflight](preflight.json) ·
[Execution](execution.json) · [Result](result.json) ·
[Independent review](review.json) · [Attribution reduction](attribution-summary.json) ·
[Collector](../../tools/recover_corpus_metadata.py) ·
[Verifier](../../tools/verify_corpus_metadata.py).

No model, table, training run, match, arena version, service, commit, push or
website deployment changed. The existing deployment stop remains in force.
