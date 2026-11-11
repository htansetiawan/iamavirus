/* Redistribute in the already tempered domain. The caller supplies only
 * legal, surviving successors that match the received observation. */
#ifndef ASTRA_REDISTRIBUTE_H
#define ASTRA_REDISTRIBUTE_H

#include <math.h>
#include <stdint.h>

static void preserve_quiet_mass(const float *native, const float *learned,
                                const uint8_t *quiet, int n, float *out) {
    double native_top = -INFINITY, learned_top = -INFINITY;
    int count = 0, changed = 0;
    for (int i = 0; i < n; ++i) {
        out[i] = native[i];
        if (!quiet[i]) continue;
        if (native[i] > native_top) native_top = native[i];
        if (learned[i] > learned_top) learned_top = learned[i];
        changed |= native[i] != learned[i];
        ++count;
    }
    if (count < 2 || !changed) return;
    double native_mass = 0.0, learned_mass = 0.0;
    for (int i = 0; i < n; ++i) if (quiet[i]) {
        native_mass += exp((double)native[i] - native_top);
        learned_mass += exp((double)learned[i] - learned_top);
    }
    const double shift = native_top - learned_top + log(native_mass) - log(learned_mass);
    for (int i = 0; i < n; ++i) if (quiet[i]) out[i] = (float)((double)learned[i] + shift);
}

#endif
