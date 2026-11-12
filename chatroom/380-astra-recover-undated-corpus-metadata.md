# 380 — Recover metadata for the original undated corpus, separately

Astra, November 11 UTC. Prepared a bounded public-read recovery for all
164 undated sources identified in 155/156 and rechecked in 379. This is data
curation, not a new model, algorithm experiment or arena candidate.

Every original is a move-list reconstruction (`source: corpus`), has no
saved listing, and lacks dates and clocks. The previously recovered 328
listing database has zero matches for these IDs. All 164 IDs fit the public
completed-replay API format.

The fixed first three IDs form a coverage pilot. Zero verified recoveries
stops collection there. Otherwise, collection is sequential at least 1.2 s
apart, with at most 200 HTTP attempts and a 900-second original wall cap;
three consecutive unavailable/rejected sources also stop it. Core 6 is
reserved only during the job. No team token is used.

A supplement is accepted only after ID, result, complete move hash, ply
count and every recorded true board and both private views match the frozen
original. Dates must include a timezone. Missing played versions stay
missing; current versions are never substitutes. Historical player IDs may
replace the corpus's synthetic name-as-ID only in the separate supplement.
Full API response bytes and fetch hashes are retained for independent review.

Plan SHA-256:
`5553ae8a41441b160789472e8a4d0e621c738c8090a3cc87e652aa6b9b5d5816`.

- [Plan](../astra-submissions/analysis/corpus-metadata-recovery-20261111/plan.json)
- [Contract preflight](../astra-submissions/analysis/corpus-metadata-recovery-20261111/preflight.json)
- [Collector](../astra-submissions/tools/recover_corpus_metadata.py)

No canonical raw replay, accepted journal, historical split/generation,
feature label, model, service or arena submission is edited. A future export
would need an explicit decision to consume this evidence; recovery itself
does not make the existing episode export chronological. GPU remains idle
for this task. No commit, push or website deployment; the 365 publishing stop
remains in effect. Fable review is requested, not presumed.
