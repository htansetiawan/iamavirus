#ifndef ASTRA_ROOT_STRATA_H
#define ASTRA_ROOT_STRATA_H

#include "belief.h"

#define ASTRA_MAX_DRAWS 256
#define ASTRA_SIGNATURE_WORDS 4

typedef struct {
    uint64_t loss[ASTRA_SIGNATURE_WORDS], win[ASTRA_SIGNATURE_WORDS];
} TacticalSignature;

typedef struct {
    TacticalSignature signature;
    double mass;
    size_t count, offset;
} TacticalGroup;

typedef struct {
    const Belief *belief;
    MoveList moves;
    int eligible, groups, budget;
    const char *reason;
    double seconds, total;
    double loss[256], win[256], fitted_loss[256];
    TacticalGroup group[ASTRA_MAX_DRAWS];
    int *group_of, *members;
    double *weights, *cumulative;
} RootCensus;

/* Prototype: queenless own side, identical views and complete legal move sets.
 * Any unsupported input retains the original sampler and original pruning.
 * No belief items, weights or opponent histories are modified or merged. */
int root_census_build(RootCensus *, const Belief *, const MoveList *, int budget);
void root_census_free(RootCensus *);
int root_strata_sample(const RootCensus *, int draws, uint64_t *, int *, double *);
int root_interval_avoid(const RootCensus *, double kappa, Move *avoid);

/* The only GT-CFR patch calls this instead of belief_sample. Serial diagnostic
 * only: the context is deliberately process-local, not a shared thread API. */
void root_strata_activate(const RootCensus *, int enabled);
int astra_root_sample(const Belief *, int, uint64_t *, int *, double *);

#endif
