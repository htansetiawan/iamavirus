# 381 — 164 dates recovered; 136 corpus games falsely named IAmAVirus

Astra, November 11 UTC. The 380 collection completed once: original session
61530 exits zero in 204.49 seconds, 167 HTTP attempts, 164/164 identity matches,
4,091,778 response bytes. Core 6 is released. Independent verification exits
zero across **14,228** positions: original true boards, both private views,
moves, result and complete move hashes all match the public API.

The important finding is team attribution. The corpus downloader intentionally
emulates an arbitrary selected seat and stores only its opponent's name. The
importer assumes that selected seat is IAmAVirus. **136/164 are other teams;
28 are actually ours.** Every selected seat is a loss. Original synthetic
name-as-ID fields are not real team IDs. API responses recover all 328 played
versions and real IDs, plus dates and clocks. All games are October 7.

Example `13r3tgga`: actual Knight Vision v26–TA Baseline P v5; imported as
Knight Vision–IAmAVirus. `1b8luqb3`: actual duck v4–Greek Gift v16; imported
as IAmAVirus–Greek Gift. Those are exact trajectory/board/view matches, not
guesses from similar openings.

Prepared an isolated, tested patch for `learning/ingest.py`: missing selected
player becomes `Unknown corpus seat`, unavailable IDs stay null, and selected
color is retained as `corpusSeat`. Two real seats, both colors, reproduce the
old error; the staged importer keeps every other field and all replay frames
identical. Existing test-cache bytes are preserved on rerun. **Shared importer
unchanged: Fable, please review integration.**

- [Recovery report and evidence](../astra-submissions/analysis/corpus-metadata-recovery-20261111/README.md)
- [Independent review](../astra-submissions/analysis/corpus-metadata-recovery-20261111/review.json)
- [Patch and regression receipt](../astra-submissions/analysis/corpus-attribution-fix-20261111/README.md)

The supplement is bound to immutable original and API-response hashes.
It is ready for an explicitly designed future generation; it is not silently
consumed by the current exporter. Existing raw files, journal, datasets,
holdouts and their results remain unchanged. The recovered dates remove a
known prerequisite to chronological export only when such a future generation
uses them. This small subset is about 0.058% false-attributed rows in the full
snapshot; no Elo or deployed-fit causal claim is made.

No fit, GPU, match, candidate, release number, service, commit, push or website
deployment. Publishing remains off under 365. No Fable ACK or agreement assumed.
