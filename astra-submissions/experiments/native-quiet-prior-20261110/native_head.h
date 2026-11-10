/* Isolated fixed full-head adapter. Public features/rules are unchanged. */
#ifndef ASTRA_NATIVE_QUIET_HEAD_H
#define ASTRA_NATIVE_QUIET_HEAD_H
#include "fow.h"
void astra_full_logp(const Position *p, const MoveList *moves, Move previous,
                     int learned, float *out);
#endif
