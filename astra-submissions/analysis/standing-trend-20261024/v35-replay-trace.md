# Exact v35 replay trace on four fatal-choice examples

## Method

I rebuilt the immutable submitted archive
`fable-submissions/iamavirus-v35-mist-c-v14.zip` in `/tmp` with its own
`build.sh` (`gcc`). The diagnostic driver sends the bot the complete sequence
of public actor observations, including views after both players' moves, and
forces only IAmAVirus's recorded actions before the target decision. It does
not send true boards through the bot protocol. The true-board sequence is
passed only to v35's existing `MIST_TRUTH_SEQ` stderr diagnostic. The archive's
Stockfish binary and `data/history.bin` are used. Search budget is the
archive's 10-second default; FOW seed 1; rules-validated replay inputs.

Cases are one earliest-by-ply fatal-choice example for each opponent among
four selected loss classes, chosen to cheaply test the trace pipeline. This is
a targeted pilot, not a random sample. All four exact archive replays
completed and selected the **same fatal move as the historical v35 game**.

## Traces

| Opponent | Ply | Fatal move replayed by v35 | Hidden attacker after move | v35 truth share / rank | v35 estimated king risk | Immediate-safe alternative risk |
|---|---:|---|---|---:|---:|---:|
| Decent Chess Bot | 33 | d8c7 | Qe1 | 3.22% / 13 | 13.12% | 0%; alternatives all had 100% queen-loss risk |
| Instructors | 28 | d4b4 | Rc8 | 0.102% / 122 | 0.41% | 0% |
| Strongly Invisible | 19 | b8c6 | Rc8 | 0.090% / 65 | 0.09% | 0.04% |
| Duck | 25 | e5g6 | Bg5 | 0.007% / 423 | 6.46% | 0.45%; alternative had 6.9% queen-loss risk |

The two most recent hidden arrivals were completely unseen: Strongly Invisible
played c1c8 and Duck played c1g5; in both cases the origin and destination were
hidden in our observation before and after the move. Instructors' rook was
already hidden; the immediate prior move was a different piece. Decent's
queen was already in the attacking line while its posterior mass remained
low. This is direct evidence for both posterior dilution and hidden-attacker
persistence as candidate mechanisms.

The source already has a king-risk guard and a queen-risk guard. At default
`MIST_KING_GUARD=0.02`, all four replayed fatal choices survive. A matched
four-position ablation with the same archive, prefix, clock and seed gave:

| `MIST_KING_GUARD` | Chosen moves still immediately fatal on true board | Historical fatal action selected |
|---:|---:|---:|
| Default 0.02 | 4/4 | 4/4 |
| 0.005 | 3/4 | 2/4 |
| 0.0001 | 1/4 | 0/4 |

At 0.0001, the engine selected immediate-safe actions in three cases. The
remaining Decent Chess Bot case changed from d8c7 to d8b8, but d8b8 was also
fatal under the referee. Thus lowering the scalar tolerance changes decisions
and fixes some examples, but does not robustly recognize every fatal choice.
The Duck case exposes the mixed-risk trade: one immediate-safe move carried
6.9% queen-loss probability, so a scalar king+queen risk can prefer a 6.46%
king-loss move. Material gain also competes directly with king danger. This
needs a terminal-risk policy or posterior improvement, not a permanent
hand-tuned threshold based on four positions.

## Interpretation and next gate

The exact binary can reproduce these four losses, so this is not only a
hypothetical audit of a different engine. The truth is present in each tracked
belief but carries very little mass in three cases; the fourth has only 3.22%
share. Two attackers arrived through zero-change hidden moves. Immediate
safety is underweighted relative to expected material/queen exposure, and
posterior support quality is visibly poor in the tail.

This remains diagnostic: four positions were deliberately selected from losses;
a different move is checked only for immediate referee fatality, not through
a branched opponent response. The lower-guard results are not an Elo estimate
or a release recommendation. Next, expand the trace to a predeclared,
stratified set of fatal and nonfatal choices from wins and losses, several
opponents/colors, and more seeds. Log posterior truth rank, chosen/alternative
risk, and retained root moves. Then branch the changed decisions and their
opponent responses through the exact referee. A candidate must reduce immediate
fatal choices on an untouched chronological set without increasing survival
errors or material/clock failures.

## Artifacts

- [`v35-fatal-choice-traces-pilot.json`](v35-fatal-choice-traces-pilot.json)
- [`v35-fatal-choice-guard005.json`](v35-fatal-choice-guard005.json)
- [`v35-fatal-choice-guard0001.json`](v35-fatal-choice-guard0001.json)
- [`guard-ablation-referee-results.json`](guard-ablation-referee-results.json)
- [`replay_v35_fatal_choices.py`](../../tools/replay_v35_fatal_choices.py)
- [`audit_guard_ablation.py`](../../tools/audit_guard_ablation.py)
