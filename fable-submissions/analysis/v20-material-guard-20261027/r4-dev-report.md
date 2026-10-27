# r4 development replays (mist-c dd89907, zip 1649dfbfe23b, build 65162c2c780c)

Paired A/B at the same time: A = r4 build, piece term off (v35 rules + terminal-aware capture events); B = r4 defaults. 2.5 s, seed 1, one worker, truth scored. Generated 2026-10-27T19:18:20Z.

## fresh-failures: A vs B (both r4)
```
fresh-failures n=97 paired decisions
  repeat of the recorded move: A 0.464  B 0.402
  changed move (A vs B chose differently): 0.505
  cp loss on the true board: A mean 212 med 86 | B mean 162 med 46 | B better by 100+ in 19, worse in 5 of 88
  fatal (safe move existed): A 0/97  B 0/97
  piece guard fired (any veto): A 0.000  B 0.938;  vetoed the recorded move: B 0.247
  truth in P at the decision: 91/97
```

## fresh-control: A vs B (both r4)
```
fresh-control n=100 paired decisions
  repeat of the recorded move: A 0.630  B 0.580
  changed move (A vs B chose differently): 0.310
  cp loss on the true board: A mean 44 med 19 | B mean 42 med 10 | B better by 100+ in 1, worse in 3 of 87
  fatal (safe move existed): A 0/100  B 0/100
  piece guard fired (any veto): A 0.000  B 0.890;  vetoed the recorded move: B 0.040
  truth in P at the decision: 99/100
```

## fresh-control-loss: A vs B (both r4)
```
fresh-control-loss n=71 paired decisions
  repeat of the recorded move: A 0.549  B 0.521
  changed move (A vs B chose differently): 0.408
  cp loss on the true board: A mean 78 med 11 | B mean 71 med 22 | B better by 100+ in 4, worse in 1 of 62
  fatal (safe move existed): A 0/71  B 0/71
  piece guard fired (any veto): A 0.000  B 0.944;  vetoed the recorded move: B 0.028
  truth in P at the decision: 69/71
```

## control-loss: A vs B (both r4)
```
control-loss n=400 paired decisions
  repeat of the recorded move: A 0.490  B 0.517
  changed move (A vs B chose differently): 0.520
  cp loss on the true board: A mean 56 med 20 | B mean 54 med 20 | B better by 100+ in 23, worse in 15 of 348
  fatal (safe move existed): A 0/400  B 0/400
  piece guard fired (any veto): A 0.000  B 0.943;  vetoed the recorded move: B 0.025
  truth in P at the decision: 392/400
```

## control: A vs B (both r4)
```
control n=400 paired decisions
  repeat of the recorded move: A 0.565  B 0.615
  changed move (A vs B chose differently): 0.398
  cp loss on the true board: A mean 55 med 14 | B mean 57 med 14 | B better by 100+ in 22, worse in 19 of 348
  fatal (safe move existed): A 0/400  B 0/400
  piece guard fired (any veto): A 0.000  B 0.895;  vetoed the recorded move: B 0.040
  truth in P at the decision: 398/400
```

## calib: A vs B (both r4)
```
calib n=796 paired decisions
  repeat of the recorded move: A 0.503  B 0.479
  changed move (A vs B chose differently): 0.549
  cp loss on the true board: A mean 161 med 57 | B mean 150 med 54 | B better by 100+ in 118, worse in 94 of 718
  fatal (safe move existed): A 0/796  B 0/796
  piece guard fired (any veto): A 0.000  B 0.946;  vetoed the recorded move: B 0.193
  truth in P at the decision: 775/796
```

## oos: A vs B (both r4)
```
oos n=818 paired decisions
  repeat of the recorded move: A 0.517  B 0.491
  changed move (A vs B chose differently): 0.477
  cp loss on the true board: A mean 155 med 51 | B mean 125 med 46 | B better by 100+ in 103, worse in 68 of 719
  fatal (safe move existed): A 1/818  B 0/818
  piece guard fired (any veto): A 0.000  B 0.943;  vetoed the recorded move: B 0.191
  truth in P at the decision: 785/818
```

## Cross-run (different times; absolute cp shifts with load): earlier B vs r4 B

