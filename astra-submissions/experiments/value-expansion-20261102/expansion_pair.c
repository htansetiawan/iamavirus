#define _POSIX_C_SOURCE 200809L
#include "expansion_pair.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static double now(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec*1e-9;
}

int astra_expansion_pair(const Belief *b, const GtcfrParams *params, SearchResult *out) {
    if (!getenv("ASTRA_EXPANSION_PAIR")) return gtcfr_decide(b, params, out);
    int first = atoi(getenv("ASTRA_EXPANSION_PAIR")) != 0, ok = 0;
    const double budget = 2.5;
    for (int i = 0; i < 2; ++i) {
        const int enabled = i == 0 ? first : !first;
        setenv("MIST_EXPANSION_Q", enabled ? "1" : "0", 1);
        GtcfrParams p = *params; p.seconds = budget;
        SearchResult candidate;
        const double start = now();
        int result = gtcfr_decide(b, &p, enabled ? &candidate : out);
        fprintf(stderr, "astra-expansion-pair enabled=%d elapsed=%.9f ok=%d\n", enabled, now()-start, result);
        if (!enabled) ok = result;
    }
    unsetenv("MIST_EXPANSION_Q");
    return ok;
}
