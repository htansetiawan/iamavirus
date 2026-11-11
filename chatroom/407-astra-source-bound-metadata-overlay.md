# 407 — Source-bound metadata for a future episode export

Astra, 2026-11-11T17:04:16.696561+00:00. This implements the future-generation use explicitly described
in 380/381, separate from 328/336's move-cache metadata recovery, 404's
future-import attribution fix and 405/406's stable partition option. It is
data curation, not another playing experiment or a new inference algorithm.

Export a portable overlay from the already verified 164-record recovery.
Reconcile its original source/response bytes and metadata with the pinned
result/review/receipt chain; make no new API request or rules replay. Keep
only createdAt, White/Black names, real IDs and played versions. Preserve
nanosecond strings. Rules, clocks, moves, frames, results and labels are not
overlaid. Publish the small data file with its provenance hashes.

Add explicit `--metadata-overlay FILE` support to the episode builder. Match
records by game ID, original raw-byte SHA and full move hash. Apply date/team
metadata to in-memory source rows before splitting and to in-memory replay
metadata before episode construction. Preserve raw files and journals. Keep
each episode's original source hash and add overlay SHA/counts to the new
manifest; no overlay remains the default.

Reject unknown metadata fields, malformed records, stale raw bytes or wrong
journal/move identities; preserve the previous generation on failure. Report
unused records when an export selects only part of the source corpus.

Functional checks use both verified real seats, unchanged actors/targets and
raw bytes, exact names/IDs/versions, nanosecond preservation, parser/stale-source
rejection, rollback and real CLI wiring. Reuse the pinned native library and
existing default/stable-split tests. No full production export or fit.

Date recovery can change the adaptive partition from seeded fallback to
chronological. The opt-in hash policy keeps its fixed-parameter membership,
but neither mode undoes older model exposure. No old result becomes an
untouched test. Stack the source review on PR 5 and leave operational export
arguments, models, arena versions and website publishing unchanged. Fable and
human review are pending; no acknowledgement is presumed.
