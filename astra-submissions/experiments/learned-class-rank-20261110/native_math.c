/* Math-only adapter. Mirrors native float history blending after its original
 * legal-action normalizer. No histories, parent boards or model state here. */
#include <math.h>
#include <stdint.h>

int astra_history_logp(int n, const float *model_logp,
                       const unsigned *counts, unsigned total, float *out) {
    if (n < 0 || n > 256 || !model_logp || !counts || !out) return -1;
    for (int j = 0; j < n; ++j)
        if (!isfinite(model_logp[j]) || model_logp[j] > 0 || counts[j] > total) return -1;
    if (total < 3) total = 0;
    for (int j = 0; j < n; ++j)
        out[j] = total ? logf(((float)counts[j] + 4.0f * expf(model_logp[j])) /
                             ((float)total + 4.0f)) : model_logp[j];
    return 0;
}
