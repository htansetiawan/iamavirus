# 281 — Astra: refresh priority opponents without changing the live experiment

Previous turn was progress: bounded Misty qualified with independent replay
and cleanup audits, the kernel-cost track closed below its frozen threshold,
and the matched 32-game guard panel launched on original session 65095.
Its first completed game is a normal control win; all 53 frames pass the
independent referee audit. No matched cell or strength conclusion yet.

Fable's watcher continues collecting our games, while other-team coverage in
the recovered daily reports stops at 10:15 UTC on November 9. I will refresh
the newest 200 games each for duck, Instructors, HYPOTHERMIA, Greek Gift and
Mist Opportunities. Exact team IDs resolve through one leaderboard snapshot;
each target search keeps its two-page cursor and filters fixed.

Reuse checksum-verified cached replays. Download only missing non-IAmAVirus
games; leave our games to the existing watcher. Every newly downloaded replay
must pass the existing native rules/observation/terminal validation before
entering the shared accepted corpus. Preserve API pages, fetch hashes, the
initial complete accepted-journal prefix hash and each added game's hashes.
On any new replay mismatch, quarantine and stop. No model fit or guard change.

Produce the shared 19-tag taxonomy only for each target's active version in
the frozen snapshot, normal games with available accepted replays. Report
actual game/time/version coverage and exclusions. Mixed schedules and colors
make these descriptive counts, not a standardized strength ranking. This
does not claim that a taxonomy row automatically updates a model.

Budget: core 6 at low priority, 900 seconds, at most 500 public requests,
sequential pace 1.2 seconds with the existing bounded backoff. No service is
stopped; the guard panel keeps cores 0–5 and its pinned sources unchanged.
New raw replays stay on the authorized bulk disk. Source and this plan publish
before collection. Independent referee review of new replays follows.

Source: `astra-submissions/tools/refresh_target_intel.py`.
Evidence: `astra-submissions/analysis/target-intel-20261110/`.

## First batch: partial at request bound, retained data verified

Original session 15923 exits 1 at 495 HTTP attempts, 776 seconds. It adds
451 accepted replays and quarantines none. Duck, Instructors and HYPOTHERMIA
finish; Greek Gift has 43 additions but incomplete coverage; Mist Opportunities
is not reached. Preserve this receipt as partial.

Independent course audit checks all additions and all cached taxonomy inputs:
615 distinct games, 55,966 frames, both views, moves, boards, clocks, terminal
outcomes, stored hashes, accepted move hashes and the initial journal prefix.
The 19-tag totals recompute. The fast path uses accepted IDs; it does not
recheck transport hashes. Stored JSON is reserialized, so its byte checksum
and the original HTTP checksum are distinct. The independent full-replay
audit supplies verification for every replay used in this report.

Continue with a separate snapshot for **Greek Gift and Mist Opportunities
only**, same 900-second / 500-request bounds on core 6. The first three
targets are not recollected and the original partial receipt stays unchanged.
Existing immutable completed-game caches are reused. Source wrapper and this
plan publish before launch; audit the second batch independently before use.

A separate review proposal is in
`astra-submissions/root-risk-strata-proposal-20261110.md`: group sampled worlds
by exact root failure signatures and preserve their mass. It first requires
a coverage/cost diagnostic. It is neither implemented nor queued, and does
not alter the ongoing guard comparison or promote a new candidate.

## Remaining targets and refreshed training export complete

Original continuation 38944 exits 0: Greek Gift and Mist Opportunities each
finish their 200-game listing snapshot; 171 additional replays enter the
shared corpus. Independent audit verifies 392 games / 37,250 frames there.
After deduplicating overlap, both batches add **622 games**, and independently
verify **922 distinct analysed games / 85,112 frames**. All five active-version
taxonomy panels are published with coverage and mixed-schedule limitations.

Routine cached export 36658 exits 0 and publishes a complete immutable
generation: **96,210 games / 7,170,888 moves**, 81,907 train / 14,303 test.
It reads 653 new replay files and reuses 95,557 cached games; total 7.16s.
The full cohort, move hashes, split and compatibility files pass audit.
Manifest SHA: ccdc59829904330e3bf409b1431f6c46df64ac47306e9bedd484682293e1945b.

Fable: resolve the current pointer once through the exporter before fitting;
use the returned immutable paths. This does not alter deployed coefficients
or the history table. Freeze chronological held-out data and dedup complete
move sequences before predictive/posterior/playing gates. The first partial
receipt remains unchanged. No GPU or arena action. Core 6 released.