### fresh-failures: earlier B (r3 build for fresh sets, v20 build at 0.758 for frozen sets) vs r4 B
```
fresh-failures n=97 paired decisions
  repeat of the recorded move: A 0.361  B 0.402
  changed move (A vs B chose differently): 0.299
  cp loss on the true board: A mean 154 med 58 | B mean 162 med 46 | B better by 100+ in 5, worse in 7 of 90
  fatal (safe move existed): A 0/97  B 0/97
  piece guard fired (any veto): A 0.938  B 0.938;  vetoed the recorded move: B 0.247
  truth in P at the decision: 92/97
```

### fresh-control: earlier B (r3 build for fresh sets, v20 build at 0.758 for frozen sets) vs r4 B
```
fresh-control n=100 paired decisions
  repeat of the recorded move: A 0.580  B 0.580
  changed move (A vs B chose differently): 0.110
  cp loss on the true board: A mean 52 med 23 | B mean 42 med 10 | B better by 100+ in 3, worse in 1 of 90
  fatal (safe move existed): A 0/100  B 0/100
  piece guard fired (any veto): A 0.890  B 0.890;  vetoed the recorded move: B 0.040
  truth in P at the decision: 100/100
```

### fresh-control-loss: earlier B (r3 build for fresh sets, v20 build at 0.758 for frozen sets) vs r4 B
```
fresh-control-loss n=71 paired decisions
  repeat of the recorded move: A 0.563  B 0.521
  changed move (A vs B chose differently): 0.141
  cp loss on the true board: A mean 78 med 15 | B mean 71 med 22 | B better by 100+ in 3, worse in 0 of 63
  fatal (safe move existed): A 0/71  B 0/71
  piece guard fired (any veto): A 0.944  B 0.944;  vetoed the recorded move: B 0.028
  truth in P at the decision: 70/71
```

### control-loss: earlier B (r3 build for fresh sets, v20 build at 0.758 for frozen sets) vs r4 B
```
control-loss n=400 paired decisions
  repeat of the recorded move: A 0.552  B 0.517
  changed move (A vs B chose differently): 0.193
  cp loss on the true board: A mean 52 med 20 | B mean 54 med 20 | B better by 100+ in 7, worse in 9 of 360
  fatal (safe move existed): A 0/400  B 0/400
  piece guard fired (any veto): A 0.943  B 0.943;  vetoed the recorded move: B 0.025
  truth in P at the decision: 397/400
```

### control: earlier B (r3 build for fresh sets, v20 build at 0.758 for frozen sets) vs r4 B
```
control n=400 paired decisions
  repeat of the recorded move: A 0.618  B 0.615
  changed move (A vs B chose differently): 0.133
  cp loss on the true board: A mean 53 med 14 | B mean 57 med 14 | B better by 100+ in 10, worse in 10 of 362
  fatal (safe move existed): A 0/400  B 0/400
  piece guard fired (any veto): A 0.895  B 0.895;  vetoed the recorded move: B 0.040
  truth in P at the decision: 398/400
```

### calib: earlier B (r3 build for fresh sets, v20 build at 0.758 for frozen sets) vs r4 B
```
calib n=796 paired decisions
  repeat of the recorded move: A 0.438  B 0.479
  changed move (A vs B chose differently): 0.219
  cp loss on the true board: A mean 141 med 52 | B mean 150 med 54 | B better by 100+ in 42, worse in 68 of 741
  fatal (safe move existed): A 1/796  B 0/796
  piece guard fired (any veto): A 0.948  B 0.946;  vetoed the recorded move: B 0.193
  truth in P at the decision: 787/796
```

### oos: earlier B (r3 build for fresh sets, v20 build at 0.758 for frozen sets) vs r4 B
```
oos n=818 paired decisions
  repeat of the recorded move: A 0.466  B 0.491
  changed move (A vs B chose differently): 0.247
  cp loss on the true board: A mean 130 med 45 | B mean 125 med 46 | B better by 100+ in 57, worse in 43 of 734
  fatal (safe move existed): A 3/818  B 0/818
  piece guard fired (any veto): A 0.952  B 0.943;  vetoed the recorded move: B 0.191
  truth in P at the decision: 790/818
```

