# Learned opponent prior at arena clocks

The first same-byte r10c comparison is promising but inconclusive: prior 2
scored **4 wins, 3 draws and 1 loss**, or 68.75%, over four color-swapped pairs
at 180+2. Its pair-bootstrap 95% interval is **37.5–93.75%**. All eight games
finished with both clocks positive; five ended with a capturable king and
three by repetition. No six-ply opening-book trap occurred. This is a small
screen against one self-opponent family, not an Elo estimate.

`r10c-result.json` pins the archive, compiled runtime, neural graphs, book,
referee, replay hashes and pair seeds 12000–12007. The archive SHA-256 is
`2ae7ee3c6cce97ab788947414dd10976c28c43cf9a2c7eef88309e6b337d90ee`.
Only `FOW_OPPONENT_PRIOR` differs between candidate (2) and control (1).

Fable subsequently fixed an opening-book safety bypass in `2e3df9d`. This
completed result is specific to the old r10c runtime. It must not be treated
as a result for the corrected r10d archive, or as evidence that book safety
has been tested here. The follow-up in `r10d-design.json` repeats four pairs
on the corrected archive using new seeds 22000–22007. Both arms use identical
book and model bytes. Results will remain separate from the old comparison.

No release ZIP is produced by these runners. A useful result still needs
broader opponents and independent evidence before changing the arena default.
