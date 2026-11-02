#include "expansion_values.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

/* One traversal: values go upward, chance and player reaches go downward.
 * Both players' zero-probability actions remain represented. A separate value
 * per world would permit different choices inside one infoset; these sums do
 * not. Own reach cancels in the conditional value under perfect recall. */
static double walk(ExpansionValues *v, const Game *g, int id, const double *x,
                   double r0, double r1, double chance) {
    const GameNode *n = &g->nodes[id];
    ++v->nodes;
    if (n->type == NODE_TERMINAL) return n->value;
    double value = 0;
    if (n->type == NODE_CHANCE) {
        for (int a = 0; a < n->count; ++a) {
            const int edge = n->first + a;
            const double p = g->prob[edge];
            value += p * walk(v, g, g->child[edge], x, r0, r1, chance * p);
        }
        return value;
    }
    const int I = n->infoset, o = g->is_offset[I];
    const double own = n->player == 0 ? r0 : r1;
    const double mass = chance * (n->player == 0 ? r1 : r0);
    const double sign = n->player == 0 ? 1.0 : -1.0;
    if (v->seen[I] && fabs(v->own[I] - own) > 1e-12) v->recall_bad[I] = 1;
    if (!v->seen[I]) v->own[I] = own;
    v->seen[I] = 1;
    v->mass[I] += mass;
    for (int a = 0; a < n->count; ++a) {
        const double p = x[o + a];
        const double q = walk(v, g, g->child[n->first + a], x,
                              n->player == 0 ? r0 * p : r0,
                              n->player == 1 ? r1 * p : r1, chance);
        v->q[o + a] += mass * sign * q;
        value += p * q;
    }
    return value;
}

void expansion_values_refresh(ExpansionValues *v, const Game *g, const double *x) {
    if (g->n_slots > v->cap_slots) {
        v->cap_slots = g->n_slots * 2;
        v->q = realloc(v->q, (size_t)v->cap_slots * sizeof(double));
        if (!v->q) abort();
    }
    if (g->n_infosets > v->cap_infosets) {
        v->cap_infosets = g->n_infosets * 2;
        v->mass = realloc(v->mass, (size_t)v->cap_infosets * sizeof(double));
        v->own = realloc(v->own, (size_t)v->cap_infosets * sizeof(double));
        v->seen = realloc(v->seen, (size_t)v->cap_infosets);
        v->recall_bad = realloc(v->recall_bad, (size_t)v->cap_infosets);
        if (!v->mass || !v->own || !v->seen || !v->recall_bad) abort();
    }
    v->slots = g->n_slots; v->infosets = g->n_infosets;
    if (v->slots) memset(v->q, 0, (size_t)v->slots * sizeof(double));
    if (v->infosets) {
        memset(v->mass, 0, (size_t)v->infosets * sizeof(double));
        memset(v->seen, 0, (size_t)v->infosets);
        memset(v->recall_bad, 0, (size_t)v->infosets);
    }
    v->root_value = walk(v, g, g->root, x, 1.0, 1.0, 1.0);
    for (int I = 0; I < g->n_infosets; ++I) {
        if (v->recall_bad[I]) ++v->recall_failures;
        if (v->mass[I] > 0 && !v->recall_bad[I]) {
            const int o = g->is_offset[I];
            for (int a = 0; a < g->is_actions[I]; ++a) v->q[o + a] /= v->mass[I];
        }
    }
    ++v->refreshes;
}

int expansion_values_available(const ExpansionValues *v, int I, int o, int actions) {
    if (I < 0 || I >= v->infosets || o < 0 || actions < 1 || o + actions > v->slots)
        return 0;
    if (!v->seen[I] || v->recall_bad[I] || !(v->mass[I] > 0) || !isfinite(v->mass[I]))
        return 0;
    for (int a = 0; a < actions; ++a) if (!isfinite(v->q[o + a])) return 0;
    return 1;
}

void expansion_values_free(ExpansionValues *v) {
    free(v->q); free(v->mass); free(v->own); free(v->seen); free(v->recall_bad);
    memset(v, 0, sizeof(*v));
}

void expansion_moment_init(ExpansionMoment *m) {
    m->mean = 0; m->m2 = 2; m->count = 2; /* prior observations -1, +1 */
}

void expansion_moment_add(ExpansionMoment *m, double value) {
    ++m->count;
    const double delta = value - m->mean;
    m->mean += delta / (double)m->count;
    m->m2 += delta * (value - m->mean);
}

double expansion_score(double q, const ExpansionMoment *m, uint64_t total, uint64_t chosen) {
    /* Appendix C.4 explicitly says variance. Population variance includes
     * the two prior observations. C=1; no coefficient tuning. */
    const double variance = fmax(0.0, m->m2 / (double)m->count);
    return q + variance * sqrt((double)total) / (1.0 + (double)chosen);
}
