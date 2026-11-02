#define _POSIX_C_SOURCE 200809L
#include "gtcfr.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int base_gtcfr_decide(const Belief *, const GtcfrParams *, SearchResult *);
static double now(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

/* Diagnostic only: both engines receive the SAME immutable belief, exclusion
 * mask, parameters and sampling seed. Separate CFR translation units keep
 * their distinct Game layouts private. Baseline chooses the protocol move. */
int astra_solver_pair(const Belief *b, const GtcfrParams *params, SearchResult *out) {
    const char *order = getenv("ASTRA_SOLVER_PAIR");
    if (!order) return gtcfr_decide(b, params, out);
    const int first = atoi(order) != 0;
    const char *budget = getenv("ASTRA_PAIR_SECONDS");
    int base_ok = 0;
    for (int i = 0; i < 2; ++i) {
        const int enabled = i == 0 ? first : !first;
        GtcfrParams p = *params; p.seconds = budget ? atof(budget) : 2.5;
        SearchResult candidate;
        const double start = now();
        int ok = enabled ? gtcfr_decide(b, &p, &candidate) : base_gtcfr_decide(b, &p, out);
        fprintf(stderr, "astra-solver-pair enabled=%d elapsed=%.9f ok=%d\n", enabled, now()-start, ok);
        if (!enabled) base_ok = ok;
    }
    return base_ok;
}
