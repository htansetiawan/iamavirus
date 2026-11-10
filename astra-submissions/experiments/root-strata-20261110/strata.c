#define _POSIX_C_SOURCE 200809L
#include "strata.h"
#include <limits.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static const RootCensus *active;
static int enabled;

static double now(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)t.tv_sec + 1e-9*t.tv_nsec;
}

static uint64_t hash_signature(const TacticalSignature *s) {
    uint64_t h = UINT64_C(1469598103934665603);
    for (int i = 0; i < ASTRA_SIGNATURE_WORDS; ++i) {
        h = (h ^ s->loss[i])*UINT64_C(1099511628211);
        h = (h ^ s->win[i])*UINT64_C(1099511628211);
    }
    return h;
}

static void set_bit(uint64_t *bits, int a) { bits[a/64] |= UINT64_C(1) << (a%64); }

static int reject(RootCensus *c, const char *reason, double started) {
    c->eligible = 0; c->reason = reason; c->seconds = now()-started;
    return 0;
}

int root_census_build(RootCensus *c, const Belief *b, const MoveList *moves, int budget) {
    const double started = now();
    memset(c, 0, sizeof(*c));
    c->belief = b; c->moves = *moves; c->budget = budget;
    c->reason = "eligible";
    if (!b->count || b->count > INT_MAX || budget < 1 || budget > ASTRA_MAX_DRAWS ||
        moves->count < 1 || moves->count > 256 || (b->us != WHITE && b->us != BLACK))
        return reject(c, "unsupported dimensions", started);
    c->weights = malloc(b->count*sizeof(double));
    c->group_of = malloc(b->count*sizeof(int));
    if (!c->weights || !c->group_of) return reject(c, "allocation failure", started);

    double max_lw = -INFINITY;
    for (size_t i = 0; i < b->count; ++i) {
        const double lw = b->logw ? b->logw[i] : 0;
        if (!isfinite(lw)) return reject(c, "nonfinite weight", started);
        if (lw > max_lw) max_lw = lw;
    }
    const double temp = belief_temperature();
    if (!(temp > 0) || !isfinite(temp)) return reject(c, "invalid temperature", started);
    double fitted_total = 0;
    /* Constant-size move stamp table avoids a nested scan over moves. */
    uint32_t *legal_stamp = calloc(UINT16_MAX+1u, sizeof(uint32_t));
    int table[1024];
    memset(table, -1, sizeof(table));
    if (!legal_stamp) return reject(c, "allocation failure", started);
    char first_view[65]; observation(&b->items[0], b->us, first_view);
    int overflow = 0;
    for (size_t i = 0; i < b->count; ++i) {
        Position p = b->items[i];
        char view[65]; observation(&p, b->us, view);
        if (p.side != b->us || king_square(&p, b->us) < 0 || king_square(&p, b->us^1) < 0 ||
            memcmp(view, first_view, 64)) {
            free(legal_stamp); return reject(c, "inconsistent information state", started);
        }
        if (p.by_type[QUEEN] & p.by_color[b->us]) {
            free(legal_stamp); return reject(c, "own queen present", started);
        }
        MoveList legal; generate_moves(&p, &legal);
        if (legal.count != moves->count) {
            free(legal_stamp); return reject(c, "legal move sets differ", started);
        }
        for (int a = 0; a < legal.count; ++a) legal_stamp[legal.moves[a]] = (uint32_t)i+1;
        const double lw = (b->logw ? b->logw[i] : 0)-max_lw;
        const double w = exp(lw), fw = exp(lw/temp);
        if (!(w > 0) || !(fw > 0)) {
            free(legal_stamp); return reject(c, "underflowed weight", started);
        }
        c->weights[i] = w; c->total += w; fitted_total += fw;
        TacticalSignature signature = {{0}, {0}};
        for (int a = 0; a < moves->count; ++a) {
            if (legal_stamp[moves->moves[a]] != (uint32_t)i+1) {
                free(legal_stamp); return reject(c, "legal move sets differ", started);
            }
            Undo undo; make_move(&p, moves->moves[a], &undo);
            /* Same terminal precedence as GT-CFR: taking their king wins
             * even when the mover's king is also attacked. */
            if (king_square(&p, b->us^1) < 0) {
                set_bit(signature.win, a); c->win[a] += w;
            } else if (mover_left_king_capturable(&p)) {
                set_bit(signature.loss, a); c->loss[a] += w; c->fitted_loss[a] += fw;
            }
            unmake_move(&p, moves->moves[a], &undo);
        }
        if (overflow) { c->group_of[i] = -1; continue; }
        size_t slot = hash_signature(&signature) & 1023;
        while (table[slot] >= 0 && memcmp(&c->group[table[slot]].signature, &signature, sizeof(signature)))
            slot = (slot+1) & 1023;
        if (table[slot] < 0) {
            if (c->groups == budget) { overflow = 1; c->group_of[i] = -1; continue; }
            table[slot] = c->groups++;
            c->group[table[slot]].signature = signature;
        }
        TacticalGroup *g = &c->group[table[slot]];
        g->mass += w; ++g->count; c->group_of[i] = table[slot];
    }
    free(legal_stamp);
    for (int a = 0; a < moves->count; ++a) {
        c->loss[a] /= c->total; c->win[a] /= c->total;
        c->fitted_loss[a] /= fitted_total;
    }
    if (overflow) return reject(c, "signature count exceeds sample budget", started);

    c->members = malloc(b->count*sizeof(int));
    c->cumulative = malloc(b->count*sizeof(double));
    if (!c->members || !c->cumulative) return reject(c, "allocation failure", started);
    size_t cursor[ASTRA_MAX_DRAWS], offset = 0;
    double sum[ASTRA_MAX_DRAWS] = {0};
    for (int g = 0; g < c->groups; ++g) {
        c->group[g].offset = offset; cursor[g] = offset; offset += c->group[g].count;
    }
    for (size_t i = 0; i < b->count; ++i) {
        const int g = c->group_of[i]; const size_t j = cursor[g]++;
        c->members[j] = (int)i; sum[g] += c->weights[i]; c->cumulative[j] = sum[g];
    }
    for (int g = 0; g < c->groups; ++g) c->group[g].mass /= c->total;
    c->eligible = 1; c->seconds = now()-started;
    return 1;
}

