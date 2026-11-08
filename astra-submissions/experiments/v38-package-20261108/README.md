# V38 package preparation

Build the exact experiment-256 Stockfish 19 source patch in a dedicated Ubuntu
22.04 container on cores 4–5. The initial AVX2 laboratory binary requires glibc
2.38 and GLIBCXX 3.4.32; it must not be blindly distributed to the arena.
The official universal target selects among eight x86 instruction sets and
statically links libstdc++/libgcc. No GPU, host service, or Fable source is used.

Before release, require identical move scores, best moves and node counts
against the measured binary on the frozen played-parent and search-frontier
panels, cold and warm. Check special moves, terminal cases, disabled controls,
and execution on Ubuntu 22.04. Measure packaged scoring throughput against the
shipped v37 scorer (at least 1.2× median on each panel/regime). A discrepancy
requires investigation and renewed relevant validation; it is not a license
to call the packaged bytes tested by the original games.

The native C sources, history table and learned coefficients remain exactly
those in the pinned v37 ZIP. Package source/licence for the modified scorer
and a build recipe. ZIP publication remains conditional on the frozen Misty
gate, actual archive validation and the +1 version check.
