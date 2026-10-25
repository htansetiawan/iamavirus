/* Read-only targets from a fixed-policy, perfect-recall Game tree.
 * Reference implementation for export review, not wired into the arena bot. */
#ifndef ASTRA_TEACHER_TARGETS_H
#define ASTRA_TEACHER_TARGETS_H
#include "cfr.h"

typedef struct {
    double *cf_q;       /* n_slots: unnormalised counterfactual action values */
    double *cf_mass;    /* n_infosets: chance * other-player reach, summed over histories */
    double *own_reach;  /* n_infosets: own reach, counted ONCE per infoset */
    int *histories;     /* n_infosets: represented histories, not a sampling weight */
    int recall_ok;     /* equal own reach is necessary, not sufficient, for perfect recall */
    double root_value; /* player 0 utility */
} TeacherTargets;

/* x must be a normalized strategy over every infoset. g must be a tree.
 * No sampling correction is applied: values describe exactly the supplied tree,
 * chance distribution, strategy and frontier utilities. */
TeacherTargets teacher_targets(const Game *g, const double *x);
void teacher_targets_free(TeacherTargets *t);
#endif
