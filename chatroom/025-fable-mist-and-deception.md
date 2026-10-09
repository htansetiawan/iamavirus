# 025 — Mist Opportunities, 64 games later, and deception

*Fable, 2026-10-09 22:00 UTC. All 64 of Mist's games (ingested by team). The user: "to win games we need to employ deceptions".*

## Mist now

41–6–17, rating 1630 (above us at 1575). Against us **8–2–0**. It loses to Strongly Invisible (0–0–4), Knight Vision (0–0–2), duck (1–2–3), TA Baseline P (11–0–3).

- **Openings:** as Black ...c6 ...d5 then ...Nf6 (23) or ...Qa5 (8); as White 1.d4 c3 Nf3 (22) or 1.d4 d5 Nc3 (5). Castles kingside in 59 of 64.
- **How it beats us (all 8):** one of our rooks, queens or knights steps onto a square covered by a Mist piece we cannot see; 3 points down at a median ply 44.5, never back.
- **How it loses:** in **7 of its 17 losses its king took a piece put next to it and walked into a hidden rook**:

| game | opponent | bait next to Mist's king | hidden cover |
| --- | --- | --- | --- |
| 7hrv61xz | Knight Vision | rook h7 | rook h1 |
| o7pac9wt | TA Baseline P | pawn g7 | rook g1 |
| rxn0geme | Strongly Invisible | queen g7 | rook g1 |
| w23syovy | TA Baseline P | queen g7 | rook g1 |
| jjagavan | duck | queen g2 | rook b2 |
| vjpcef4g | Knight Vision | queen h1 | rook c1 |
| ucrmeu8z | TA Baseline S | queen b3 | rook b8 |

The recipe: a rook behind the queen on a line aimed at the castled king, then the queen (or a rook or pawn) next to the king. Mist cannot see the rook and takes.

## Deception in our engine

Our search plays every hypothesis as if the opponent saw everything, so a guarded bait looks pointless to it: the full-information opponent sees the guard and declines. The new term (`FOW_BAIT_P`, branch `deception` `a1ff75b`, off by default) changes that cell by cell: when our moved piece stands next to their king, their king can take it, and once it has, our pieces that hit the square are all on squares none of theirs can see, the cell's value blends in that chance of capturing the king, in win-probability terms (a guarded bait gets a real boost; a true sacrifice still needs a high chance to pay). Tests reproduce Mist's g7/g1 pattern and its visible-cover counter-case.

Gates: against the **pure-network** Mist replica (refreshed on 51 training games, 45.9% move match; the search-guided replica would decline the bait because it runs our full-information search), with v20 on the same seeds, plus the v20 bytes and the TA Baseline P replica. Next for deception: building the hidden battery deliberately (rook behind queen on the line to the believed king), which needs the king location the belief fusion now provides.
