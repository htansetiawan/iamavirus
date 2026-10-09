# Mist Opportunities v1: what it does, and where to attack it

Astra · 2026-10-09. Frozen public snapshot at **21:43:26 UTC** (5:43 p.m. Boston).
All **64 completed games**, not only losses: **41 wins, 6 draws, 17 losses**, Elo **1629.62** at collection.
All are Mist v1; our comparison games are **arena IAmAVirus v21**. Archive numbers are separate.

**Conclusion:** Mist develops reliably, converts material advantages, and makes hidden attacks that our bot mishandles. Its recurring kingside king location gives us a concrete attack target. Hidden rook batteries and bait have beaten it, but the better plan is to build pressure and then offer bait; Mist often declines an isolated poisoned capture.

## Record and style

All records below are from Mist's perspective, W–D–L.

| Opponent | Record |
|---|---:|
| IAmAVirus v21 | **8–2–0** |
| TA Baseline A v5 | 7–1–0 |
| TA Baseline S v3 | 6–0–2 |
| TA Baseline P v5 | 11–0–3 |
| Instructors v4 | 2–0–2 |
| duck v5 | 1–2–3 |
| Strongly Invisible v35 | 0–0–4 |
| Knight Vision v29 | 0–0–2 |
| Decent Chess Bot v4 | 0–1–1 |
| baseline.py v1 / Apricot Squad v9 | 4–0–0 / 2–0–0 |

It has no Greek Gift game in this snapshot. These small matchup counts characterize this snapshot, not precise underlying win rates.

- **Predictable destination, adaptive route.** White plays 1.d4 in 32/32 games; its first three moves are d4, c3, Nf3 in 22/32. Black starts ...c6 in 31/32 and ...d5 second in 31/32; its third move is ...Nf6 in 23 and ...Qa5 in 8. The exact five-move development sequence is much less fixed: the common White d4/c3/Nf3/e3/Bd3 sequence occurs seven times, Black c6/d5/Nf6/e6/Bd6 thirteen times.
- **Kingside castling in 59/64**, queenside once, no castling four times. All ten games against us feature kingside castling. Do not encode “always castles kingside.”
- **Active middlegame.** After ply 24, rooks account for 429/1,606 moves, pawns 396, kings 224. King moves are 14%, so “just shuffles its king” understates its play. Replay behavior does not identify its private search/model architecture.
- **Strong conversion.** A sustained material lead of at least three points occurred in 38 games: 35 wins, one draw, two losses. None of its 41 wins included a sustained three-point deficit. Here “sustained” means four complete consecutive plies, with P=1, N/B=3, R=5, Q=9.
- **It uses its clock.** Median move cost 4.79 seconds, maximum 8.22. Lowest final clock 25.71 seconds; no time forfeits. Clock exhaustion is not the first exploit to pursue from these games.

## Why it beats us

All eight wins against us included a sustained three-point material lead. Our queen was captured in nine of the ten games, but some were queen exchanges: that statistic alone is not nine blunders. The concrete exchange patterns matter.

| Mechanism | Evidence |
|---|---|
| We make king attacks easy to see | Our **six** immediate king threats all had at least one attacker visible in Mist's reply observation. Mist escaped all six. |
| Mist creates concealed pressure | **12 of its 17** immediate king threats against us had every attacker hidden in our reply observation. Three ended the game on our next move. All 17 positions had a surviving reply on the true board. |
| Our king wanders into covered squares | In **five of our eight losses**, our king was not attacked before our fatal king move. |
| We miss an existing hidden attack | The other **three** losses followed an existing hidden king threat. One king escape entered a different hidden attack; two unrelated moves left the threat in place. |
| We still had a move that survives | **All eight** final positions had at least one true-board surviving alternative. This establishes an avoidable immediate loss, not that those alternatives would win the game. |

Two especially useful replay diagnoses:

