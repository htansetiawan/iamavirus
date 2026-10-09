# 027 — SunTzu: a hierarchy of strategies learned as residual codes

*Fable, 2026-10-10 00:00 UTC. The user's vision: strategies form a hierarchy with roles (chief, generals, officers), learned as codebooks (VQ-VAE / RVQ-VAE) from replays and from grandmaster and Sun Tzu principles, triggered by context and refined online against the opponent. Working name for the system and the paper: **SunTzu**.*

## The command structure

| level | role | decides | input (what it knows) | output |
| --- | --- | --- | --- | --- |
| 0 | **Intelligence** | what is true now | observations, particle belief + king fusion, shelter class, opponent classifier | beliefs: enemy king square and shelter, opponent style, material, clock |
| 1 | **Chief (Sun Tzu)** | grand strategy | beliefs + game phase + opponent style | one code from codebook 1: hunt the king / fortress and wait / ambush / convert the lead / scout / survive (bare-king defense) |
| 2 | **Generals** | operational plan | chief's code + beliefs | one residual code from codebook 2: e.g. kingside storm with hidden battery, queen ambush on raid squares, diagonal check vs uncastled king, bait with hidden cover |
| 3 | **Officers** | tactics | general's code + position | one residual code from codebook 3: e.g. h-pawn push, rook lift, x-ray battery, sacrifice, waiting move |
| 4 | **Soldiers** | the move | the plan's priors and terms | the engine: search + matrix game over hypotheses, with the plan conditioning the policy prior and the plan terms |

Residual vector quantization (RVQ) matches this shape: the first codebook captures the coarsest description of a stretch of play, each further codebook encodes what the previous levels left unexplained. Level 1 is the chief's choice; levels 2 and 3 refine it.

## What each code means, and where it comes from

1. **Data.** Windows of 8 own moves from the 40,000+ mirrored games, both sides, described by features we already compute: move-taxonomy tags (captures, captures from the fog, fog routes, king threats, unseen king threats, sacrifices, queen raids, vision gains and losses, king moves), pawn advances toward the enemy king, heavy pieces on files into the king zone, material and its trend, own and enemy shelter class, phase.
2. **Codebook.** An RVQ-VAE (encoder → 3 residual codebooks of 16 codes → decoder reconstructing the features and the next window's outcome signals). Train on the GPU.
3. **Naming the codes.** Each code is named by the tags it over-represents (e.g. "fog ambush", "kingside storm", "fortress shuffle"), checked against the chess-book and Sun Tzu principles in notes 024–026, and by which teams use it (style fingerprints).
4. **The book.** For each opponent and phase: which code sequences won and lost. That table is the strategy book: lookup and apply.

## Triggering and adaptation

- **Trigger:** the chief picks the level-1 code from beliefs and the opponent classifier (Penumbra's lesson: identify the opponent, then switch).
- **Adapt:** a bandit over codes per opponent class, updated from game results and from the opponent's observed responses inside the game (e.g. a king that takes bait raises the bait plan's value).

## Execution

The engine stays the soldier. A plan acts through knobs that already exist or are half-built: the policy prior (RL network), belief fusion, storm credit, deception (bait), risk charges, time. Later, the network takes the code as an input (a style-conditioned policy).

## Evaluation and the paper

- Belief: probability on true squares and shelter accuracy (`tools/belief_eval.cc`).
- Plans: the gym's strike and giveaway corpora; games against replicas and the open-source Misty (Obscuro); arena by opponent class.
- Paper: *SunTzu: hierarchical strategy codes for imperfect-information games* — learned residual strategy codes from human and bot play, belief-conditioned plan selection, and exploitation of an equilibrium searcher's belief dilution.

## First step (started)

Window dataset from top-team games → RVQ-VAE (3 × 16 codes) → code usage by team and code-to-outcome tables.
