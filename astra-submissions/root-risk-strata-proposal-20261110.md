# Review proposal: preserve tactical probability when sampling worlds

**A design for review, not an implemented candidate.** The guard comparison
and bounded data audits are now terminal. The guard candidate failed its
original gate; this proposal neither reopens it nor changes that verdict.

The next question is whether 32 weighted worlds adequately represent the
different tactical risks already present in our full belief. Exact true-board
coverage is insufficient evidence: another sampled board may contain the
same attacker. We need to measure coverage of **action consequences**.

For a legal root action a and belief world i, let L(i,a) indicate that the
move immediately loses our king under the deployed rules. With normalized
belief weights p_i, its posterior risk is r_a = sum_i p_i L(i,a). Ordinary
K-draw sampling estimates this with variance r_a(1-r_a)/K. If r_a = 0.01,
32 draws miss that failure family with probability 0.99^32, about 72.5%.
That is a mathematical example, not a measured rate for our bot.

**Proposal.** Group worlds by the complete bit vector of immediate root
failure indicators, using exactly the search's legal-move and terminal
precedence rules. Let group g have mass P_g. When there are at most K groups,
allocate at least one draw per group and distribute the remaining draws by
mass. Within a group draw according to p_i/P_g. Each draw carries chance
weight P_g/K_g; merge duplicate worlds by adding those weights.

For every action, L is constant inside each group, so:

```
sampled risk(a)
  = sum_g (P_g / K_g) sum_{j=1..K_g} L(i_gj, a)
  = sum_g P_g L(g, a)
  = exact risk over the retained belief.
```

For a fixed continuation policy, the same weighted draws remain unbiased
for its expected value. This does **not** prove unbiased equilibrium solutions
after optimizing a sampled game, lower exploitability, or improved Elo.
It also cannot recover truth lost from the belief or repair incorrect weights.
General stratification and the need for probability correction are established
Monte Carlo methods; our proposed contribution is the choice of a tactical
partition for this engine. [Mike Giles, variance-reduction lectures](https://people.maths.ox.ac.uk/gilesm/mc2013/lec2-2x2.pdf).

This is a task-directed compression: the first code is an exact consequence
signature, rather than a learned visual codebook. Worlds within one code
remain distinct for deeper search and opponent observation histories. It
does not merge their information sets. Later features could distinguish
offensive hidden threats, but that is outside this first proposal.

The first signature census costs O(N·A) attack tests for N worlds and A root
actions. Hash grouping adds expected O(N), with full signature equality
checks; it is not a magical O(log N) replacement. Keep one position copy per
world and make/unmake each action, and compute both weightings once per world.
The existing guard already measures related risks, so sharing a census may
reduce repeated work, but source inspection alone does not establish savings.
For more than K groups, either revert to the old sampler or use a separately
specified coarse partition. Never discard a group's probability mass and
then claim exact risk preservation.

The diagnostic should first measure group counts, census cost, and baseline
versus stratified error for each action's true full-belief risk. Use unused
control histories, not only losing seats. Preserve root action sets, cap,
model, clock and search budget. Count true safety-family coverage separately
from exact true-board coverage. Only then decide whether native integration
earns an equal-clock decision gate and independent full games. No GPU needed
for this first measurement; no launch or promotion is authorized by this note.

The new paired loss audit supplies an eligibility warning. At the Black
terminal root, both guards retain only g7g8 and exclude the two safe moves
g7f6 and g7h6. Stratifying the unchanged action set cannot recover them.
The first follow-up should export full-belief support and fitted/sharpened
per-action risks after search, without feeding truth to the actor. Distinguish
lost support, probability calibration, sampling error and action censorship
before selecting an intervention. A losing move in one hidden true state is
not by itself proof that the Bayesian decision was wrong.

The full census is now complete: the true rule state survives among 2,344
worlds. The chosen capture's sharpened fatal mass is 0.01390%, versus 11.65%
and 10.00% for the two actual escapes. The ordinary sample misses the capture
failure family. Six fatality signatures suffice for all 15 root actions in
this one population. These facts support a concrete diagnostic, not a claim
of population-wide miscalibration.

One companion idea replaces the king-risk margin with a payoff bound. Let
nonfatal continuations have verified bounds [L,U], and immediate root loss
pay -kappa. Then each root action satisfies:

```
lower(a) = (1-r_a)*L - kappa*r_a
upper(a) = (1-r_a)*U - kappa*r_a
```

An action is dominated when its upper bound is below another's lower bound.
The frozen v38 GT-CFR source uses tanh for frontier values and +/-1 for later
king terminals, giving [L,U]=[-1,1]; the larger loss applies only at the root.
With kappa=2 in this census, certain-fatal moves are dominated, while all
three king choices survive the interval test. The existing 0.02 margin keeps
only the queen capture. The interval test says the escapes cannot be ruled
out from immediate risk alone; it does not say their continuation is better.

First isolate ordinary/stratified sampling crossed with old/bounded root
pruning on the same belief. Keep the queen guard issue separate: queen loss
is not terminal and supplies no such payoff bound. A queenless specialist is
a plausible first scope. Runtime bounds, legality ambiguity, fallback for
too many signatures and balanced-control tests must precede any full-game
candidate. This remains a design for review, not an implemented change or
an instruction to reopen the failed union-guard candidate.

Obscuro's search reasons over a sampled subgame with information sets; that
sets a constraint on this experiment: preserve each sampled world's actual
opponent history and chance mass. Stratification supplies neither KLUSS nor
safe resolving, which remain separate architectural gaps. [Zhang and Sandholm](https://arxiv.org/html/2506.01242v2).