1. [s8p7ue0x](https://www.mit.edu/~6.7980/fow/?tab=arena&game=s8p7ue0x): at ply 47 our **Qe2xe8** takes a rook, then Mist's **Bc6xe8** takes our queen; another rook exchange follows. Later **...Nf6–g4** at ply 72 attacks our king on h2 invisibly. We choose **Ng2xe1**, taking a rook while losing the king. **Kh2–h3** was the single surviving reply. This is a direct example of attractive material overwhelming a hidden terminal threat.
2. [gjmn6za2](https://www.mit.edu/~6.7980/fow/?tab=arena&game=gjmn6za2): Mist's queen moves to **b3 at ply 41**, is visible to us at frame 42, and stays there. At ply 54 we play **Kf8–g8**, entering its diagonal. We had **18** surviving alternatives. The attacker was not a newly invented hypothesis: it had been observed on that very square. This is a high-value persistence/memory regression case.

Across the full sample, Mist's hidden threats with a surviving reply caused **19 failures in 51 opportunities**; threats with a visible attacker caused **2 in 36**. These are descriptive, opponent-mixed counts, not a causal estimate of the gain from hiding a piece. They nevertheless identify behavior we currently underproduce against Mist.

## Its exploitable weakness: concealed cover plus pressure near the king

Seven of Mist's 17 losses finish with its king taking a piece guarded by a hidden rook. **Four were already forced losses at that final decision**: every pseudo-legal reply left its king capturable. Those four demonstrate successful attacks, but not a preference for bait over a safe move.

The three clean, avoidable examples are:

| Replay | What the opponent built | Mist's fatal move | Surviving alternatives on the true board |
|---|---|---|---|
| [7hrv61xz](https://www.mit.edu/~6.7980/fow/?tab=arena&game=7hrv61xz), Knight Vision | g/h pawn advances; rooks doubled on the h-file; **Rh2–h7** at ply 59, backed by hidden Rh1 | **Kg8xh7**, ply 60 | **20**, including Kg8–f8. Mist was not in check before taking. |
| [o7pac9wt](https://www.mit.edu/~6.7980/fow/?tab=arena&game=o7pac9wt), TA P | Rg1 behind a pawn on g7; then **h6–h7** at ply 61 attacks Kg8 | **Kg8xg7**, ply 62 | Only **Nf6xh7**. Mist finished eight material points ahead and still lost. |
| [vjpcef4g](https://www.mit.edu/~6.7980/fow/?tab=arena&game=vjpcef4g), Knight Vision | Hidden Rc1 behind **Qd1–h1** at ply 60, attacking Kh2 | **Kh2xh1**, ply 61 | Only **Kh2–g3**. |

There is valuable negative evidence too. Over all games, Mist faced **33 turns in 13 games** where a king capture would lose to cover entirely hidden in its decision observation, while some other move survived. It chose the fatal capture **three** times, declining it on **30** turns. Nineteen of the 33 turns included hidden rook cover. These turns are correlated within games and include different bait pieces and cover types; **3/33 is not a universal bait probability**.

In `o7pac9wt`, it avoids Kxg7 at plies **48, 50, 52, 54, 56, 58 and 60**. At 48 it takes the queen on g7 with a knight instead. Only after the h-pawn creates a king threat at ply 61 does it take with the king. This gives us a more useful exploit than a blanket “Mist is greedy”: **make the safe reply less obvious, remove alternative capturers, and maintain concealed backing coverage.** Knight Vision's rook offer also proves that check is not necessary in every successful case.

Pawn pressure is a way to reach those positions, not a guaranteed counter. An opposing f/g/h pawn reached its fifth rank or beyond after Mist castled kingside in 12/17 losses **and 17/41 wins**. Opponent strength, game duration and prior material advantage confound this association. Simply paying a bonus for any advanced pawn would miss the actual line-opening/battery mechanism.

## Next experiment to share with Fable

Fable's [deception candidate](../../../chatroom/025-fable-mist-and-deception.md) already implements a concealed-cover bait term. That is the right concrete experiment to develop; this audit supplies better cases and conditioning.

1. **Attack preparation:** use the inferred castled king region to favor useful g/h-file breaks and rook batteries, then consider a pawn/rook/queen offer beside the king. Price the preparatory moves too: a one-ply bait bonus alone cannot build the position from the opening.
2. **Conditional response prediction:** distinguish an unforced offer from a checked king with one escape; account for other pieces that can safely take the bait, visible cover, repeated earlier refusals and the specific bait piece. Begin with this small feature model before adding a larger style architecture. Keep Fable's constant-probability candidate as the comparison.
3. **Preserve attacking resources:** probe the queen-for-rook exchanges and our observed-attacker memory failures alongside offense. Mist converted all eight of its sustained leads against us; reaching a rook battery with a queen already lost is a different proposition.
4. **Target Mist explicitly:** use the existing refreshed pure-network Mist replica for paired seeds and both colors. It is a behavior proxy, not arena Mist. First inspect whether it reproduces the three positive bait cases **and the 30 declines**, replaying complete histories for recurrent state. Cases used for its training are diagnostic only; reserve newly completed Mist games for prediction validation and the arena for strength confirmation.
5. **Style recognition:** combine legal observation history with likely castling/opening patterns; do not require certain opponent identity before trying a useful battery. True replay moves such as a hidden ...Qa5 are labels, not available classifier inputs. We can specialize and accept measured costs elsewhere; unseen-team generalization is not a required gate.

## Data and reproducibility

- [summary.json](summary.json): totals, opening frequencies, matchup records, clock/terminal/threat counts.
- [anatomy.json](anatomy.json): per-game moves, captures, threats, king-capture choices, safe replies, replay SHA-256 hashes.
- [tactical-cases.json](tactical-cases.json): **41 diagnostic decisions**: our eight fatal king decisions and Mist's 33 hidden-bait opportunities, including declines. Repeated positions are grouped by game, not independent trials.
- [analyze_mist.py](../../tools/analyze_mist.py): offline analyzer; no requests, training or engine changes.
- Raw cache: `/media/henrytan/seagate/iamavirus/astra/corpus/mist-v1-20261009/`. All 64 replays reused Fable's existing mirror; no duplicate replay downloads. `games.json`, `leaderboard.json`, `versions.json`, `fetched_at.txt`, and `cache-receipt.json` preserve acquisition metadata.

Validation reconstructed **4,788 frames** from the initial position using the course `FowBoard`: every move, full board, both observations, castling/en-passant state, and terminal outcome agree. Safe alternatives use the actual fog rules, not orthodox check restrictions or a FEN with missing history. Hiddenness is evaluated in the defender's decision observation; for offered threats, that is the observation after the attacking move.

```sh
.venv/bin/python astra-submissions/tools/analyze_mist.py \
  --corpus /media/henrytan/seagate/iamavirus/astra/corpus/mist-v1-20261009 \
  --referee /home/henrytan/git/fow-starter/referee.py \
  --output astra-submissions/analysis/mist-v1-20261009/anatomy.json
```

The referee/script hashes are recorded in the output. Full replay truth is used only for retrospective labels. No new bot ZIP or playing-strength claim is produced by this analysis.
