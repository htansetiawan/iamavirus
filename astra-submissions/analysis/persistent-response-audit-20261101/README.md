# Persistent mode changes the intended search mechanism; match trial remains open

1 November 2026. Nine first-attempt calls completed under the plan published
at `f059d22db6ace09c40b9b27c264b72196ef4a6bb`. No assertion, protocol or model
query fault. All three arms use identical sampled physical positions in each
case. This does not assert identical beliefs or trees to the earlier 213 run.

For each named root move, the table reports how much its restricted-best
value falls when **future** opponent replies are unrestricted while the first
reply retains its restriction. Own continuation and the tree are fixed within
each measurement.

| Root move / earlier case | Local projected mode | Persistent mode |
|---|---:|---:|
| Bf1-c4 / p0 White ply20 | 0.10555 | 0.02306 |
| Be7-g5 / p0 Black ply31 | 0.19165 | 0.03518 |
| Nb8-d7 / p1 Black ply17 | 0.94054 | 0.10926 |

These are finite-tree utility differences, not win probabilities or Elo.
Cross-arm trees and policies differ. The numerical reduction is descriptive;
it is not a same-tree causal estimate of the algorithm's strength effect.

## What is verified

Every pure-root decomposition confirms that removing model restrictions has
**zero effect on free-mode branch best-response values**. All restriction-gap
contributions come from the model-mode quarter of root chance. With these
leaf values in [-2,1], total dependence is bounded by 0.75. This loose bound
is checked, not a full-game safety guarantee. Sampled worlds, root weights,
legal root/reply moves and solver/tree hashes also pass 1,808 checks; 172
original replay frames validate. Eight full export fixtures pass optimized
and ASan/UBSan; the BR algorithm is byte-identical to 213's exhaustive oracle.

The local formulation still exhibits the earlier mechanism on Nd7: current
value +0.13589, best within restrictions +0.13588, first-only restricted best
-0.80466, unrestricted best -0.99329. This is not chiefly a convergence gap.
Persistent Nd7 gives -0.43122 / -0.43122 / -0.54048 / -0.68467. The persistent
search instead chooses Bf3xe4 in this run. That does not prove Bxe4 is a better
chess move; a short earlier exchange diagnostic favored Nd7.

Persistent play chooses Rd2 instead of local Bc4 in the first example, keeps
Bg5 in the second, and changes Nd7 to Bxe4 in the third. Dependence on the
**first** modeled reply remains material: for persistent Bg5, freeing that
reply costs another 0.31733 after future replies are already unrestricted.
We have reduced one source of optimism, not validated the response predictor
or repaired all strategic errors.

Root purification also remains: in the first persistent tree, the unchanged
mixed profile has a current-to-restricted-BR gap of 0.00417; forcing Rd2 gives
0.18484. The latter includes the opponent adjusting to the changed root
policy, so it is not evidence of poor mixed-profile solver convergence.

The audit takes 42–76 ms after choosing. It does not add CFR iterations or
grow the tree, and is not included in the playing binary. Cores 4–5 are now
released. The original 214 match lanes continue on 0–1 and 6–7, unchanged.
Their first two completed games are candidate wins as White without faults;
the Black games are live. Two same-colour wins are not strength evidence and
do not change any stopping rule. No release or GPU.

`analysis.json`, raw `.br.json` files, receipts, plan and source hashes preserve
all quantities. Results use reused development positions, not a held-out gate.
