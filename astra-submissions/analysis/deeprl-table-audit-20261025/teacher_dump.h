#ifndef ASTRA_TEACHER_DUMP_H
#define ASTRA_TEACHER_DUMP_H
#include "gtcfr.h"
#include "teacher_targets.h"

/* Offline instrumentation only, after the solver has finished choosing.
 * Returns 0 if no MIST_TEACHER_OUT is requested, 1 if written, -1 on error. */
int astra_teacher_dump(const Game *g, const double *x, int root_I,
                       const MoveList *moves, const SearchResult *result,
                       const Belief *belief, const int *indices,
                       const double *shares, int sampled,
                       const GtcfrParams *params);
#endif
