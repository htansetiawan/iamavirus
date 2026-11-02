/* Astra 234: read-only conditional values and visit statistics for GT-CFR.
 * Values describe exactly the current finite tree, not the unknown real game. */
#ifndef ASTRA_EXPANSION_VALUES_H
#define ASTRA_EXPANSION_VALUES_H
#include "cfr.h"
#include <stdint.h>

typedef struct {
    double *q, *mass, *own;
    unsigned char *seen, *recall_bad;
    int slots, infosets, cap_slots, cap_infosets;
    uint64_t nodes, refreshes, recall_failures;
    double root_value;
} ExpansionValues;

typedef struct { double mean, m2; uint64_t count; } ExpansionMoment;

void expansion_values_refresh(ExpansionValues *v, const Game *g, const double *x);
int expansion_values_available(const ExpansionValues *v, int infoset, int offset, int actions);
void expansion_values_free(ExpansionValues *v);
void expansion_moment_init(ExpansionMoment *m);
void expansion_moment_add(ExpansionMoment *m, double value);
double expansion_score(double q, const ExpansionMoment *m, uint64_t total, uint64_t chosen);
#endif
