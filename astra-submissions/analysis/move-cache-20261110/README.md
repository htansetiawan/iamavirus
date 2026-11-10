# Fresh immutable move generation after the opponent refresh

Original export session 36658 exits 0. The generation contains **96,210 games
and 7,170,888 moves**: 81,907 train and 14,303 test. It retains the same
October 19 cutoff, seed 7 and 15% ID-based test split as the previous
generation. The cache serves 95,557 games and reads 653 new replay files.

The exporter reports 7.16 seconds including publication; its manifest records
5.78 seconds before publication. This routine warm-cache refresh is not a
controlled comparison against the old exporter and implies no Elo gain.

The independent auditor verifies the entire eligible accepted-journal cohort,
all 7.17 million move tokens, sequence hashes, player tags, train/test split,
manifest hashes and compatibility-file equality. It verifies moves against
the accepted ingest authority; it is not a fresh rules replay of 96,210 games.
The separate opponent refresh independently checks 922 analysed games and
85,112 distinct frames, including all 622 newly collected replays.

Manifest SHA-256:
`ccdc59829904330e3bf409b1431f6c46df64ac47306e9bedd484682293e1945b`.
The immutable generation on the bulk disk is
`gen-800092857d6f4c6082f4b2a06a2b971c`. The JSON pointer and individually
replaced compatibility files pass their checks; the previous generation
remains available.

Resolve once before fitting:

```sh
python3 astra-submissions/tools/export_move_cache.py \
  --out-prefix data/derived/moves/arena-latest --resolve
```

Use the returned immutable pair. A fit still needs a fresh chronological
test design, sequence deduplication, predictive/posterior validation and
playing gates. No model, history table, candidate or arena policy changes
follow automatically from these additions.

See [audit.json](audit.json), [generation-manifest.json](generation-manifest.json)
and [receipt.json](receipt.json).
