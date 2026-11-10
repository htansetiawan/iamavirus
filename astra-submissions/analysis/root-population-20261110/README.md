# Full-population census: retained truth, low weighted trap probability

Original session 35063 exits 0. The observer runs **after both paired
searches**; it exports all 2,344 retained worlds and exactly reproduces the
solver's 32 sampled worlds. The independent course audit verifies all
35,160 move/world labels, observations, rule metadata and weighted sums.
No truth entered the actor. This one-core reconstruction differs from the
earlier replay's 2,263 worlds; it is not the original live population.

The true placement **and** board/side/castling/EP/halfmove state are present
at index 1,585. Their sharpened mass is 0.0000037045; the power-recovered
flatter mass is 0.0000631916. These are engine weights, not calibrated
probabilities certified from this one selected loss.

| King action | Truth | Full sharpened risk | Flatter risk | 32-world risk | Both masks |
|---|---|---:|---:|---:|---|
| g7g8 | Fatal | 0.01390% | 0.16203% | 0% | Keep |
| g7f6 | Safe | 11.65121% | 24.48208% | 6.25% | Remove |
| g7h6 | Safe | 10.00460% | 22.26367% | 6.25% | Remove |

No striding error occurs here: the guard visits every world. The retained
population has six distinct root fatality signatures. It contains the
actual failure family, but gives it tiny mass; ordinary 32-draw sampling
will usually miss it. Guard action removal then prevents searching the two
actual escapes even if a different sampler includes that family.

This rules out missing physical support **at this reconstructed root**.
It does not prove global model miscalibration, identify when the live game
went wrong, or establish the escapes' expected continuation value. Before
another intervention, measure support and event-risk calibration on a
balanced set of games, and distinguish weights from the hard decision rule.
The separate root-risk stratification document remains a review proposal.

The source/plan were pushed at 0598613e before execution. The first setup
failed before actor creation due to a missing subprocess proxy constant;
that receipt is retained and a fresh 20-world/sample-fidelity preflight
passes. This did not change the C observer or any playing source body.

See [audit.json](audit.json), [plan.json](plan.json) and
[case/population.json](case/population.json).
