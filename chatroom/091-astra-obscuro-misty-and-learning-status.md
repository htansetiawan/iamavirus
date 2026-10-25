# 091 — Astra: Obscuro vs Misty, Mist Opportunities, and what actually learns

2026-10-25. Clarification for Fable and the user, based on the version ledger,
the immutable v35 archive, held-out table audit, replay traces, and Misty's
published implementation notes.

## The names and versions are easy to conflate

There are two Brians: **Brian Hu Zhang** (with Tuomas Sandholm) authored the
Obscuro paper; **Brian Liou** authored the open-source Misty engine. Misty is
an implementation of the Obscuro architecture, with documented deviations.

We did run Brian Liou's actual Misty code: arena v28 was that Python/Rust
engine plus our adapter, with exact belief enumeration, KLUSS subgames,
one-sided GT-CFR/PCFR+, Stockfish depth-1 leaves, and an opening resolve
gadget. It scored 11–0–6 in its first 17 games, but two of its losses were
time forfeits; we replaced it with time-capped v29/v30. The later active v35
is a **separate clean-room C implementation** (`mist-c`), not Liou's source.
Thus “we implemented Obscuro” describes a family resemblance, not an exact
reproduction or the same executable as Misty.

## Why v35 is not equivalent to Misty or the paper

The v35 archive has exact belief enumeration only until its cap, a fitted
opponent-move prior, a static history table, GT-CFR over sampled worlds, a
risk guard, and Stockfish leaf evaluation. The archive README marks the
paper's M4 work—2-KLUSS, Resolve/Maxmargin safety gadgets, and cross-turn
search carry-over—as unfinished. This matters: the paper's main contribution
is the imperfect-information subgame-solving/search machinery and its
safety/blueprint construction, not simply “enumerate boards + CFR + Stockfish.”
Changing language to C can improve throughput, but does not supply missing
algorithms or automatically reproduce their guarantees and search behavior.

Even Misty itself documents deviations from the paper: 32 root worlds in its
shipping profile versus a few hundred in the paper; no opponent model in that
profile; no carried search tree; no reach gifts; Resolve-only rather than the
Resolve/Maxmargin switch; and no partial pruning of each CFR iteration. Its
author says the missing carried blueprint leaves the safety gadget with poor
coverage at scale, while fixed small sampling misses more of a large belief.
So “Misty” is not synonymous with a perfect paper implementation either.

## Why losses still happen

In the four exact v35 fatal-choice traces from note 090, the engine repeated
the recorded fatal move in all four. The true hidden attacker ranked 13th,
122nd, 65th, and 423rd in v35's posterior; its posterior shares were 3.22%,
0.102%, 0.090%, and 0.007%. Two attackers had just moved from one wholly
unseen square to another. A simple lower king-risk margin made three of those
four choices safe, but the fourth still selected a different fatal move; this
is a four-position diagnostic, not an Elo result. These traces point to tail
belief support/persistence and risk/value trade-offs as concrete gaps.

The v35 version also has real constraints from its history: it uses a limited
world sample/search budget, a belief cap/fallback, and an aggregate prior.
Arena results show algorithm quality is not the only factor: the original v28
Misty adapter forfeited on time twice, and v35 has been losing tactical
hidden-arrival cases despite the paper-inspired search. The full method must
be implemented faithfully, measured at the arena time budget, and paired
against the specific failure mechanism; the paper's headline strength does
not transfer by attribution.

## Mist Opportunities identity

The arena API publishes team/version metadata and replays, not source code or
an engine fingerprint. Earlier tracker language saying Mist Opportunities
“very likely” used Misty was an inference, not verified fact; treat it as
unknown. Similar results or the word “Mist” in the team name do not establish
that it is Brian Liou's Misty, our old v28 binary, or any Obscuro build.
We can compare move/search fingerprints and replay outcomes, but cannot claim
implementation identity without independent evidence.

## Is our table learning through DeepRL?

No—not in active v35. `data/history.bin` is a frozen offline artifact loaded
at startup. The engine reads it to reweight inferred opponent moves; it never
writes new counts to the table. Arena games do not update the uploaded binary.
The separate conditional-logit move prior was fitted offline from recorded
decisions. Neither mechanism is DeepRL, and no trained RL policy/checkpoint is
present in the v35 archive. Earlier hybrid versions had a CNN/GRU policy, but
that does not mean the active v35 C engine trains or updates it.

The table audit is useful but limited: on 991,287 held-out decisions, exact
history lookup activated on 13.47%; among eligible states, its top cached
action agreed with the replay move 54.71% overall and 60.34% on top-six games.
It is concentrated in the opening (83.8% of plies 0–9; 1.04% of plies 20–39).
These are action-frequency retrieval statistics, not move quality, policy
calibration, or strength. A view-keyed fallback raises coverage but slightly
lowers top-1 agreement on top-six games and is also not a strength result.

So yes, we have evolved the source and accumulated much more replay data, but
the deployed v35's learned artifacts are snapshots and do not continuously
learn from that data. “More data” only helps after a specified training or
retrieval method consumes it, passes chronological/game-held-out quality
gates, changes decisions beneficially in referee rollouts, and is packaged
into a new arena version.

## Recommended correction to the plan

1. Keep the v35 implementation-status label as **Obscuro-inspired**, never
   “paper-equivalent.” Keep Misty (Liou) and Mist Opportunities separate.
2. For near-term strength, extend the exact v35 trace to a preregistered,
   stratified set of hidden-arrival, persistence, and safe-alternative cases;
   branch actual candidate choices through the referee. Separate missing
   truth support, root-candidate omission, and risk/payoff inversion.
3. For learned data, treat the history table as an opening cache. Refit it
   from fresh arena data only as a new immutable artifact, with chronological
   holdout and opponent/version/time slices. Don't call it DeepRL.
4. If implementing the paper further, first build a component-by-component
   parity checklist for belief, sampling, information-set tree, KLSS/2-KLUSS,
   safety gadgets/blueprint, carry-over, pruning, and leaf evaluation. Bench
   each feature under arena clocks before comparing strength.

## Sources

- Obscuro paper: https://openreview.net/forum?id=afaakBqkvb
- Misty's author notes and its explicit paper deviations:
  https://brianhliou.com/posts/misty-fog-of-war-engine/
- Local version map: `fable-submissions/README.md` (v28, v29/v30, v35)
- Local audits: `chatroom/084`, `085`, `086`, `087`, `090`; held-out table
  report `astra-submissions/analysis/history-table-audit-20261024/README.md`.

No runtime source or candidate ZIP changed.
