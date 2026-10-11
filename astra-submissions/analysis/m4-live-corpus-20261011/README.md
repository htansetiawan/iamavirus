# Fresh v30 data, a clock failure, and corrected observation labels

Public snapshot: **2026-10-11 13:18 UTC**. Arena v30 (Misty 4-second wrapper,
not our clean-room C engine) was active at **1760.23 Elo**, 115W–19D–132L in
266 games. Duck was 1950.26 Elo. This is a snapshot, not a version-effect claim.

The paced monitor cached **43 new completed games**. The course referee
independently reconstructs **42 board-terminal games, 3,547 frames and 1,755
of our decisions**, validating moves, both observations and final results.
The remaining game is a time forfeit and is retained separately. The validated
set is 17W–2D–23L; including the forfeit, 17W–2D–24L. It is a recent interval
with an uneven opponent mix, not a held-out strength benchmark.

## What the cases say

All **23 king losses** end to attackers hidden before our final move. Sixteen
have an immediate-survival alternative on the true board; seven do not. Those
alternatives do not establish actor-known safety or a winning continuation.

Seventeen losses follow an opponent move with **no change in our observation**.
Denominators matter: this is 17/851 unchanged-observation decisions, versus
6/904 changed-observation decisions. The observations are correlated within
games and differ in game phase. Do not turn this into an unconditional "move
the king whenever nothing changed" rule.

The fatal moves split into eight king entries onto attacked squares, eight
non-king moves that leave an existing attack, and seven king moves that fail
to escape an existing attack. **Twenty-one of the 23 were already behind on
material.** The two equal-material exceptions provide compact new regression
cases without attributing every lost endgame to the final move:

- **gjlnku86, Black, ply17:** central exchanges leave the e8 king exposed to
  hidden Qa4. After the invisible queen move, Ne5xd3 loses immediately.
  Seven moves survive one turn. A composable motif: vacated center → hidden
  diagonal check → tempting capture elsewhere.
- **c4ak2ldi, Black, ply59:** hidden Rc8 attacks the g8 king. Re2xf2 loses;
  Re2-e8 is the only immediate-survival move. A composable motif: exposed back
  rank → invisible rook invasion → defensive interposition. Replay clocks
  indicate the fatal move took about **1.7 ms**, unlike the usual multi-second
  turns; public data does not reveal why the bot returned so quickly.

Neither case is an opponent-name rule. Both are retrospective labels, suitable
for diagnosing belief support and action ranking with observation-only inputs.
`patterns.json` retains all cases and the denominator counts.

## Time failure

**rixuad4w**, Black against Mist Opportunities v2: public diagnostics report
`time_limit`, move phase, ply143. The final supplied clock is 2.418274676 s;
there is no complete response. Across 71 successful own moves, mean elapsed
time is 4.501 s and median 4.469 s under a 2-second increment. This identifies
a clock failure but does not localize it to search, inference or the wrapper.
Fable was notified in `chatroom/056-astra-v30-clock-forfeit-and-dominance-screen.md`.
The final position is materially lost but has seven immediately surviving moves.

## Correction to earlier local-game audits

`m4_match_audit.py` previously compared frame `index-3` with `index-1` before
our move. That interval contains **our previous move as well as the opponent's**.
It must compare `index-2` with `index-1`. The new regression reconstructs a full
legal game where d4 changes White's view but ...e6 does not, and checks both colors.

Corrected copies for the historical fast-root and settling screens are retained
here. **46 and 49 observation-change labels change**, respectively. A structural
comparison proves every other audit field identical after ignoring the auditor
hash. Outcomes, legal alternatives, material values and previous promotion
decisions are unchanged. Original reports remain available as historical artifacts;
use the corrected copies for this field. The first uncorrected public curation
attempt is preserved on Seagate but is superseded by this bundle.

## Reproduction and provenance

- `summary.json`: selected replay IDs, source hashes, referee/auditor hashes.
- `poll.json`: frozen selection from the public monitor.
- `audits.json.gz`: all independently checked decisions and tactical labels.
- `examples/`: the two equal-material cases and the public time-forfeit report.
- `bundle.json`: source and repository hashes for retained evidence.
- `correction-check.json`: historical-report comparison.

Run the curator with the starter kit Python and the frozen `referee.py`; its
full inputs remain under `/media/henrytan/seagate/iamavirus/astra/arena-monitor/`.
`analyze.py` recreates `patterns.json`. No GPU work or model fitting was needed.
