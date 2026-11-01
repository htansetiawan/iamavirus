/* Exercise the actual frozen belief_shrink, not a sampler reimplementation. */
#include "../temporal-belief-20261101/native/belief.c"
#include <assert.h>
int main(void) {
    fow_init(); zobrist_init(); Belief b; belief_init_start(&b, WHITE, 3);
    b.rng = 11012026;
    const double weights[3] = {.6, .3, .1};
    double sums[3] = {0}, squares[3] = {0};
    const int trials = 300000;
    for (int t = 0; t < trials; ++t) {
        b.count = 3;
        for (int i = 0; i < 3; ++i) {
            pos_start(&b.items[i]);
            if (i) { pos_remove(&b.items[i], 57); pos_put(&b.items[i], i == 1 ? 40 : 42, BLACK, KNIGHT); }
            b.hist[i] = (uint64_t)i; b.recent[i] = 0;
            b.logw[i] = (float)log(weights[i]);
        }
        belief_shrink(&b, 2); assert(b.count == 2);
        double total = exp(b.logw[0]) + exp(b.logw[1]);
        for (size_t j = 0; j < b.count; ++j) {
            int i = (int)b.hist[j]; double share = exp(b.logw[j]) / total;
            sums[i] += share; squares[i] += share * share;
        }
    }
    printf("{\"trials\":%d,\"input\":[0.6,0.3,0.1],\"estimated_mean\":[", trials);
    for (int i = 0; i < 3; ++i) printf("%s%.12g", i ? "," : "", sums[i] / trials);
    printf("],\"standard_errors\":[");
    for (int i = 0; i < 3; ++i) {
        double mean = sums[i] / trials;
        printf("%s%.12g", i ? "," : "", sqrt((squares[i] / trials - mean * mean) / trials));
    }
    puts("]}"); belief_free(&b); return 0;
}
