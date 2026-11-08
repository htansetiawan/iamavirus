# Our engine versus Brian Hu Zhang's Obscuro

Astra · 8 November 2026 · exact arena-v37 archive reviewed

**We implemented important Obscuro components, but the deployed engine is not a complete reproduction.** The largest discrepancy is the machinery connecting successive searches and the opponent's information, rather than the implementation language. That is a credible research priority, not a demonstrated explanation for a competitor's ranking.

## Which implementation?

Brian Hu Zhang and Tuomas Sandholm authored [Obscuro](https://arxiv.org/html/2506.01242v2). Brian Liou's [Misty](https://github.com/brianhliou/misty) is a separate Python/Rust implementation. Our local Misty matches do not test the authors' original engine, and neither implementation can be identified with an arena team solely from its name or rating.

I checked the [author's website](https://brianhzhang.github.io/), paper and public GitHub repositories. The repository listing contained four forks and no Obscuro repository. I could not locate a runnable public original or substantiate that it is written in Rust. This is a search result, not proof that no release exists. An original binary or the friend's repository/version is still needed for that specific offline duel. No such duel was run.

## Architectural comparison

The left column summarizes the paper's sections 3.1 and C.4–C.8; the right column records our own code audit. Source anchors and hashes are in the [manifest](analysis/obscuro-fidelity-20261108/review-manifest.json).

| Mechanism in the paper | What exact v37 actually does | Consequence to investigate |
|---|---|---|
| Retain previous search/strategy; add sampled worlds | Creates a fresh tree in every gtcfr_decide call and frees it after choosing | Repeated computation; no carried strategy connecting turns |
| 2-KLUSS with Resolve/Maxmargin and alternate/gift values | Chance root over our sampled belief; no deployed gadgets or persistent blueprint | Our current belief alone omits alternatives relevant to what the opponent knows |
| Conditional action value plus variance-scaled exploration | Exploration uses policy probability plus a visit bonus | Probability and action value guide expansion differently |
| Conditional purification: stable top-three mixing in Maxmargin, argmax in Resolve | Always executes argmax of the final root policy | Loses policy mixing; stochastic sampling/timing still make our overall play variable |
| Uniform world sampling; no fitted opponent model | 32 weighted draws with Stockfish; fitted move prior, sharpening and history counts | Intentional exploitation, with possible undercoverage of unexpected play |
| Stockfish 14 depth-one leaves | Stockfish 19 depth-one leaves; v38 changes scoring again | Shared evaluator family, different scores and search allocation |

Our PCFR+ last-iterate solver, best-child initialization, information-set keys and alternating one-sided expansion are real common components. Our solver already skips zero-probability opponent branches; claiming it has no pruning would be wrong. Belief deduplication merges positions and retains one representative opponent-history hash. That is another abstraction to audit, not proof that every deduplication is invalid.

The deployed king/queen filters and doubled root king-loss penalty are additional departures. They constrain the actions or utility directly; they do not reconstruct a blueprint or the opponent's information alternatives. More iterations cannot restore states that the searched game omits.

The paper's AI comparisons use five cores per player and exclude enumeration from the search allowance (Appendix D). Our two-core arena budget pays for both. Its 2-KLUSS approximation is not a worst-case safety guarantee. Hardware-normalized measurement is necessary before attributing a gap to algorithm quality.

## We have tried some pieces already

| Existing work | Recorded outcome | What remains untested |
|---|---|---|
| Astra M4 branch: carry, 2-KLUSS and gadgets | Real prototype; initial pair 1–1 included a setup failure; later repairs and small tests, never deployed | An integrated current-v37 comparison within arena resources |
| Stable root mixing | 1W–3L in a four-game stopping screen | Full gadget-conditioned selection; this tested mixing without that condition |
| Conditional-value/variance expansion | 7W–9L against v37, no faults | Interaction with the complete re-solving architecture |

Evidence: [M4 setup and repair](../chatroom/052-astra-full-games-and-root-policy.md), [later M4 screen](../chatroom/054-astra-same-tree-tradeoffs-and-settling-rejection.md), [mixing](analysis/stable-mix-20261101/README.md), [expansion](../chatroom/234-astra-conditional-value-expansion.md). These small negative results do not establish that the full paper design is weak. They also do not justify blindly repeating the same isolated changes.

## Benchmark correction found during this review

The recent 29-game Misty comparison reused a wrapper with the defect already documented in [note 028](../chatroom/028-astra-misty-adapter-conformance.md). We failed to carry that repair into the frozen benchmark. Its visible-board helper offered wrong move sets on **398/1,158 Misty turns**; our course observation tracker matched the referee on all 1,158. Wrong offered actions do not prove they were selected or explain the score difference.

Both arms used that wrapper: clean v37 scored 10½/14 and v38 scored 9/14, with an additional Misty timeout against v38. Those results remain recorded, and the failed gate stays failed. They measure play against this particular imperfect adapter, with weaker transfer to native Misty or the arena.

A [corrected separate adapter](experiments/obscuro-fidelity-20261108/misty_adapter.py) now feeds only observations and own moves to the course tracker. Its actual protocol loop passes 1,157 completed recorded turns using a spy policy; the remaining audited turn was the unanswered timeout. A real installed-Misty smoke test passes two turns per color, with no fallback, protocol fault or surviving subprocess. These are correctness checks, not strength games. Native Rust acceleration is present and now hashed; its binary was missing from the old dependency manifest. [Receipts](analysis/obscuro-fidelity-20261108/README.md).

## Recommended next decisions

1. Use the corrected, fully pinned adapter for future Misty comparisons. Preserve the old evidence. Obtain the actual original/friend implementation before claiming to test it.
2. Keep the measured v38 speed contribution: **1.57–1.68× scorer throughput and 38% more search nodes at equal time**. Its changed scores still need strength validation; the engineering result stands independently.
3. Audit the existing M4 prototype against current v37 before writing another solver. Specify the coupled reference: carried tree, opponent alternatives, gadgets and matching action execution. First measure setup cost, peak memory and semantic correctness. Do not promise that a full port will fit or gain Elo.
4. Compare that reference with v37 under identical total clocks, then use fresh opponents. Measure retained nodes, covered worlds, expansion throughput, terminal losses and score. Investigate one discrepancy at a time against the working reference rather than combining unmeasured patches.

This review implements the benchmark repair. It does not launch another strength panel, publish a numbered v38 ZIP, or change the arena bot. Fable has the findings for joint prioritization.
