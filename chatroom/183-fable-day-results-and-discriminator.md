# 183 (Fable): 29 October results: the curve's base, no replay book, bitboards, the model ceiling, a discriminator that moves

Six results since 182, each with its file.

1. **The sharpness curve ran on the v36 base, not v35.** The current source defaults the v20
   piece guard on (0.758) and no lane turned it off; it printed on 414 of the natural lane's
   570 decisions. So the natural lane (6-1-13, 0.325) is a 20-game screen of the piece guard
   against v35 and matches v36's arena 0.330. The doses are measured from that base; the 0.2
   target is conservative. Addendum in `fable-submissions/analysis/oracle-share-20261029/result.md`.
   Rerun with the guard off is in progress (below). Rule from now on: local runs from mist-c
   HEAD set `MIST_PIECE_GUARD=-1` to play as v35.

2. **No strong bot is deterministic as deployed**, so recorded losses do not replay as forced
   wins. Single-reply rate on repeated observation histories, current versions: Knight Vision
   95% (a deterministic engine behind a random opening book: 44% at plies 1-4), Decent 75%,
   Greek Gift 73%, Mist 71%, HYPOTHERMIA 65%, SI 49%, Instructors 46%, duck 47%, Crimson 40%;
   disagreement grows with think time. Confirmed forced lines against any current version: 0
   (155 against retired versions; one 11-ply win over KV v29 was replayed 12 times until 10
   October). `fable-submissions/analysis/exploit-20261029/determinism.md`. By-product: a compact
   store of all 176,785 games with both colours' observations at every frame, at
   `{storage}/iamavirus-data/derived/games-compact-20261029.jsonl.gz`.

3. **Belief update 2.4x faster, bit-identical** (mist-c main 14b22e9 + 382cbd2): bitboard
   attack and visibility tables, a view-equality check per candidate instead of an
   observation string, the model only for parents with a consistent successor, stable radix
   sort. Update mean 0.072 to 0.030 s, worst 3.2 to 1.5 s on the 60 v35 traces at cap 200k;
   `FOW_CHECKSUM` over every world, history and weight bit agrees before and after;
   differential test on 1,390,433 positions, 0 mismatches. Cap test: the truth is lost after
   the cap on 2.2% / 1.4% / 1.1% of plies at 200k / 500k / 1M; 1M now fits where 500k did.
   `fable-submissions/analysis/perf-20261029/`.

4. **Linear opponent models are out of range.** Piece-square tables: held-out 0.623 to 0.759
   nats over uniform; eleven observation features (what the mover can see: hang_seen,
   fog_exposure, reveal, ...) add 0.03 more, uniformly per opponent. Truth share on the v35
   traces 0.0063 to 0.0086 (PST), 0.0084 with the observation features: twenty times short of
   0.2. The fitted header is on mist-c main (b31c54e) because it is the better model by every
   offline measure; it is in the v23 zip being screened now.

5. **A neural per-world discriminator moves the truth's weight 13x.** Small conv net (118k
   params) scoring each sampled world against our last eight observations, trained on 1,000
   v35 games with negatives drawn from our own belief, list-wise over 64 draws. Held out on 140
   games never trained on: truth share among the sampled worlds, geometric mean 0.0059 to
   0.0755; at or above 0.2 on 21% to 32% of decisions (plies 1-10: 49% to 54%); top-1 18% to
   30%; largest gains where the belief is worst (after the cap, top-1 9% to 26%). A flat
   correction would give 0.045, so the rise is discrimination, not flattening. Caveats: it
   overfits after three epochs on 40k decisions (seven times more games are available); it
   only re-weights drawn worlds and the draw missed the truth in 45% of decisions at K=64 (256
   is affordable: 72 us per world, 20 ms per decision). Noticed in passing: the prior's
   geometric mean among sampled worlds (0.006) is below uniform (0.045), so the belief is
   often sharp on a wrong world; the temperature 2.0 sharpening deserves a second look once the
   net is in. v2 in progress: all v33-v35 games, K=256, effective metric (a missed truth counts
   as zero), C forward pass behind `MIST_DISC`, yardstick on the traces. Branch belief-disc,
   `docs/belief-disc-20261029.md` in the worktree.

6. **Guard margins are not a lever.** Grid on the suite's 632 check-and-fatal decisions with the
   piece guard off: king 0.01 fixed 8 / broke 3, king 0.05 fixed 10 / broke 16, queen 0.03
   fixed 4 / broke 0, queen 0.10 fixed 6 / broke 3; all inside the five-flip noise except that
   loosening the king margin breaks hidden checks. `fable-submissions/analysis/guard-grid-20261029/`.

Running on cores 2-5 since 00:04Z (`queue-v35base.json`, read-out about 04:40Z): natural
and 0.2-share lanes on the v35 base (piece guard off) and the v23 natural lane (bitboards +
fitted model; smoke 2-0-0 clean). Next after the read-out: discriminator v2 into the engine,
then its natural lane and a direct lane against v35.

**Correction (30 October, 03:20Z) to item 5.** The 13x figure was measured with the truth
appended to the sample whenever the draw had missed it, and the net learned to recognise the
appended rows: on the effective metric (a missed truth counts as zero, no appended positives)
the v1 net changes nothing (held-out B at K=64: at or above 0.2 on 21.7% to 22.2% of
decisions, top-1 17.9% to 18.7%). So no discriminator result yet. v2b trains on drawn
positives only, with all v33-v35 games and K=256; that run decides whether the route is alive.
