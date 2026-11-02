#ifndef ASTRA_BELIEF_SNAPSHOT_H
#define ASTRA_BELIEF_SNAPSHOT_H
#include "belief.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Canonical text, not a dump of ABI-dependent padding or pointers. */
static void snapshot_save(const Belief *b, const char *path) {
    FILE *f = fopen(path, "wx"); assert(f);
    assert(fprintf(f, "ASTRA_BELIEF1 %zu %zu %d %llu %u %d\n", b->count,
        b->cap, b->us, (unsigned long long)b->rng, (unsigned)b->last_own,
        b->overflowed) > 0);
    for (size_t i = 0; i < b->count; ++i) {
        char board[65]; pos_to_board_string(&b->items[i], board);
        assert(fprintf(f, "%s %d %llx %d %d %a %llx\n", board,
            b->items[i].side, (unsigned long long)b->items[i].castle_rooks,
            b->items[i].ep, b->items[i].halfmove,
            (double)(b->logw ? b->logw[i] : 0),
            (unsigned long long)(b->hist ? b->hist[i] : 0)) > 0);
    }
    assert(fclose(f) == 0);
}

static void snapshot_load(Belief *b, const char *path) {
    FILE *f = fopen(path, "r"); assert(f);
    memset(b, 0, sizeof *b);
    char magic[32]; unsigned long long rng; unsigned last;
    assert(fscanf(f, "%31s %zu %zu %d %llu %u %d", magic, &b->count,
        &b->cap, &b->us, &rng, &last, &b->overflowed) == 7);
    assert(strcmp(magic, "ASTRA_BELIEF1") == 0 && b->count <= 200000);
    assert(b->us == WHITE || b->us == BLACK);
    b->rng = rng; b->last_own = (Move)last; b->capacity = b->count;
    b->items = malloc(b->count * sizeof *b->items);
    b->hist = malloc(b->count * sizeof *b->hist);
    b->logw = malloc(b->count * sizeof *b->logw);
    assert(b->items && b->hist && b->logw);
    for (size_t i = 0; i < b->count; ++i) {
        char board[65]; int side, ep, halfmove;
        unsigned long long castle, hist; float logw;
        assert(fscanf(f, "%64s %d %llx %d %d %a %llx", board, &side,
            &castle, &ep, &halfmove, &logw, &hist) == 7);
        assert(pos_from_board_string(&b->items[i], board, side, castle, ep) == 0);
        b->items[i].halfmove = halfmove;
        b->hist[i] = hist; b->logw[i] = logw;
    }
    char extra[2]; assert(fscanf(f, "%1s", extra) == EOF);
    assert(fclose(f) == 0);
}

static void snapshot_at(const Belief *b, int ply, const char *phase) {
    const char *directory = getenv("ASTRA_SNAPSHOT_DIR");
    if (!directory || ply != 28) return;
    char path[4096]; int n = snprintf(path, sizeof path, "%s/%s.txt", directory, phase);
    assert(n > 0 && (size_t)n < sizeof path);
    snapshot_save(b, path);
}
#endif