void root_census_free(RootCensus *c) {
    free(c->group_of); free(c->members); free(c->weights); free(c->cumulative);
    memset(c, 0, sizeof(*c));
}

static double uniform(uint64_t *state) {
    uint64_t z = (*state += UINT64_C(0x9E3779B97F4A7C15));
    z = (z ^ (z >> 30))*UINT64_C(0xBF58476D1CE4E5B9);
    z = (z ^ (z >> 27))*UINT64_C(0x94D049BB133111EB);
    z ^= z >> 31;
    return ((double)(z >> 11)+0.5)*(1.0/9007199254740992.0);
}

typedef struct { int group; double fraction; } Remainder;
static int remainder_order(const void *pa, const void *pb) {
    const Remainder *a = pa, *b = pb;
    if (a->fraction != b->fraction) return a->fraction > b->fraction ? -1 : 1;
    return (a->group > b->group)-(a->group < b->group);
}
typedef struct { int index; double mass; } Draw;
static int draw_order(const void *pa, const void *pb) {
    const Draw *a = pa, *b = pb;
    return (a->index > b->index)-(a->index < b->index);
}

int root_strata_sample(const RootCensus *c, int draws, uint64_t *rng, int *idx, double *prob) {
    if (!c->eligible || draws != c->budget || c->belief->count <= (size_t)draws)
        return belief_sample(c->belief, draws, rng, idx, prob);
    int allocation[ASTRA_MAX_DRAWS], assigned = 0;
    Remainder rem[ASTRA_MAX_DRAWS];
    for (int g = 0; g < c->groups; ++g) {
        const double extra = (draws-c->groups)*c->group[g].mass;
        allocation[g] = 1+(int)floor(extra); assigned += allocation[g];
        rem[g] = (Remainder){g, extra-floor(extra)};
    }
    qsort(rem, (size_t)c->groups, sizeof(*rem), remainder_order);
    for (int j = 0; assigned < draws; ++j, ++assigned) ++allocation[rem[j].group];
    Draw sampled[ASTRA_MAX_DRAWS]; int n = 0;
    for (int g = 0; g < c->groups; ++g) {
        const TacticalGroup *group = &c->group[g];
        const size_t end = group->offset+group->count;
        const double total = c->cumulative[end-1];
        for (int k = 0; k < allocation[g]; ++k) {
            const double target = uniform(rng)*total;
            size_t lo = group->offset, hi = end-1;
            while (lo < hi) {
                const size_t mid = lo+(hi-lo)/2;
                if (c->cumulative[mid] < target) lo = mid+1; else hi = mid;
            }
            sampled[n++] = (Draw){c->members[lo], group->mass/allocation[g]};
        }
    }
    qsort(sampled, (size_t)n, sizeof(*sampled), draw_order);
    int distinct = 0;
    for (int k = 0; k < n; ) {
        int j = k+1; double mass = sampled[k].mass;
        while (j < n && sampled[j].index == sampled[k].index) mass += sampled[j++].mass;
        idx[distinct] = sampled[k].index; prob[distinct++] = mass; k = j;
    }
    return distinct;
}

int root_interval_avoid(const RootCensus *c, double kappa, Move *avoid) {
    if (!c->eligible || !isfinite(kappa)) return -1;
    if (kappa < 1) kappa = 1;
    double low[256], high[256], best = -INFINITY;
    for (int a = 0; a < c->moves.count; ++a) {
        const double cont = fmax(0, 1-c->loss[a]-c->win[a]);
        low[a] = c->win[a]-kappa*c->loss[a]-cont;
        high[a] = c->win[a]-kappa*c->loss[a]+cont;
        if (low[a] > best) best = low[a];
    }
    int n = 0;
    /* Strict dominance, conservatively allowing floating point roundoff. */
    for (int a = 0; a < c->moves.count; ++a)
        if (high[a] < best-1e-12) avoid[n++] = c->moves.moves[a];
    return n;
}

void root_strata_activate(const RootCensus *c, int use_strata) { active = c; enabled = use_strata; }

int astra_root_sample(const Belief *b, int draws, uint64_t *rng, int *idx, double *prob) {
    if (enabled && active && active->belief == b) return root_strata_sample(active, draws, rng, idx, prob);
    return belief_sample(b, draws, rng, idx, prob);
}
