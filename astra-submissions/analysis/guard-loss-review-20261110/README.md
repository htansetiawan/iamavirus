# Four paired roots: the union guard does not fix these final losses

Original session 97171 exits 0. Every pair uses the same reconstructed belief,
sample seed and sampled worlds, with 2.5 seconds per arm and alternating order.
The independent audit verifies 322 source frames, source/result hashes,
unchanged belief fingerprints, probability/value arithmetic and truth labels.

| Root | Base move | Candidate move | Safe actions kept, base / candidate |
|---|---|---|---:|
| White ply 78 | d8c8 | d8c8 | 11 / 12 |
| White ply 80 | h2g1 | h2g1 | 0 / 0; none exists on truth |
| Black ply 79 | h3h2 | h3h2 | 5 / 5 |
| Black ply 81 | g7g8 | g7g8 | 0 / 0; two exist on truth |

White's final position is already lost in one ply. Its preceding decision
adds e8d7 under the candidate but still selects d8c8. The terminal sample
correctly assigns fatal risk 1 and value -2, so this loss was created earlier.

Black's final root retains only g7g8 under either mask. Both actual safe
escapes, g7f6 and g7h6, are removed. All 32 sampled worlds give the chosen
capture zero immediate fatal risk, while its searched continuation value is
about -0.963. Changing the sampler within this one-action set cannot restore
an excluded escape.

These outcome-selected positions do not establish which earlier policy
choice caused the live loss, or prove a probability-calibration defect. The
one-core reconstruction can thin differently, and no full-population snapshot
was exported. The next useful measurement separates full-belief support,
weighted risks, sampled risk and action-set censorship. It must distinguish
a missing hypothesis from a low-weight one; exact-board absence among 32
draws is insufficient evidence of either.

The source and plan were published at a8c8c12a before execution. Cleanup
finds no paired actor or its evaluator remaining. An initial overbroad
Stockfish-name scan matched active comparison workers; it is preserved, and
exact executable/ancestry checks identify them separately. No process was
signaled. The 32-game strength panel stays unchanged and active.

See [audit.json](audit.json), [cleanup.json](cleanup.json), and the individual
paired action/world exports. This is diagnosis, not strength evidence.
