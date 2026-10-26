# v20 calibration replay, 26 Oct 2026 20:00-20:52 UTC

Engine mist-c 539d4e3 (defaults = v35); v35 zip's Stockfish 19 and history table; 2.5 s a decision, seed 1, one worker per core pair (A cores 2-3, B cores 4-5).
A = baseline (piece term off); B = MIST_PIECE_GUARD=0.758 (the fitted lambda), MIST_PIECE_LOSS=3.

```
calib n=796 paired decisions
  repeat of the recorded move: A 0.585  B 0.438
  changed move (A vs B chose differently): 0.494
  cp loss on the true board: A mean 185 med 68 | B mean 141 med 52 | B better by 100+ in 125, worse in 57 of 730
  fatal (safe move existed): A 1/796  B 1/796
  piece guard fired (any veto): A 0.000  B 0.948;  vetoed the recorded move: B 0.242
  truth in P at the decision: 787/796
```

Where the piece term vetoed the recorded losing move (193 of 796): cp loss 315 -> 125 (better by 100+ in 77, worse in 16). Where it did not (603): 148 -> 145. By opponent, cp A -> B / repeat A -> B: Decent 220 -> 130 / 0.60 -> 0.50; Greek Gift 150 -> 110 / 0.63 -> 0.48; Instructors 182 -> 166 / 0.65 -> 0.44; Knight Vision 257 -> 199 / 0.53 -> 0.44; Strongly Invisible 183 -> 143 / 0.55 -> 0.47; duck 139 -> 98 / 0.60 -> 0.41.

Not yet known: the false-veto rate on ordinary positions (both control sets running), the out-of-sample set, and the guard's clock cost.
