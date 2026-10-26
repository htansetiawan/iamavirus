# Review 2 — Architectural choices

**Astra · 25 October 2026 · Proposal for human review · About 4 minutes**

**Choose the architecture by demonstrated decisions and complete games.** Our
current controller is a baseline we can replace. The
[state brief](https://github.com/htansetiawan/iamavirus/blob/main/docs/review-current-state.md)
separates deployed components from research infrastructure.

## What the research actually says

There is no common tournament ranking all these systems. Published Dark Chess
results, MIT arena ratings, and results from other hidden-information games
must remain separate.

| Reference | Core idea in plain language | Evidence and limit |
|---|---|---|
| [Obscuro](https://arxiv.org/html/2506.01242v2) | Track plausible worlds; reason about both players' knowledge; grow and solve a strategy tree during each move | 16–4 against the then top-rated human; 85.1% score against predecessor ZS21. Strongest direct FoW reference found |
| [ZS21](https://papers.nips.cc/paper_files/paper/2021/file/c96c08f8bb7960e11a1239352a479053-Paper.pdf) | Make imperfect-information search tractable by limiting how many layers of players' knowledge it considers | Earlier strong Dark Chess system, developed further by Obscuro; not a separate breakthrough to stack on it |
| [ESCHER](https://web.mit.edu/~gfarina/www/2023/escher_iclr23/2206.04122.pdf) | Learn action values and regrets through self-play, retaining knowledge across games | Over 90% against DREAM/NFSP baselines; their Dark Chess networks saw only the current observation. This does not establish elite playing strength |
| [Misty](https://brianhliou.com/posts/misty-fog-of-war-engine/) | An inspectable, runnable implementation of the Obscuro family | Useful comparison opponent; documented departures mean its results cannot stand in for Obscuro's |

**CFR versus Deep CFR:** “regret” measures how much better an alternative would
have performed against the same opponent strategies. CFR uses that feedback to
improve a strategy. Deep CFR learns neural approximations instead of storing an
enormous table for every distinguishable situation. It is a training algorithm;
Obscuro is a complete playing system using a CFR variant during search.
[Deep CFR](https://proceedings.mlr.press/v97/brown19b/brown19b.pdf).

## Three implementation choices

| Choice | What we would build | Principal risk |
|---|---|---|
| **A. Stronger search** | Improve fidelity to Obscuro, including carried strategies and modelling opponent knowledge | Deeper search still fails if beliefs or excluded actions are wrong |
| **B. Learned controller** | A history-aware ESCHER-style learner that selects moves directly | Training cost and generalisation are uncertain; strong baseline wins may not transfer to arena leaders |
| **C. Hybrid** | A persistent learned model proposes useful alternatives; search evaluates and refines them | Integration can combine both systems' errors and consume the clock |

**Astra's recommendation:** develop one bounded learned-controller pilot,
then compare it alone and inside search with the existing search reference.
Give the learner observation history, not just a snapshot. Initially use its
output to allocate search effort; retain Stockfish while that interface is tested.
Do not undertake several simultaneous evaluator, representation and guard rewrites.

For the learning loop, [Student of Games](https://pmc.ncbi.nlm.nih.gov/articles/PMC10651118/)
offers a useful design: search generates difficult questions, including unplayed
alternatives; additional computation refines targets; training improves later
searches. Its results are in other games, and its representation needs adaptation
to FoW. Combining these ideas is our engineering proposal, not a proven algorithm.

## What humans should decide before the next run

1. **Scope and ownership:** name one candidate and one accountable owner; confirm
   what enters the deployed move selector and what remains research.
2. **Resources and deadline:** fix a compute cap and a 24-hour review checkpoint.
   A run reaching its cap produces a report, not an automatic extension.
3. **Evidence:** check rules and information boundaries, then compare complete
   games at equal total turn budgets, including inference and belief updates.
   Test both colours against frozen opponents; use later unseen games to confirm.
4. **Decision:** continue, revise, or stop based on results. Lower training loss
   and fewer mistakes on selected replays are useful diagnostics, not release criteria.

Each review should contain the exact artifact, measured results and uncertainty,
resources spent, and one proposed next action. The data pipeline and simulator
already exist; no broad rebuild is required to begin this comparison.

This brief records a proposal, not approval or a new training launch.
[Detailed literature review and corrections to the earlier memo](https://github.com/htansetiawan/iamavirus/blob/main/astra-submissions/specs/dark-chess-literature-20261025.md).
