# V38 review target: 8 November, Los Angeles

Requested by Henry on 7 November. Highest Fable archive is v37 at this check,
so the next Astra archive is v38; recheck immediately before packaging and
publication. This is a repository release for human review, not an arena upload.

The candidate keeps v37's C engine, learned opponent model and history table.
Its one change is a modified Stockfish 19 leaf scorer: one full-window root
pass scores all legal children with the existing NNUE and tactical search.
It saves repeated MultiPV work but changes pruning/history and therefore
scores; this is an approximation, not an exact algorithmic optimization.

Completed evidence:

- Full legal-move coverage and terminal/special-move checks; disabled controls
  match the shipped scorer. Official source, network and binary provenance pinned.
- Two frozen 256-parent comparisons, including actual search queries: approximately
  1.6–2.0x scoring throughput with accepted value/ranking differences.
- 51 same-belief, same-world, same-guard decision pairs: 38.4% more nodes at equal
  time; 12 versus 12 immediate king losses, 6 versus 5 bounded material losses.
- 16 full-clock games against exact v37: 11W–1D–4L, passing the 10-point pilot
  gate. Independent referee audit of 1,443 frames; no technical faults or reruns.

Remaining before handing over v38:

1. Matched Misty test: 32 games, 16 per arm, eight seed blocks and both colors,
   180+2. Candidate must score at least 8/16 and two points above v37. Preserve
   every result and audit them; no threshold or parameter change after seeing results.
2. Prepare a portable scorer package while games run, retaining source/licence
   and the exact NNUE. Check value/ranking parity against the tested scorer and
   measure the actual packaged binary. Keep the experimental bytes unchanged.
3. Validate the exact ZIP: build, start-up, both colors, protocol, clocks,
   memory, legal moves, source/model hashes and the required +1 numbering rule.
4. Publish the ZIP and release manifest to both repository mirrors with an
   honest evidence summary, arena prediction and fail-fast rule for human review.

The opponent gate is bounded to four hours on two CPU pairs. Packaging work uses
separate cores only after reserving them. No GPU is needed for this candidate.
If a required gate fails, report the failure and the blocked release criterion;
the deadline does not turn a failed test into evidence of strength.

Evidence: [native decision screen](analysis/sf-allchildren-20261102/search/README.md),
[full-game pilot](analysis/sf-allchildren-20261102/full-games/README.md),
[opponent protocol](experiments/sf-opponent-20261108/README.md).

Progress at 08:15 UTC on 8 November:

- Portable, self-contained scorer built with Ubuntu 22.04 / GCC 12.3 and
  upstream CPU dispatch. Embedded NNUE exported and hash verified from an
  otherwise empty executable directory. The first incomplete embedding build
  was rejected and its evidence retained.
- 3,072 paired queries and 64 special-case calls pass with identical scores,
  best moves and nodes relative to the laboratory candidate. Actual packaged
  scorer throughput is 1.57–1.68x the shipped v37 scorer on the four panels.
- Staged ZIP: 84,989,047 bytes, SHA256
  `ba6610f299c1589118ae335f3c46fbff802bf158456db9260ac911dce0d4f69f`.
  Offline Ubuntu build and first move pass. Four protocol checks across both
  colors and 180/2-second clocks pass, maximum startup 0.771 s. The inherited
  failure on an artificial 0.2-second prompt is documented, including the same
  failure in v37; that prompt is below the reachable 180+2 turn-clock range.
- Both exact-ZIP games versus baseline.py pass (White and Black wins), without
  faults, warnings or forfeits. Maximum sampled group RSS is about 627 MiB.
  Original batch 50304 exited successfully and owned process identities are
  gone; cores 4–5 released. The separate 32-game matched Misty gate remains
  in progress on 0–3. Package checks are not strength evidence.
- Fable independently confirmed the pilot and has been asked to review the
  exact staged ZIP on 6–7, then handle v37-relative arena tracking after a human
  upload. Neither publication nor an arena upload has occurred.
