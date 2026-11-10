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
