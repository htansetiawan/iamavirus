# What the continuation labels can teach

Astra, 2 November 2026. Review note written while the frozen budget pilot runs;
it does not change that pilot or authorize a bulk fit. This revisits the
[25 October literature/design review](../../specs/dark-chess-literature-20261025.md)
now that private-history continuation mechanics are executable.

## Name the target before choosing the network

Let x be the true environment state, h0/h1 the two private action-observation
histories, c the clocks, and pi a pair of fixed reconstructed policies with a
specified computation budget. A completed continuation supplies one sample G
of the terminal return under that policy pair. Repeated continuations estimate

    V_pi(x, h0, h1, c) = E[G | x, h0, h1, c; pi].

This is a policy-conditioned history value. A censored run supplies no terminal
return. Neither one sample nor its average is an equilibrium certificate.
Different prefixes from one source game and branches of one prefix are
correlated; all belong in the same dataset split and uncertainty unit.

Our previous board-plus-current-visibility predictor omits h0/h1 and c. It
therefore averages over those missing variables in its training distribution.
Changing a CNN to attention or compressing it cannot restore information the
input contract excludes. A prediction error on a historical game also does
not, by itself, identify the value of that position under a different policy.

## What the research supports

ReBeL represents the search input with a public belief state and learns values
for information states within it. Its training uses search-derived value
targets; it is not simply terminal-outcome regression on complete boards.
Its guarantees require its stated assumptions. Our single reconstructed
trajectory does not supply the public ranges that representation needs.
[Brown et al., NeurIPS 2020, sections 3–6](https://proceedings.neurips.cc/paper_files/paper/2020/file/c61f571dbd2fb949d3fe5ae1608dd48b-Paper.pdf).

Student of Games combines GT-CFR with learned counterfactual values/policies.
Training includes outcomes and additional searches on queries encountered
during earlier searches, including unplayed situations. Its input and
re-solving contracts matter; a scalar board regressor is not that system.
[Schmid et al., Student of Games](https://arxiv.org/pdf/2112.03178).

Obscuro deliberately uses a practical node evaluator, Stockfish, inside its
imperfect-information search. Its conclusion identifies learned evaluation and
continuation strategies as further directions; this is not evidence that
arbitrary outcome labels can replace its evaluator without testing.
[Zhang and Sandholm, section 5](https://arxiv.org/html/2506.01242v2#S5).

## Consequences for the next implementation

1. Retain both private histories, clocks, policy/binary hashes, seed, source
   trajectory and branch identity in the training environment. The exported
   actor input must contain only the actor's permitted information. Store
   histories once with prefix references, as experiment 241 already does.
2. Compare a history-conditioned critic with a matched board-only control
   before assuming the extra data solves representation error. A privileged
   training critic and an observable deployed actor are different interfaces.
3. To learn action improvements, collect actual alternative-action
   continuations, not just a reward for the move the current policy chose.
   Alternatives must be available from the actor's information, and their
   clock convention must be fixed. This intervention is not implemented by
   241/242; they currently evaluate the policies' own continuation choices.
4. Keep a small reference subset at the intended deployment budget. A faster
   generator may change search, belief thinning and targets. Agreement on the
   four 242 prefixes cannot validate a broad cheap-data substitution.
5. A learned root critic, a proposal policy and a CFR frontier are distinct
   integration choices. Any CFR frontier must specify its belief/reach and
   continuation-strategy semantics. Do not assign arbitrary predicted returns
   to every leaf and describe the result as Deep CFR or ReBeL.

The immediate decision after 242 is a costed data/target pilot, not another
capacity sweep. Its contract needs the policy budget, natural-terminal and
censor handling, source-level split, number of independent prefixes and
branches, and the exact runtime input that the eventual student can receive.
No model, history table, guard threshold or submitted ZIP changes here.
