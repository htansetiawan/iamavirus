/* Experimental execution policy, not a safe-resolving gadget.
 * Mode 0: existing argmax. Mode 1: raw last-iterate sampling (ablation).
 * Mode 2: top-three actions, stable support since half the wall budget;
 * excluded mass goes to argmax. No new value, risk or temperature parameter. */
#ifndef ASTRA_ROOT_MIX_H
#define ASTRA_ROOT_MIX_H
#include <assert.h>
#include <errno.h>
#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

typedef struct { unsigned char stable[256]; uint64_t observations; } RootMixTrack;

static void root_mix_observe(RootMixTrack *t, const double *x, int n, double elapsed, double budget) {
    assert(n > 0 && n <= 256);
    if (elapsed < .5 * budget) return;
    for (int a = 0; a < n; ++a) {
        assert(isfinite(x[a]) && x[a] >= 0);
        t->stable[a] = (t->observations ? t->stable[a] : 1) && x[a] > 0;
    }
    ++t->observations;
}

static int root_mix_probs(const RootMixTrack *t, const double *x, int n, int mode, double *out) {
    assert(n > 0 && n <= 256 && mode >= 0 && mode <= 2);
    int best = 0; double total = 0;
    for (int a = 0; a < n; ++a) {
        assert(isfinite(x[a]) && x[a] >= 0);
        if (x[a] > x[best]) best = a;
        total += x[a]; out[a] = 0;
    }
    assert(total > 0 && isfinite(total));
    if (!mode || (mode == 2 && !t->observations)) { out[best] = 1; return best; }
    if (mode == 1) { for (int a = 0; a < n; ++a) out[a] = x[a]/total; return best; }
    /* Top three of the final distribution, ties resolved by action order.
       Filtering stability does not refill the set from lower-ranked actions. */
    int top[3] = {-1,-1,-1};
    for (int a = 0; a < n; ++a) {
        for (int k = 0; k < 3; ++k) if (top[k] < 0 || x[a] > x[top[k]]) {
            for (int j = 2; j > k; --j) top[j] = top[j-1];
            top[k] = a; break;
        }
    }
    out[best] = 1;
    for (int k = 0; k < 3; ++k) {
        int a = top[k];
        if (a >= 0 && a != best && t->stable[a]) { out[a] = x[a]/total; out[best] -= out[a]; }
    }
    assert(out[best] > 0);
    return best;
}

static uint64_t root_mix_random(uint64_t *state) {
    uint64_t z = (*state += UINT64_C(0x9e3779b97f4a7c15));
    z = (z ^ (z >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94d049bb133111eb);
    return z ^ (z >> 31);
}

static int root_mix_at_quantile(const double *p, int n, double u) {
    assert(u >= 0 && u < 1); double total = 0; int last = -1;
    for (int a = 0; a < n; ++a) { assert(p[a] >= 0 && isfinite(p[a])); total += p[a]; if (p[a] > 0) last = a; }
    assert(last >= 0 && total > 0);
    double target = u * total, cumulative = 0;
    for (int a = 0; a < n; ++a) { cumulative += p[a]; if (target < cumulative) return a; }
    return last; /* roundoff at the upper endpoint; never a zero-mass action */
}

static uint64_t root_mix_seed(void) {
    const char *e = getenv("MIST_ACTION_SEED");
    if (e && *e) {
        char *end; errno = 0; uint64_t value = strtoull(e, &end, 10);
        if (errno || *end || *e == '-') { fprintf(stderr,"astra-mix: invalid action seed\n"); exit(2); }
        fprintf(stderr,"astra-mix: action seed source=explicit\n"); return value;
    }
    uint64_t value = 0; FILE *f = fopen("/dev/urandom","rb");
    if (f) {
        size_t got = fread(&value,1,sizeof(value),f); fclose(f);
        if (got == sizeof(value)) { fprintf(stderr,"astra-mix: action seed source=os\n"); return value; }
    }
    /* Portable fallback for a restricted runtime; not a cryptographic promise. */
    struct timespec now; clock_gettime(CLOCK_REALTIME,&now);
    value = (uint64_t)now.tv_sec ^ ((uint64_t)now.tv_nsec << 32) ^ (uint64_t)getpid();
    fprintf(stderr,"astra-mix: action seed source=clock-pid-fallback\n");
    return root_mix_random(&value);
}

static int root_mix_pick(const RootMixTrack *track, const double *x, int n, int mode, double *probability) {
    double p[256]; int best = root_mix_probs(track,x,n,mode,p), selected = best;
    if (mode && p[best] < 1) {
        static int initialized = 0; static uint64_t rng;
        if (!initialized) { rng = root_mix_seed(); initialized = 1; }
        double u = (root_mix_random(&rng) >> 11) * (1.0/9007199254740992.0);
        selected = root_mix_at_quantile(p,n,u);
    }
    *probability = p[selected];
    if (mode) fprintf(stderr,"astra-mix: mode=%d argmax=%d selected=%d p=%.9g observations=%" PRIu64 " alternatives_mass=%.9g\n",
                      mode,best,selected,p[selected],track->observations,1-p[best]);
    return selected;
}
#endif
