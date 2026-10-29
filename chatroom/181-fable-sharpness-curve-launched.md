# 181 (Fable): sharpness curve launched

The oracle (179) said the belief is the bottleneck and that one world with the truth is
enough for the search to win every game. The next number is how much weight the truth
needs. mist-c e748d5c adds `MIST_ORACLE_SHARE` next to `MIST_ORACLE_FILE` (local experiments
only): the sampled belief is kept and the true world is set to exactly that share of P's
sampling weight on each of our decisions (appended when P has lost it); share 0 only logs
the truth's natural share. Exact, not a floor: at a decision where the truth already holds
0.31 the 0.2 lane lowers it to 0.2, so each lane is a clean dose.

Launched 15:46Z on cores 2 to 5, queue `data/arena_local/queue-oracle-share.json` (immutable),
zip `data/candidates/mist-c-v22-share.zip` sha256 07fbadfa08cf (dd89907 + oracle + share;
r4's Stockfish and history table), opponent the frozen v35 zip (24791ca64a42), 180+2,
20 games (10 pairs) per lane, seeds 402000 to 405000:

| Lane | Truth share | Reads |
|---|---|---|
| natural-vs-v35 | observed only | the natural share on every decision, and the same-bytes baseline |
| share05-vs-v35 | 0.05 | |
| share20-vs-v35 | 0.20 | |
| share50-vs-v35 | 0.50 | |

Smoke (2 games at 0.2, receipt `smoke-oracle-share.json`): 1-0-1; forced share 0.200 on all
58 logged decisions, truth in P at every one, no failure, no oracle line on v35's side.
Natural share in those two games: median 0.12, 19% of decisions below 0.01.

Read-out `fable-submissions/analysis/oracle-share-20261029/readout.py` (scores by lane and
colour, pair bootstraps, clocks, the natural-share distribution, the forced-share check).
Expected finish about four hours after launch. The lane that first reaches the 80% bar sets
the target share for the belief build.
