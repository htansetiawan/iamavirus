#define _POSIX_C_SOURCE 200809L
#include "gtcfr.h"
#include "sfeval.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double now(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

/* Diagnostic only. Both calls use the SAME immutable belief and search code.
 * Fresh worker processes isolate scorer history and exclude startup from the
 * equal search budget. No replay truth enters this process. */
int astra_solver_pair(const Belief *b, const GtcfrParams *params, SearchResult *out) {
    const char *order = getenv("ASTRA_SOLVER_PAIR");
    if (!order) return gtcfr_decide(b, params, out);
    const int first = atoi(order) != 0;
    const char *budget = getenv("ASTRA_PAIR_SECONDS");
    const char *original = getenv("MIST_STOCKFISH");
    const char *candidate = getenv("ASTRA_SF_CANDIDATE");
    const int both_off = getenv("ASTRA_PAIR_CONTROL") != NULL;
    int base_ok = 0;
    for (int i = 0; i < 2; ++i) {
        const int enabled = i == 0 ? first : !first;
        GtcfrParams p = *params; p.seconds = budget ? atof(budget) : 2.5;
        SearchResult answer;
        if (original) {
            sf_stop();
            if (enabled && !both_off && !candidate) { fprintf(stderr,"missing candidate scorer\n"); exit(2); }
            setenv("ASTRA_SF_ALLCHILDREN", enabled && !both_off ? "1" : "0", 1);
            const char *path = enabled && !both_off ? candidate : original;
            if (!sf_start(path)) { fprintf(stderr,"scorer startup failed\n"); exit(3); }
        }
        const double start = now();
        const int ok = gtcfr_decide(b, &p, &answer);
        fprintf(stderr, "astra-solver-pair enabled=%d elapsed=%.9f ok=%d\n", enabled, now()-start, ok);
        if (!enabled) { *out = answer; base_ok = ok; }
    }
    if (original) sf_stop();
    return base_ok;
}
