# V38 — faster all-child scoring, experimental arena release

**Uploaded by Henry on 8 November 2026; active as arena version 38.** This
record publishes the exact reviewed bytes under their numbered repository
name. It is not a rebuild or a second upload.

- Archive: [iamavirus-v38-mist-c-allchildren.zip](iamavirus-v38-mist-c-allchildren.zip)
- Uploaded-name alias: v38-review.zip
- SHA-256: ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f
- Size: 84,989,047 bytes
- Parent: Fable v37, SHA-256 41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c
- Arena creation: 8 November, 11:30:06 a.m. Boston time (16:30:06 UTC).

The public API confirms the assigned version and creation time, but does not
expose uploaded ZIP hashes. The bytes-to-version mapping rests on Henry's
upload statement and Fable's recorded same-archive decision. The original
archive's embedded candidate status is preserved; this external release record
and [manifest](v38-manifest.json) record the subsequent decision.

## What changed and why it shipped

The native C engine, fitted move model and history table match exact v37.
Only the playing launcher and Stockfish binary change: the launcher enables
the modified depth-one all-child scorer. The archive also includes its source,
licence and an offline rebuild recipe. Scoring throughput is 1.57–1.68× the
reference, producing about 38% more search nodes at equal time in the measured
panel. Scores are not identical; this is an approximation.

The direct-v37 development pilot scored 11W–1D–4L. The subsequent local Misty
gate failed: clean candidate 9/14 points versus control 10½/14, with an extra
opponent timeout and three unstarted games. A later audit found an action-list
defect in our local Misty wrapper. Neither that defect nor the arena results
rewrite the failed local gate.

Fable independently accepted these exact package bytes after extraction,
hash/build checks and four referee games, including the scorer-failure path.
Henry then approved an explicitly experimental arena trial and uploaded it.
This is a separate release decision, not a gate-passing promotion. See
[Fable's acceptance](../chatroom/267-fable-v38-zip-acceptance-and-recommendation.md)
and the original [review](v38-review.md).

## First arena decision

At the 9 November, 3:45 p.m. Boston snapshot, v38 had **179W–12D–127L / 318
games, 58.18% score**, Elo 1915.34, rank 10 among visible rated teams.

The predeclared checkpoints both permit retention:

| First games | W–D–L | Score | Predeclared rule |
|---|---|---:|---|
| 48 | 30–1–17 | 63.54% | z = +1.28; withdrawal was z ≤ −2 versus 54.3% |
| 300 | 170–10–120 | 58.33% | Retain if score ≥ 54.3% |

No recorded loss is a timeout, crash or illegal move. The sole time-forfeit
game was a win over Next; public diagnostics identify Black, Next, as the
side that timed out. These are operational retention criteria, not a test
proving an Elo gain. The historical 54.3% reference remains fixed; v37's final
2,322-game score is 53.90%.

Against the same opponent IDs, played versions and our colors, 242 v38 games
score 58.26%; reweighting v37's records to those cells gives 52.18%. The other
76 games have no matching baseline cell. Historical comparison, small cells
and changing opponents prevent a causal claim. [Full checkpoint and evidence](analysis/v38-arena-20261109/README.md).

**Recommendation: retain v38 and continue monitoring.** Duck v11 and Greek
Gift v25 remain the clearest measured weaknesses. The campaign continues;
there is no claim that this release reaches the 2000-Elo objective.

## Later follow-up — November 11

Fable's 03:27 UTC reading records **339W–27D–254L / 620 games**, 56.9%,
with no technical losses. After the first 127 games, the later 493 play
approximately at v37's historical same-opponent level. The keep decision
remains operational; the record does not establish a lasting strength gain.
[620-game follow-up](../fable-submissions/analysis/v38-arena-20261108/result.md).

The local [release-record reconciliation](analysis/presentation-audit-20261111/release-record-review.json)
verifies all member hashes, the staged upload alias, the unchanged parent
native source/history and the shared version-map entries. The original
archive, manifest and dated checkpoints above are preserved. This follow-up
is documentation only: no rebuild, new upload or version reservation.
Website publishing remains disabled.
