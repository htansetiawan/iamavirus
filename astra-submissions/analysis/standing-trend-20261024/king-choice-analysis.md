# v35 king-choice audit against four high-drain opponents

## Scope and validation

I audited all available IAmAVirus v35 games since Oct 17 against Duck, Decent
Chess Bot, Strongly Invisible, and Instructors, through the latest raw replay
(Oct 24 10:12 UTC). This is a saved corpus analysis, not a live API fetch. The
accepted replay index SHA-256 and exact game IDs are in
[`king-choice-audit.json`](king-choice-audit.json). The 1,171 selected replays
all revalidated against the pinned course rules; none were skipped and there
were no legal-candidate mismatches. This gives 784 losses, 346 wins, and 41
draws: 52,254 own decisions total.

For every own choice, `histories.build_episode` reconstructs the actor's legal
move set from its actual observation history. The pinned referee then labels
whether each legal move leaves the own king capturable immediately on the true
board. These labels are used only for this after-the-game audit.

## Result

| Outcome | Games | Own decisions | King moves / 100 decisions | Chosen immediate-fatal moves / 100 decisions | Fatal king move rate | Fatal choices with a safe actor-legal alternative |
|---|---:|---:|---:|---:|---:|---:|
| Loss | 784 | 34,221 | 19.82 | 2.29 | 7.27% of king moves | 492 / 783 (62.8%) |
| Win | 346 | 15,720 | 9.75 | 0 | 0 | 0 |
| Draw | 41 | 2,313 | 19.28 | 0 | 0 | 0 |

Game-cluster bootstrap (5,000 resamples, stratified by result) puts the
loss-minus-win increase in king moves at **10.09 per 100 decisions** (95% CI
8.77 to 11.38). Chosen immediate-fatal moves increase by **2.29 per 100
loss decisions** (95% CI 2.24 to 2.34); fatal choices that had at least one
nonfatal actor-legal alternative increase by **1.44 per 100 loss decisions**
(95% CI 1.36 to 1.52). The full intervals and the deterministic bootstrap seed
are in the JSON.

The 492 fatal choices with safe alternatives split across the four opponents:
Decent Chess Bot 136, Strongly Invisible 139, Duck 121, Instructors 96. The
per-opponent fatal-choice rates and representative observation/board/action
records are retained in the JSON.

## What this means

This provides a concrete safety target: in this sample, many losing games
contain an own move that is fatal on the true board even though another move
from the actor's legal list survives the immediate king-capture rule. A
belief or final-choice safety mechanism failed to preserve/select that escape.
The next engine replay should inspect these choices' particle support and
selected-move risk, then determine whether the true attacker was absent from
the belief, underweighted, or present but filtered out at the root.

It does **not** justify a blanket king-move penalty. Losses have nearly twice
the king-move rate of wins, but among selected king moves only 67.6% of losing
game king moves had a non-king move that was safe on the true board, compared
with 92.7% for winning games. Losing-game king moves more often occur under
immediate danger; the pattern is consistent with earlier pressure forcing
king defense. The target should be keeping fatal choices out of the final
candidate set, while preserving purposeful king escapes and offense.

A true-board safe alternative is not proof that the bot could infer it from
its observation, that it remains safe in every plausible hidden world, or that
it is strategically superior over multiple plies. The associations are
conditioned on game result and four opponents; they are not an Elo estimate.
The reported 62.8% is a diagnostic upper-bound opportunity under immediate
truth labels, not a claimed recoverable-win rate.

## Next validation gate

Replay v35's exact binary on these actor histories and log for each fatal
choice: whether the truth occurs in its belief set, its rank/weight, estimated
risk of the chosen and nonfatal alternatives, and whether the chosen move
survives the engine's final root safety union. This splits three failure modes:

1. **Belief omission/misweighting:** preserve exact capture facts and improve
   recent-attacker persistence; validate truth support/calibration.
2. **Candidate omission:** ensure the safer move survives regret/search shortlists.
3. **Choice inversion:** if retained and estimated safer, repair the payoff/gate.

Run the same audit on matched wins and colors. Branch the changed choice through
the referee only after one mechanism is identified. Do not build a release until
the candidate fixes these known cases without increasing fatal choices on an
untouched chronological set and without protocol/clock regressions.

## Reproduction

```sh
python3 astra-submissions/tools/audit_king_choice_windows.py \
  --raw data/raw \
  --since 2026-10-17 \
  --version 35 \
  --output astra-submissions/analysis/standing-trend-20261024/king-choice-audit.json
```
