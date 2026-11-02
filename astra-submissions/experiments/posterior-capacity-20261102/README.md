# 232: development screen of posterior-objective capacity

231 changed the objective with 26 coefficients and gained only 0.0205 nats on
its held-out primary decisions. 228's move-trained interactions improved average
move prediction but regressed surprise captures. Test the combination before
spending another prospective holdout: interactions trained directly for the
posterior, with both linear and move-trained controls.

Use exactly 231's 400 training and 80 validation games. Its 80 test games are
excluded. This is reused development data, not an independent confirmation.
The 26-variable quadratic logit has 357 coefficients: 26 linear terms, 325
pair interactions, and squares of six continuous features. Compute x'Qx as
sum((xQ)*x), retaining only 26 columns per action instead of expanding a
331-column interaction matrix. A sparse C inference function exports the same
formula; no model from 228 or 231 initializes the fits.

Four model/objective combinations, each with ridge 0.001 and 0.01. Adam 0.03,
60 full-batch steps, evaluation every five steps, zero initialization. Same
history blend, transition temperature, incoming beliefs, game weights and
exact-prefix limits as 231. CPU only on cores 2–3; no GPU service touched.
Maximum 45 minutes. Preserve every curve and choose by primary validation
posterior NLL. Keep output metadata separate from prediction objects.

Development advancement requires quadratic-posterior gain >=0.10 nats versus
the original prior, >=0.05 versus linear-posterior and >=0.05 versus
quadratic-move training; no >0.02 regression on later decisions or at least
20 surprise captures; no all-case regression or support failure. This screen
only determines whether to design a larger, independently tested fit. It
cannot authorize filter integration, a ZIP, or a strength claim. If it fails,
close this configuration rather than inspecting 231's old test again.

Preflight checks fused versus explicit interactions and gradients, native C
agreement and bit-identical zero residual. Reconstruction must match 231's
feature hashes and baseline probabilities. Independent NumPy checks verify
every selected validation prediction and selection. Publish the source and
plan before fitting. No update to Fable's runtime source.
