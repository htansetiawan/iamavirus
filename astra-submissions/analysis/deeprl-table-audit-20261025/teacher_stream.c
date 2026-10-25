#include "teacher_stream.h"
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int astra_stream_line(char *line, size_t capacity, char forced_move[8], const char **forced) {
    *forced = NULL;
    if (strncmp(line, "play ", 5) != 0) return 1;
    double clock; char extra;
    if (sscanf(line + 5, "%5s %lf %c", forced_move, &clock, &extra) != 2 ||
        !isfinite(clock) || clock <= 0) return 0;
    *forced = forced_move;
    snprintf(line, capacity, "%.17g", clock);
    return 1;
}

static int find_move(const MoveList *list, const char *uci, Move *move) {
    for (int i=0; i<list->count; ++i) {
        char candidate[6]; move_to_uci(list->moves[i], candidate);
        if (!strcmp(candidate, uci)) { *move=list->moves[i]; return 1; }
    }
    return 0;
}

int astra_stream_commit(FILE *in, const MoveList *allowed, const Belief *b, Move *move) {
    char line[128], uci[8], extra;
    if (!fgets(line, sizeof line, in) ||
        sscanf(line, "commit %5s %c", uci, &extra) != 1) return 0;
    if (find_move(allowed, uci, move)) return 1;
    /* Same historical-move fallback as the archive's MIST_FORCE_MOVES path.
       This is not permission for the deployed selector to choose this move. */
    if (b->count) {
        MoveList moves; generate_moves(&b->items[0], &moves);
        if (find_move(&moves, uci, move)) return 1;
    }
    return 0;
}

static uint64_t mix(uint64_t h, uint64_t x) {
    return (h ^ x) * UINT64_C(1099511628211);
}

uint64_t astra_stream_fingerprint(const Belief *b) {
    /* Diagnostic checksum of logical fields, never struct padding/pointers.
       Not a cryptographic equality proof; also compare sampled hypotheses,
       weights, root candidates and exclusions in the Python harness. */
    uint64_t h=UINT64_C(14695981039346656037);
    h=mix(h,b->count); h=mix(h,b->cap); h=mix(h,b->us);
    h=mix(h,b->last_own); h=mix(h,b->rng); h=mix(h,b->overflowed);
    h=mix(h,b->hist!=NULL); h=mix(h,b->logw!=NULL);
    for (size_t i=0; i<b->count; ++i) {
        const Position *p=&b->items[i];
        for (int c=0;c<2;++c) h=mix(h,p->by_color[c]);
        for (int t=0;t<6;++t) h=mix(h,p->by_type[t]);
        for (int s=0;s<64;++s) { h=mix(h,(uint8_t)p->piece[s]); h=mix(h,(uint8_t)p->color[s]); }
        h=mix(h,p->side); h=mix(h,p->castle_rooks);
        h=mix(h,(uint64_t)p->ep); h=mix(h,p->halfmove);
        if (b->hist) h=mix(h,b->hist[i]);
        if (b->logw) { uint32_t bits; memcpy(&bits,&b->logw[i],sizeof bits); h=mix(h,bits); }
    }
    return h;
}

void astra_stream_stamp(const Belief *b, int ply, const char *phase) {
    fprintf(stderr,"astra: stream %s ply=%d count=%zu hash=%016llx\n",phase,ply,b->count,
            (unsigned long long)astra_stream_fingerprint(b));
}
