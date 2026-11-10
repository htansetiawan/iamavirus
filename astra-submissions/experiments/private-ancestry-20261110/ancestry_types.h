/* One representative natural history, not all histories of a merged board. */
#ifndef ASTRA_ANCESTRY_TYPES_H
#define ASTRA_ANCESTRY_TYPES_H
#include "fow.h"
#include <stddef.h>

typedef struct {
    uint32_t parent;
    Move opponent;
    uint16_t valid;                 /* 1: pending reply; 2: complete edge */
} AstraOrigin;
_Static_assert(sizeof(AstraOrigin) == 8, "compact ancestry edge");

typedef struct {
    Position *items;
    uint64_t *hist;
    float *logw;
    size_t count, capacity;
} AstraPool;

typedef struct {
    AstraPool pool;
    AstraOrigin *origin;
    size_t origin_capacity;
    Move own;
    uint64_t own_before, own_now;
    int natural;                    /* permanently false after recovery */
} AstraAncestry;

typedef struct {
    Position ancestor, current;
    Move own, opponent;
    uint64_t opponent_before, opponent_now, own_before, own_now;
    float ancestor_logw, current_logw; /* native weights, NOT alternative reaches */
    uint32_t parent;
} AstraContext;

typedef struct {
    Position current;
    Move alternative_own;
    uint64_t own_history, opponent_history;
    int reach_known;                /* always zero: no invented probability */
} AstraAlternative;

typedef void (*AstraAlternativeFn)(const AstraAlternative *, void *);
#endif
