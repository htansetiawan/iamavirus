# All-child Stockfish scoring, experiment 256

The current v37 profile puts 82.2% of search wall time inside Stockfish calls.
Test a different depth-one evaluator: one root traversal, full-window PV search
for every legal child, with native quiescence and NNUE retained. This removes
repeated MultiPV root passes. It is **not** an exact optimization: aspiration,
history, optimism and transposition-table trajectories differ. No change to
mist-c, lower MultiPV, async mode, score floors, or arena submission is involved.

Source is official Stockfish `sf_19`, compared file by file with the locally
saved release whose binary hash equals our shipped evaluator. Export the
embedded network from that binary and check its content hash. Keep the upstream
licence; the published patch and source pins reproduce the experiment. Build
base and patched controls with identical AVX2 non-PGO flags. Also compare the
actual shipped universal PGO binary: a faster control is insufficient if the
candidate is slower than the shipped implementation.

The flag is opt-in (`ASTRA_SF_ALLCHILDREN=1`), applies only to depth 1, one
thread, full MultiPV, no handicap and no root tablebase result. Deeper searches
and ordinary settings retain the upstream path. It never changes FoW terminal
logic: unsupported worlds and moves still belong to the unmodified native
engine. This first stage evaluates orthodox-supported complete parents only.

Freeze 256 played parents, two from each of 128 games in the existing development
validation fold, by salted game/position hashes without score/outcome selection.
Reconstruct full histories with the course referee and verify both observations
and board. Record and replace only unsupported parents before any scoring;
require at least two orthodox legal moves. This is a reused development corpus,
not untouched validation, searched leaves, or an Elo test.

Preflight checks starting position, castling, en passant, promotion, being in
check, mate-in-one, checkmate and stalemate. All legal root moves must be scored;
mate/stalemate terminals must remain correct. Patched-off versus rebuilt base
must match scores, best move and nodes; flag-on at depth 2 and restricted
MultiPV must match ordinary behavior. Verify expected moves independently with
python-chess. Preserve all first attempts and protocol failures.

Measure cold-TT per parent and a warmed stream; four arms (shipped, rebuilt,
patched-off, patched-on), rotating request order. Reset between cold parents,
but exclude reset time from query latency. The warm stream keeps TT/history
across the identical parent order. One initial warmup, then three whole passes
per arm. Parent-process timings include UCI transport; also retain SF node counts
and worker CPU totals. CPU cores 0–1 only, no GPU, 15-minute collection cap.

Advancement requires complete identical move coverage, valid terminal handling,
and in **both cold and warmed regimes**: equal-game tanh(cp/400) MAE <=0.08,
mean shipped-teacher regret of candidate's best action <=0.05, regret >0.5
frequency <=1%, total-query speedup >=1.5 versus rebuilt base and >=1.2 versus
the shipped binary. Shipped scores are a fidelity reference, not FoW truth.
Also report mate-label disagreements and exact top-choice agreement. A failure
closes this specific one-pass approximation without selecting different
windows or tuning on the measured parents. A pass earns a separate searched-
frontier fidelity check and actual mist-c integration, not a release.

Primary sources: [Stockfish 19 release](https://github.com/official-stockfish/Stockfish/releases/tag/sf_19),
[its root search](https://github.com/official-stockfish/Stockfish/blob/sf_19/src/search.cpp).
