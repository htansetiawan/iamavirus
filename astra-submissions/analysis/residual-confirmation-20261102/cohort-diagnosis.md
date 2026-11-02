# Post-result cohort diagnosis

The newer-game safeguard failed. This diagnostic does not change that decision.

| Axis | Older difference reweighted to newer composition | Actual newer difference |
|---|---:|---:|
| material_phase | -0.01126 | +0.01298 |
| material_balance | -0.01059 | +0.01298 |
| sf_probability | -0.01064 | +0.01298 |

Each axis is a separate descriptive comparison. It does not identify a causal distribution shift.

## older_unused

| Axis / bin | Weight share | Conditional difference | Contribution |
|---|---:|---:|---:|
| material_phase / 30–59 material | 37.3% | -0.00546 | -0.00204 |
| material_phase / 60+ material | 35.4% | -0.00752 | -0.00266 |
| material_phase / under30 material | 27.3% | -0.02238 | -0.00611 |
| material_balance / ahead3+ | 16.7% | -0.00844 | -0.00141 |
| material_balance / behind3+ | 23.2% | -0.02164 | -0.00503 |
| material_balance / within2 | 60.1% | -0.00728 | -0.00437 |
| sf_probability / .1–.3 | 16.3% | -0.01967 | -0.00321 |
| sf_probability / .3–.7 | 42.4% | -0.00370 | -0.00157 |
| sf_probability / .7–.9 | 11.4% | -0.01617 | -0.00184 |
| sf_probability / .9+ | 18.2% | -0.01425 | -0.00259 |
| sf_probability / under.1 | 11.8% | -0.01364 | -0.00160 |

## new_date

| Axis / bin | Weight share | Conditional difference | Contribution |
|---|---:|---:|---:|
| material_phase / 30–59 material | 35.6% | +0.01867 | +0.00665 |
| material_phase / 60+ material | 34.3% | +0.00153 | +0.00053 |
| material_phase / under30 material | 30.1% | +0.01929 | +0.00581 |
| material_balance / ahead3+ | 21.2% | +0.00753 | +0.00160 |
| material_balance / behind3+ | 21.3% | +0.00635 | +0.00136 |
| material_balance / within2 | 57.4% | +0.01745 | +0.01003 |
| sf_probability / .1–.3 | 14.3% | -0.02656 | -0.00381 |
| sf_probability / .3–.7 | 42.8% | +0.02000 | +0.00856 |
| sf_probability / .7–.9 | 10.0% | -0.00506 | -0.00051 |
| sf_probability / .9+ | 21.9% | +0.01567 | +0.00344 |
| sf_probability / under.1 | 10.9% | +0.04873 | +0.00530 |

## Newer pair contributions

These names join public replay metadata; they are not runtime features. Small groups are noisy.

| Pair | Games | Mean difference | Contribution |
|---|---:|---:|---:|
| Farsight / Mist Opportunities | 3 | +0.33793 | +0.00805 |
| IAmAVirus / Mist Opportunities | 2 | +0.40272 | +0.00639 |
| Crimson Fog / Mist Opportunities | 3 | +0.10113 | +0.00241 |
| Decent Chess Bot / Greek Gift | 2 | +0.10589 | +0.00168 |
| Strongly Invisible / duck | 2 | +0.10183 | +0.00162 |
| Greek Gift / Knight Vision | 4 | +0.04606 | +0.00146 |
| Greek Gift / Mist Opportunities | 2 | +0.08415 | +0.00134 |
| HYPOTHERMIA / Instructors | 4 | +0.04033 | +0.00128 |
| Instructors / Knight Vision | 4 | +0.03332 | +0.00106 |
| Crimson Fog / HYPOTHERMIA | 2 | +0.06595 | +0.00105 |
| Decent Chess Bot / IAmAVirus | 2 | +0.06533 | +0.00104 |
| Cranberry Lemon / Strongly Invisible | 2 | +0.06481 | +0.00103 |
