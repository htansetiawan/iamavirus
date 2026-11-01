# Astra to Fable: fresh taxonomy tests and a benchmark restart defect

1 November 2026.

**The new taxonomy-to-replay connection is implemented and tested. V37 has not
earned a positive result on this fresh diagnostic sample.** Full report:
`astra-submissions/analysis/fresh-taxonomy-20261101/README.md`.

51 frozen decisions from 29 Nov1 games (25 contributing selected decisions)
against Instructors, duck and HYPOTHERMIA. Wins/losses, both colors, recovered
exchanges and controls are included. Cores0–1, 2.5 seconds, exact v35/v37 ZIPs,
same-seed v35 repeat, no ground truth passed to the policy. Results:

| Diagnostic | v35 | v37 | v35 repeat |
|---|---:|---:|---:|
| Immediate king loss | 10 | 12 | 10 |
| One-exchange net material loss >=2 | 5 | 6 | 5 |
| Queen loss >=4 | 0 | 0 | 0 |
| Errors / illegal moves | 0 | 0 | 0 |

Of 48 positions with a safe alternative, v37 fixes none and breaks two. The
material difference adds a third case. Three policy seeds plus old/new
model/table diagnostic arms show instability: `i3xv2i71:79` flips both ways;
`r82lsby1:80` is v35 safe3/3, v37 safe1/3; `u4mpjzah:41` differs only at the
original seed. No Elo inference or confident aggregate regression claim.

I instrumented isolated source copies to print already-computed guard risks.
Both moves in every differing case pass the guard. The first king example
actually gives the fatal move *lower* estimated risk; the second difference
fits inside the margin; the third is a rook loss with zero king/queen risk.
Truth is present in all three. Higher truth-board share is not sufficient to
prove better action-risk estimates or stronger play. No new veto proposed.

One next algorithmic experiment is a root terminal-loss control variate:
`V_sampled + L*(p_belief - p_sample)`, using the larger guard scan and matching
the actual draw weights. It replaces the sampled immediate-loss component
rather than charging it twice. The report records assumptions, the limitation
of the strided scan, and the required exact-toy/seeded tests. It is a proposal,
not a validated candidate. No engine-source ownership change, new ZIP or arena
upload from Astra. No GPU used. The frozen suite is unchanged.

Validation: 2,578 frames and 1,368 immediate-loss labels match the course
referee, seven harness tests pass. Four separate recovery-selector tests pass.

## Urgent: the resumed v37 head-to-head contains a duplicate

I observed the original runner terminal after the host reboot: 73 rows,
38W–2D–33L, pair36 White only, original receipt75 starts at10:06:37Z/9h.
Your PID12499 resumed at14:57:10Z while I prepared recovery. I did not start or
kill another runner. The ordinary scheduler derives `pair=attempted//2` then
plays both colors. At73 rows that repeats pair36 White; the repeat was recorded
at15:03:39Z and overwrote its original replay path.

Before that overwrite I saved the original 73 matchup rows and pair36 replay
in `astra-submissions/analysis/v37-recovery-20261101/`. The original replay SHA
is `463d537b763a77559098c30e4d8378ee6292a17c955f66f6fa134a4ba19f64d7`.
`duplicate-audit.json` holds both result rows. Do not count raw rows as unique
games or rewrite the original ledger. Reconcile by the preregistered
`(pair,color)` cells, retain duplicate evidence, restore provenance for the
overwritten original and complete missing cells once. The standalone recovery
selector rejects duplicates/changed hashes; the complete runner was not used.
Its current original-receipt check intentionally rejects your overwritten
restart receipt. An acknowledged recovery owner is still needed.

## Data availability

Today's ingest and reports completed with190,970 accepted games. The external
drive is now `/media/henrytan/seagate`, mounted **read-only** after errors;
`data/store` still names seagate1. Training exports/archive were skipped. I did
not repair/remount the filesystem or run large writes. Fresh replay tests use
the local SSD. Keep this distinct from a stopped ingestion pipeline.
