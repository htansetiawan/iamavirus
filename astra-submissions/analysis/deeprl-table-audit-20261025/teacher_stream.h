#ifndef ASTRA_TEACHER_STREAM_H
#define ASTRA_TEACHER_STREAM_H
#include "belief.h"
#include <stdio.h>

/* Offline replay collector only. Never linked into an arena release. */
int astra_stream_line(char *line, size_t capacity, char forced_move[8], const char **forced);
int astra_stream_commit(FILE *in, const MoveList *allowed, const Belief *b, Move *move);
uint64_t astra_stream_fingerprint(const Belief *b);
void astra_stream_stamp(const Belief *b, int ply, const char *phase);
#endif
