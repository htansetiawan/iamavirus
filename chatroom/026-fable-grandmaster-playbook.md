# 026 — The grandmaster playbook: what wins Fog of War, top-down

*Fable, 2026-10-09 22:45 UTC. The user: work backward from the goal; learn the wisdom first (experts, the best papers), then implement it as lookup-and-apply, instead of only learning bottom-up from replays.*

## Sources

- **Obscuro** (Zhang & Sandholm, ICLR 2026; [arXiv 2506.01242](https://arxiv.org/abs/2506.01242)): first superhuman Fog of War program; beat the #1 chess.com FoW player (2318) 16–4. Exact belief, knowledge-limited subgame solving (KLUSS: model what the *opponent* knows), growing-tree CFR, purification, Stockfish leaves. Its ablations: the opponent-knowledge model mattered most.
- **Misty** ([PyPI misty-chess](https://pypi.org/project/misty-chess/), [GitHub brianhliou/misty](https://github.com/brianhliou/misty), GPL-3.0, v0.1.3, 2026-09-23): an open implementation of Obscuro. Exact enumeration of positions consistent with the observation history, KLUSS over sampled information sets, one-sided GT-CFR with PCFR+, Stockfish depth 1 at the leaves, purification. The author's own known limits: *"the belief can lose the true board past the enumeration cap, and won endgames can be drawn against a bare king."* **Mist Opportunities, new in our arena on 2026-10-09, is almost certainly Misty.**
- **Reconnaissance Blind Chess** winners ([past competitions](https://rbc.jhuapl.edu/past_competitions), [Penumbra, arXiv 2110.01810](https://arxiv.org/abs/2110.01810), [RBC 2022 report](https://proceedings.mlr.press/v220/gardner23a/gardner23a.pdf)): StrangeFish (exhaustive belief, risk-weighted aggregation); **Penumbra won 2020 by identifying the opponent and switching to a network trained for that opponent**, with a catch-all network when recognition fails — the user's classifier idea, proven in competition.
- **Kriegspiel** (Ciancarini & Favini, [metapositions, IJCAI 2007](https://mlanthology.org/ijcai/2007/ciancarini2007ijcai-representing)): human experts defend lost endings by shuttling between two squares for threefold repetition; defense lasts long against imperfect-information attackers.
- **chess.com experts** ([variant guide](https://www.chess.com/blog/EnergeticHay/fog-of-war-chess-coms-most-popular-variant), [club tips](https://chess.com/clubs/forum/view/fog-of-war-tips)): vision is the main resource; bishops on long diagonals (fianchetto); push pawns for vision; knights out early (they see and attack what cannot see them back); keep every piece protected; king safety first; do not overextend.

## Skills A–H, and where we stand

| skill | the wisdom | our status | the lookup-and-apply action |
| --- | --- | --- | --- |
| A. Know the enemy | identify the opponent, play the counter (Penumbra) | classifier 52% from early views; exploit cards (note 024) | per-opponent profiles switched by the classifier; for Mist: read Misty's code, spar against it locally |
| B. Model what they know | KLUSS: reason about the opponent's information (Obscuro's biggest factor) | none in search; first step = deception term (hidden-cover bait) | extend: their view decides their reply in our cells |
| C. Know where their king is | exact belief (Obscuro), king location = our strike ceiling (note 017) | particles 0.18 → king fusion 0.57 (middlegame) | shipped in the v22 candidate |
| D. Vision | long diagonals, advanced pawns, knights early | vision term exists (weight 0 in v20) | measure, then turn on |
| E. Never leave a piece unprotected | experts' first rule; we walk into unseen attacks 3x Mist's rate | queen charge cut queen losses 38% → 29% but no more points | protection rule for all pieces, not only the queen |
| F. King safety and bait | castle, shelter, never take bait with the king | king takes bait: 18 of 57 king captures lost the king next ply | refuse king captures of pieces that just arrived next to it unless the square is provably safe |
| G. Mix, stay unpredictable | purification, randomized openings | matrix-game mixture | keep |
| H. Endgame | bare-king defense draws; Misty cannot convert vs a bare king | repetition accepted when losing | when lost vs Misty, keep the king alive and shuttle |

## Tonight

1. **Spar against the real Misty** locally (pip package + Stockfish + an adapter to our referee protocol): an exact opponent for testing the bait trap and the bare-king defense, instead of a replica.
2. Upload the v22 candidate (king fusion + deception) and watch it by opponent class.
