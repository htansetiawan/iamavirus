#ifndef ASTRA_TEACHER_PAIR_H
#define ASTRA_TEACHER_PAIR_H
#include "gtcfr.h"
/* Offline only: two searches of the SAME frozen belief. Returns the B move. */
int astra_teacher_pair(const Belief *b, const GtcfrParams *params, SearchResult *out);
#endif
