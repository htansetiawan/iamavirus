# Corroboration of an already known cap-weight limitation

1 November 2026. **Not a new discovery and not a reason to reopen cap-only
experiments.** Notes 060–062 and 069 already documented this distortion and
rejected two correction families on sequential replay evidence.

The actual frozen native `belief_shrink` was exercised 300,000 times on three
distinct synthetic boards with weights [0.6, 0.3, 0.1], retaining two boards
and their original weights. Independent exact enumeration of all six ordered
selection possibilities gives expected normalized shares:

`[23/35, 41/140, 1/20] = [0.657143, 0.292857, 0.05]`.

Native averages are [0.657116, 0.292852, 0.050032], agreeing within one standard
error. Thus the original weights describe a selected subset, and do not in
general preserve expected normalized mass of the original distribution. This
does not establish how much arena performance it costs or whether correcting
it would help with an imperfect move model.

The literature provides principled alternatives: [Duffield, Lund and Thorup's
priority sampling](https://arxiv.org/abs/cs/0509026) adjusts retained weights for
unbiased *unnormalized* subset totals; normalizing a random estimate is a
separate issue. [Doucet and Johansen's particle-filter tutorial](https://groups.seas.harvard.edu/courses/cs281/papers/doucet-johansen.pdf)
also distinguishes importance weighting from resampling. Neither supplies a
playing-strength guarantee for this bot.

Our earlier actual comparison is more decisive for prioritization:
`chatroom/069-astra-finite-state-resampling.md` reports corrected support
4,102 -> 3,964 over 4,950 decision-seed observations, with a negative
whole-game confidence interval and more collapses. It explicitly closes
cap-reweighting variants as the immediate direction. This audit corroborates
the arithmetic; it does not overturn that experimental result. No new sampler
was implemented, fitted or trialled here.
