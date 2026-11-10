# How native alternatives can enter search without inventing probabilities

The native producer now generates locally legal alternatives from our private
inputs. The next unresolved question is their reference measure. More aliases
do not by themselves establish opponent uncertainty or a useful strategy.

For a previous local reference tree, let `c(p)` be its chance/range weight,
`x(a|I)` our previous reference behavior, and `y(b|J)` the opponent's behavior.
At a cut after our move `a` and its reply `b`, three different quantities appear:

\[
 r_{\rm cf}(p,a,b)=c(p)x(a\mid I),\qquad
 r_{\rm opp}(p,a,b)=y(b\mid J),\qquad
 w(p,a,b)\propto r_{\rm cf}r_{\rm opp}.
\]

This is a two-ply example. A longer tree uses the corresponding full prefix
products. The existing M4 gadget expects chance-times-our reach and opponent-
only reach separately. Its conditional distribution within an opponent group
uses normalized `r_cf`; its group prior and reference values need the opponent
reach and previous continuation policy. Neither quantity is a board count.

## The native posterior cannot identify these reaches

Consider a previous own-action probability `x=1/5` and two parent branches:

| Reference | `c` | `y` | Normalized current joint weights | Resolve group prior |
|---|---|---|---|---|
| A | `(1/2, 1/2)` | `(9/10, 1/10)` | `(9/10, 1/10)` | `(7/10, 3/10)` |
| B | `(9/10, 1/10)` | `(1/2, 1/2)` | `(9/10, 1/10)` | `(1/2, 1/2)` |

The same posterior gives different valid reference reaches and group priors.
An exact rational preflight verifies this counterexample. Recovering those
parts by dividing current native weights or spreading them uniformly over
aliases is unjustified. Native weights also merge histories and use a
tempered move model, strengthening the reason to preserve a separate
reference receipt rather than infer one after the fact.

There is another important distinction: the engine's raw last-iterate
distribution `x_ref` versus the pure argmax move it actually executes. For
an earlier chosen argmax, all *different* past own actions have zero mass
under that pure executed distribution. They can have positive mass under
`x_ref`. Choosing a search blueprint as reference is a deliberate local
approximation; its probabilities are not calibrated claims about what the
deployed opponent observed or believes.

## Preserve the actual information sets

An alternative shares the parent's complete opponent-history key only after
both intervening views and the opponent's same reply have been checked.
Its own history differs because its earlier own action differs. Keep those
own information sets and legal action rows distinct. Never put these boards
into the posterior that represents our actual known pieces and history.

An opponent reference action distribution must be one distribution across
every node of its information set. Re-evaluating a full-board move model
independently in each alternative can violate that requirement. A saved CFR
behavior keyed by the full private history and action row can supply it where
covered. Missing history/row support is a missing reference, not permission
to invent a small epsilon or a probability from duplicate counts.

Full native-path repetition certification is also still absent. Even a
correct reference measure cannot turn a merely locally legal two-ply alias
into a certified nonterminal full-game history.

## What is old and what would be new

M4 already carries continuations, builds Resolve/Maxmargin gadgets and keeps
off-information-set branches. Its prior negative matches stand. Separate
scopes for fresh samples are consistent with the paper: Figure 9 explicitly
places a newly sampled state in a singleton opponent information set. Adding
fresh past-action alternatives would extend that treatment, not repair an
omitted paper instruction. The paper also makes clear that KLUSS lacks a
general worst-case safety guarantee. [Primary source](https://arxiv.org/html/2506.01242v2)

The previous history-only test251, response-policy tests207/211 and M4
continuation tests do not supply this missing reference. Repeating their
matches would not answer the new support question. Conversely, new ancestry
code does not overturn any of their negative evidence.

## The next bounded decision: does the raw reference support the aliases?

Before a new range builder or search treatment, run a read-only support
screen on the same32 DEVELOPMENT selections. At the preceding own decision,
run exactly one guarded v38 GT-CFR search for0.75s and save its complete raw
root row before it is freed. All other prefix decisions remain forced and
unsearched. Then force the recorded historical own action, process the next
private views and enumerate up to32 native contexts at the target root.
Only private views/moves/clocks enter the actor; no truth or hidden reply.

For each context, report the previous actual action's reference probability,
its agreement with the searched argmax, and total reference mass on distinct
native alternatives. Separate guard exclusions from zero CFR probabilities.
The primary necessary-support criterion counts only historical argmax matches
with actual probability above1e-6 and at least1% raw mass on alternatives.
Require these in at least20% of sampled contexts across at least4 games.
Off-policy prefixes remain visible in the denominator and report; never
force their reference probabilities positive. Costs and outcomes are not Elo.

Failure closes this fixed support configuration. Passing earns a design for
retaining opponent reference rows, continuation values and complete draw
histories. It does not prove a useful gadget, an on-policy effect, a stronger
decision or a reason to launch another playing batch. No new version is
reserved.

[Native producer evidence](analysis/private-ancestry-20261110/README.md) ·
[Support-screen plan](analysis/reference-support-20261110/plan.json) ·
[Prior experiment register](RESEARCH_REGISTER.md)

## Frozen support-screen result — November 10, 05:11 UTC

The [32-prefix probe](analysis/reference-support-20261110/README.md) completes
and fails its declared gate:104/740 contexts,14.05%, across3games instead of
at least20% across4. All policy rows, private inputs and7,425 local aliases
pass independent audit. Only185 contexts match the preceding searched argmax;
371 have historical-action reference probability at most1e-6. Old M4's forced-
prefix zero-reach warning applies here too. Do not reinterpret this as an
on-policy playing test or proof that all future carry methods fail.

No range integration, larger probe, match or parameter sweep is earned.
The raw rows and native ancestry interface remain reusable artifacts. A
materially different successor must resolve its reference and data-population
contract before spending further search time, and preserve this negative gate.
