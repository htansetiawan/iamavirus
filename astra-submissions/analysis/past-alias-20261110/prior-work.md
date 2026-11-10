# Distinction from existing work

- M4 branch a521bf8 already implements knowledge closure and carried blueprint
  gadgets. m4search.c `carry()` retains same-ply frontiers and connected off-I
  branches; the negative October continuation and match tests stand.
- In `m4_decide()` each fresh sample gets `scope=s->next_scope++` and its own
  new group. `their_key()` includes that scope. The fresh sample does not
  receive past-own-move alternatives simply by having an opponent history hash.
- The deployed v38 GT-CFR builds every world from our current information set
  and gives them a common current own root history. It has no M4 carry path.
- 251 shows that copying more histories within this current-world support only
  splits equivalent response problems. 062 already mines future action aliases.
  This miner instead varies an earlier OWN move, preserving BOTH intervening
  opponent views and its same own reply, then tests a common current action.
- It uses TRUE completed replay ancestors and the hidden recorded reply, so it
  is an offline oracle feasibility producer, not an observation-only agent.
  Native belief ancestry and blueprint reaches remain implementation gaps.
- Successful witnesses prove legal opponent-compatible alternatives exist in
  these contexts. They do not supply justified range weights, safe resolving,
  a stronger value function or an earned playing candidate.

Immutable reviewed source extracts are adjacent, from our own M4 branch.
The proposal follows the architectural issue in
`docs/opponent-uncertainty-20261102.md`, not a claim that KLUSS is new.
[Primary paper, appendix C.6](https://arxiv.org/html/2506.01242v2#A3.SS6).
