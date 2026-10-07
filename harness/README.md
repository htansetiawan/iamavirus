# Measurement harness

See [../versions/MEASUREMENT.md](../versions/MEASUREMENT.md) for what each tool
can and cannot resolve.

These scripts need the course starter kit, because `referee.py` is the rules
oracle and is GPL-2.0 course material that is deliberately **not** vendored here.
Extract the kit, create its virtual environment, and copy or symlink these scripts
beside its `referee.py`.

```bash
# corpus of real games from the public read-only API (be polite; it rate-limits)
python3 corpus_download.py --team "Greek Gift" --outcome team-won \
    --limit 40 --side loser --pause 1.2 --out corpus-greek.txt

# offline benchmark: real positions, ground-truth labels
g++ -O2 -std=c++20 tools/benchmark_corpus.cc <engine .cc files> -o benchmark
./benchmark corpus-greek.txt <stride> <nodes-per-decision>

# validate the harness itself before trusting it: must score ~0.500
python3 selftest.py /path/to/bot 16 20 0.3 4

# sequential A/B between two configurations of one binary
python3 sprt.py "candidate" "baseline" --nodes 4000000 --elo0 0 --elo1 50 \
    -- FOW_OPPONENT_PRIOR=1 -- FOW_OPPONENT_PRIOR=0
```

`arena.py` is the older fixed-batch runner against `baseline.py`. It is kept for
reference; `sprt.py` supersedes it, and `baseline.py` at Elo 1000 is too weak to
separate strong configurations anyway.

## Ablation knobs

Every judgement call in the engine reads from the environment, so configurations
can be compared without recompiling. Unset, each keeps the shipping default; a
malformed value is reported on stderr and the default kept.

`FOW_OPPONENT_PRIOR`, `FOW_KING_RISK_PRICE`, `FOW_KING_LOSS_TOLERANCE`,
`FOW_PIECE_RISK`, `FOW_SPECULATIVE_WIN`, `FOW_MATRIX_GAME`, `FOW_PARTICLES`,
`FOW_HYPOTHESES`, `FOW_SHORTLIST`, `FOW_NODE_BUDGET`, `FOW_TIME_CAP`,
`FOW_HASH_MB`, `FOW_LMR`, `FOW_ASPIRATION`, `FOW_SEED`.
