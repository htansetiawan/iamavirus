#include "redistribute.h"
#include <assert.h>
#include <float.h>
#include <stdio.h>
#include <string.h>

static uint32_t rng = UINT32_C(3531111);

static uint32_t draw(void) {
    rng = rng * UINT32_C(1664525) + UINT32_C(1013904223);
    return rng;
}

int main(void) {
    double max_error = 0.0;
    unsigned identity = 0, redistributed = 0;
    for (int trial = 0; trial < 4096; ++trial) {
        const int n = trial % 257;
        float native[256], learned[256], out[256];
        uint8_t quiet[256];
        int count = 0;
        for (int j = 0; j < n; ++j) {
            const float offset = trial % 5 == 0 ? -1000.0f : 0.0f;
            native[j] = offset - (float)(draw() % 100000) / 1600.0f;
            learned[j] = trial % 7 == 0 ? native[j] : offset - (float)(draw() % 100000) / 1600.0f;
            quiet[j] = trial % 11 == 0 ? j == 0 : (draw() >> 31) != 0;
            count += quiet[j];
        }
        preserve_quiet_mass(native, learned, quiet, n, out);
        long double sum_native = 0.0L, sum_out = 0.0L;
        for (int j = 0; j < n; ++j) {
            assert(isfinite(out[j]));
            if (!quiet[j] || count < 2 || trial % 7 == 0) {
                assert(memcmp(out+j,native+j,sizeof(float)) == 0);
                ++identity;
            }
            sum_native += expl((long double)native[j]);
            sum_out += expl((long double)out[j]);
        }
        if (n) {
            double error = (double)fabsl(logl(sum_native) - logl(sum_out));
            assert(error < 1e-4);
            if (error > max_error) max_error = error;
        }
        redistributed += count >= 2 && trial % 7 != 0;
    }
    printf("{\"trials\":4096,\"identity_entries\":%u,\"redistributed\":%u,\"max_log_mass_error\":%.9g}\n",
           identity, redistributed, max_error);
    return 0;
}
