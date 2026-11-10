#ifndef ASTRA_REFERENCE_OBSERVE_H
#define ASTRA_REFERENCE_OBSERVE_H
#include "belief.h"
int astra_reference_warm(int decision);
void astra_reference_legal(const MoveList *legal);
void astra_reference_capture(const Belief *b,const MoveList *moves,const double *x,int best);
void astra_reference_dump(const Belief *b,int decision);
#endif
