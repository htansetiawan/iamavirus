#include "teacher_targets.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

static double walk(const Game *g, int id, const double *x, double r0, double r1,
                   double rc, TeacherTargets *t) {
    const GameNode *n = &g->nodes[id];
    if (n->type == NODE_TERMINAL) return n->value;
    if (n->type == NODE_CHANCE) {
        double v = 0;
        for (int a = 0; a < n->count; ++a) {
            double p = g->prob[n->first + a];
            v += p * walk(g, g->child[n->first + a], x, r0, r1, rc*p, t);
        }
        return v;
    }
    int I = n->infoset, o = g->is_offset[I];
    double own = n->player == 0 ? r0 : r1;
    double mass = rc * (n->player == 0 ? r1 : r0);
    double sign = n->player == 0 ? 1 : -1;
    if (t->histories[I] && fabs(t->own_reach[I] - own) > 1e-12)
        t->recall_ok = 0;
    if (!t->histories[I]) t->own_reach[I] = own;
    t->histories[I]++;
    t->cf_mass[I] += mass;
    double v = 0;
    for (int a = 0; a < n->count; ++a) {
        double p = x[o+a];
        double q = walk(g, g->child[n->first+a], x,
                        n->player == 0 ? r0*p : r0,
                        n->player == 1 ? r1*p : r1, rc, t);
        t->cf_q[o+a] += mass * sign * q;
        v += p*q;
    }
    return v;
}

TeacherTargets teacher_targets(const Game *g, const double *x) {
    TeacherTargets t = {0};
    t.cf_q = calloc(g->n_slots, sizeof(double));
    t.cf_mass = calloc(g->n_infosets, sizeof(double));
    t.own_reach = calloc(g->n_infosets, sizeof(double));
    t.histories = calloc(g->n_infosets, sizeof(int));
    if (!t.cf_q || !t.cf_mass || !t.own_reach || !t.histories) abort();
    t.recall_ok = 1;
    t.root_value = walk(g, g->root, x, 1, 1, 1, &t);
    return t;
}

void teacher_targets_free(TeacherTargets *t) {
    free(t->cf_q); free(t->cf_mass); free(t->own_reach); free(t->histories);
    memset(t, 0, sizeof(*t));
}
