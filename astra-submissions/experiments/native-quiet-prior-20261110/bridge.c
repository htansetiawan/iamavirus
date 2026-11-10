/* Test the fused adapter with the exact existing native state/history bridge. */
#include "../deployed-prior-comparison-20261102/prior.c"
#include "native_head.h"

/* Both log probabilities and the actual native temperature-two/history result
 * are exported. No new model, sampling or truth-dependent weighting. */
int adapter_scores(uint16_t *moves, float *base, float *zero, float *learned,
                   float *base_weight, float *zero_weight, float *learned_weight,
                   float *x, unsigned *counts, unsigned *total) {
    MoveList list; generate_moves(&current, &list);
    float raw[256], top = -INFINITY;
    move_logits(&current, &list, previous, 1, raw);
    for (int j = 0; j < list.count; ++j) if (raw[j] > top) top = raw[j];
    double sum = 0;
    for (int j = 0; j < list.count; ++j) sum += exp((double)(raw[j] - top));
    const float normalizer = top + (float)log(sum);
    astra_full_logp(&current, &list, previous, 0, zero);
    astra_full_logp(&current, &list, previous, 1, learned);
    *total = history_counts(histories[current.side], &list, counts);
    for (int j = 0; j < list.count; ++j) {
        moves[j] = list.moves[j];
        base[j] = raw[j] - normalizer;
        float features[MM_FEATURES]; move_features(&current, list.moves[j], previous, 1, features);
        memcpy(x + 26 * j, features, 26 * sizeof(float));
        const float probabilities[3] = {base[j], zero[j], learned[j]};
        float *outputs[3] = {base_weight, zero_weight, learned_weight};
        for (int k = 0; k < 3; ++k)
            outputs[k][j] = *total >= 3
                ? 2.0f * logf(((float)counts[j] + 4.0f * expf(probabilities[k])) / ((float)*total + 4.0f))
                : 2.0f * probabilities[k];
    }
    return list.count;
}

int adapter_set(const char *board, int side, uint64_t castle, int ep, int halfmove) {
    if (pos_from_board_string(&current, board, side, castle, ep)) return -1;
    current.halfmove = halfmove; previous = 0;
    for (int s = 0; s < 2; ++s) {
        char view[65]; observation(&current, s, view);
        histories[s] = history_mix(0, view_hash(view));
    }
    return 0;
}
