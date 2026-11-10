#ifndef ASTRA_CAP_CORRECTION_H
#define ASTRA_CAP_CORRECTION_H
#include <math.h>

/* Native rank key t_i=log(-log(U_i))-log(w_i), smaller is better.
 * cutoff is the smallest EXCLUDED key (rank k+1), not the last included key.
 * q_i = 1-exp(-exp(log(w_i)+cutoff)); retained mass estimate is w_i/q_i.
 * Equivalent Gumbel estimator: Kool et al. JMLR2020 eq21–23, Appendix B/C.
 * This is a mass estimator; self-normalizing it is still biased for finite k.
 * It is not an alternative move-model coefficient or a guard threshold. */
static inline double cap_corrected_logweight(double logw, double cutoff) {
    if (isinf(cutoff) && cutoff > 0) return logw; /* entire population kept */
    const double d = logw+cutoff;
    if (d > 8) return logw; /* exp(-exp(d)) is below double precision */
    const double z = exp(d);
    if (d < -20) {
        /* Avoid subtracting two large negative logs when q is tiny.
         * log(w/q) = -cutoff + z/2 - z²/24 + O(z⁴). */
        return -cutoff+z/2-z*z/24;
    }
    return logw-log(-expm1(-z));
}
#endif
