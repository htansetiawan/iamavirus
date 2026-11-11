# November 11 incremental archive: replay coverage verified

The original refresh finished at 15:04:16 UTC with systemd exit status zero.
Its new archive, `daily-2026-11-11T1442Z.tar.gz`, is **163,956,013 bytes**.
The archive cursor advances from 195,614 to 234,942 journal rows.

Original audit session 66516 exited zero once, in 22.54 seconds under its
900-second cap. It streams the complete gzip file through EOF/CRC validation
and records its SHA-256:
`27ab9d4b99e6c70868d1d1855015588281bdadb9a2115eef0f4b040f7be26745`.
No files are extracted to the filesystem.

All **39,328 replay occurrences / 39,297 unique IDs** have the expected
multiplicity and full replay-content hash. Every reference comes from the
independently checked episode index; no separate raw-hash fallback was needed.
The 31 repeat occurrences preserve the source journal's historical duplicates;
they do not create duplicate-ID episode weights.

The archived journal's 104,270,050 bytes / 234,942 rows match the pinned source
prefix exactly, with zero rows beyond the recorded cursor. The stream covers
1,488,056,320 decoded tar bytes, 158,138 members and 412 snapshot entries. Its
snapshot frontier matches `2026-11-11T100543.191524Z0000`.

## Verification boundaries

Eight functional checks passed before the real scan, including actual mirror
output with duplicate records, truncated gzip trailer rejection, content/count
and journal/snapshot disagreement, byte budget and unsafe member paths.
The original stream pass checks the real archive's bytes and replay content.
A separate receipt review reconciles all replay hashes/multiplicities,
journal-prefix hash, cursor arithmetic, file identity/size and lease release.
That review is not a second tar scan.

[Plan](plan.json) · [Execution](execution.json) · [Result](result.json)
· [Receipt review](review.json) · [Runner](../../tools/audit_daily_raw_archive.py)
· [Stream checker](../../tools/check_daily_archive_stream.py)
· [Functional checks](../../tools/test_daily_archive_stream.py)
· [Receipt reviewer](../../tools/review_daily_raw_archive.py).

Private before/after state, pinned journal prefix, expected replay hashes and
stream receipts remain under `data/astra-spool/`. The raw inputs, original
archive and state file were read without alteration. The older archive chain,
every auxiliary cache file's equality to its raw counterpart and physical
device health are outside this verification. No model, engine, arena version,
service restart or website deployment was changed.
