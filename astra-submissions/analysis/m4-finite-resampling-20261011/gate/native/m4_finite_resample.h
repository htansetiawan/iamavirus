#ifndef M4_FINITE_RESAMPLE_H
#define M4_FINITE_RESAMPLE_H
#include <stddef.h>
#include <stdint.h>
/* Select k distinct indices. Input log weights must be finite, 0<k<=n,
 * n<=UINT32_MAX, and 0<=offset<1. No RNG or mutable global state.
 * Output weights retain large masses and correct sampled-tail inclusion.
 * Returns 0 on success, -1 for bad input/allocation/numerical failure. */
int m4_finite_resample(const float *logw, size_t n, size_t k, double offset,
                       uint32_t *chosen, float *out_logw);
#endif
