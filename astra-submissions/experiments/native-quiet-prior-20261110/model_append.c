/* Appended to an exact copy of native movemodel.c, whose theta_full is static.
 * Original move_features/move_logits bodies stay byte-for-byte unchanged.
 * Reuse each full feature vector for both the original dot product and the
 * frozen quiet residual; do not compute the costly board features twice. */
#include "native_head.h"
#include "weights.h"
#include "quiet.h"

void astra_full_logp(const Position *p, const MoveList *moves, Move previous,
                     int learned, float *out) {
    float x[256 * 26], base[256], features[MM_FEATURES];
    static const float zero[22] = {0};
    static const float zeroq[22 * 22] = {0};
    for (int j = 0; j < moves->count; ++j) {
        move_features(p, moves->moves[j], previous, 1, features);
        float logit = 0;
        /* Same order/type as original move_logits, including zero weights. */
        for (int k = 0; k < MM_FEATURES; ++k) logit += theta_full[k] * features[k];
        base[j] = logit;
        memcpy(x + 26 * j, features, 26 * sizeof(float));
    }
    astra_quiet_logp(x, base, moves->count, 22,
                    learned ? astra_fixed_linear : zero,
                    learned ? astra_fixed_quadratic : zeroq, out);
}