## Cross-run, piece term off: earlier A (v20 build for the frozen sets, r3 build for the fresh sets) vs r4 A (terminal-aware events only)

### fresh-failures
```
fresh-failures n=97 paired decisions
  repeat of the recorded move: A 0.546  B 0.464
  changed move (A vs B chose differently): 0.464
  cp loss on the true board: A mean 209 med 69 | B mean 212 med 86 | B better by 100+ in 8, worse in 12 of 90
  fatal (safe move existed): A 0/97  B 0/97
  piece guard fired (any veto): A 0.000  B 0.000;  vetoed the recorded move: B 0.000
  truth in P at the decision: 92/97
```

### fresh-control
```
fresh-control n=100 paired decisions
  repeat of the recorded move: A 0.560  B 0.630
  changed move (A vs B chose differently): 0.320
  cp loss on the true board: A mean 66 med 24 | B mean 44 med 19 | B better by 100+ in 8, worse in 0 of 89
  fatal (safe move existed): A 0/100  B 0/100
  piece guard fired (any veto): A 0.000  B 0.000;  vetoed the recorded move: B 0.000
  truth in P at the decision: 100/100
```

### fresh-control-loss
```
fresh-control-loss n=71 paired decisions
  repeat of the recorded move: A 0.577  B 0.549
  changed move (A vs B chose differently): 0.465
  cp loss on the true board: A mean 99 med 29 | B mean 78 med 11 | B better by 100+ in 3, worse in 4 of 62
  fatal (safe move existed): A 0/71  B 0/71
  piece guard fired (any veto): A 0.000  B 0.000;  vetoed the recorded move: B 0.000
  truth in P at the decision: 70/71
```

### control-loss
```
control-loss n=400 paired decisions
  repeat of the recorded move: A 0.547  B 0.490
  changed move (A vs B chose differently): 0.502
  cp loss on the true board: A mean 54 med 19 | B mean 56 med 20 | B better by 100+ in 15, worse in 25 of 350
  fatal (safe move existed): A 0/400  B 0/400
  piece guard fired (any veto): A 0.000  B 0.000;  vetoed the recorded move: B 0.000
  truth in P at the decision: 397/400
```

### control
```
control n=400 paired decisions
  repeat of the recorded move: A 0.640  B 0.565
  changed move (A vs B chose differently): 0.365
  cp loss on the true board: A mean 51 med 10 | B mean 55 med 14 | B better by 100+ in 12, worse in 20 of 353
  fatal (safe move existed): A 0/400  B 0/400
  piece guard fired (any veto): A 0.000  B 0.000;  vetoed the recorded move: B 0.000
  truth in P at the decision: 398/400
```

### calib
```
calib n=796 paired decisions
  repeat of the recorded move: A 0.585  B 0.503
  changed move (A vs B chose differently): 0.398
  cp loss on the true board: A mean 185 med 68 | B mean 161 med 57 | B better by 100+ in 95, worse in 68 of 730
  fatal (safe move existed): A 1/796  B 0/796
  piece guard fired (any veto): A 0.000  B 0.000;  vetoed the recorded move: B 0.000
  truth in P at the decision: 787/796
```

### oos
```
oos n=818 paired decisions
  repeat of the recorded move: A 0.620  B 0.517
  changed move (A vs B chose differently): 0.414
  cp loss on the true board: A mean 164 med 56 | B mean 155 med 51 | B better by 100+ in 78, worse in 72 of 724
  fatal (safe move existed): A 0/818  B 1/818
  piece guard fired (any veto): A 0.000  B 0.000;  vetoed the recorded move: B 0.000
  truth in P at the decision: 791/818
```

## Reading (Fable, 19:25Z)

Paired at the same time, the piece term on the r4 build does what it did on r3: on the fresh
failures cp loss mean 212 to 162 (median 86 to 46), better by 100+ cp in 19 decisions and worse in
5, repeat of the losing move 0.46 to 0.40; on the out-of-sample set 155 to 125; calibration 161 to
150; the four control sets within a few cp either way with 2.5 to 4 percent of recorded moves
vetoed; no fatal move in 2,682 decisions (A had one on oos). The cross-run columns are at
different load and only say how many decisions moved. This is development evidence; the bench
decides.
