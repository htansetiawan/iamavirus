/* Isolated posterior experiment, not a protocol/search replacement.
 * Reuse pinned rules, view filters, RNG and cap-selection helpers. */
#include "../temporal-belief-20261101/native/belief.c"
#include <limits.h>

typedef struct { uint32_t recent; float logw; } MixContext;
typedef struct { Position position; uint32_t begin, end; float logw; } MixBoard;
typedef struct {
    MixBoard *boards;
    MixContext *contexts;
    size_t count, context_count, cap, peak_candidates;
    int us, temporal, overflowed;
    Move last_own;
    float temperature;
    uint64_t rng;
} Mixture;

static void *checked_alloc(size_t n, size_t width) {
    if (width && n > SIZE_MAX / width) abort();
    void *p = malloc((n ? n : 1) * width);
    if (!p) { fprintf(stderr, "context mixture allocation failed\n"); abort(); }
    return p;
}

static float add_mass(float a, float b) {
    if (a == -INFINITY) return b;
    if (b == -INFINITY) return a;
    return log_add(a, b);
}

static void mix_init(Mixture *b, int us, size_t cap, uint64_t seed, int temporal, float temperature) {
    memset(b, 0, sizeof(*b)); b->us = us; b->cap = cap; b->rng = seed;
    b->temporal = temporal; b->temperature = temperature;
    b->boards = checked_alloc(1, sizeof(MixBoard));
    b->contexts = checked_alloc(1, sizeof(MixContext));
    b->count = b->context_count = 1;
    pos_start(&b->boards[0].position);
    b->boards[0].begin = 0; b->boards[0].end = 1; b->boards[0].logw = 0;
    b->contexts[0] = (MixContext){0, 0};
}

static void mix_free(Mixture *b) { free(b->boards); free(b->contexts); memset(b, 0, sizeof(*b)); }

/* Sort (physical board key, context). Six stable 16-bit radix passes, O(N),
 * with a bounded 512 KiB counting table and one Candidate-sized scratch row.
 * No full Position is stored for a generated successor until after the cap. */
static void mix_sort(Candidate *rows, size_t n) {
    if (n < 2) return;
    Candidate *scratch = checked_alloc(n, sizeof(*scratch));
    size_t *counts = checked_alloc(65537, sizeof(*counts));
    Candidate *src = rows, *dst = scratch;
    for (int pass = 0; pass < 6; ++pass) {
        memset(counts, 0, 65537 * sizeof(*counts));
        for (size_t i = 0; i < n; ++i) {
            unsigned digit = pass < 2 ? (src[i].recent >> (16 * pass)) & 65535U
                                      : (src[i].key >> (16 * (pass - 2))) & 65535U;
            ++counts[digit + 1];
        }
        for (size_t j = 1; j < 65537; ++j) counts[j] += counts[j - 1];
        for (size_t i = 0; i < n; ++i) {
            unsigned digit = pass < 2 ? (src[i].recent >> (16 * pass)) & 65535U
                                      : (src[i].key >> (16 * (pass - 2))) & 65535U;
            dst[counts[digit]++] = src[i];
        }
        Candidate *tmp = src; src = dst; dst = tmp;
    }
    if (src != rows) memcpy(rows, src, n * sizeof(*rows));
    free(scratch); free(counts);
}

typedef struct { uint32_t begin, end, representative; float logw; } MixGroup;

static size_t mix_commit(Mixture *b, Candidate *rows, size_t n) {
    if (n > b->peak_candidates) b->peak_candidates = n;
    if (n > UINT32_MAX) abort();
    mix_sort(rows, n);
    size_t merged = 0;
    for (size_t i = 0; i < n;) {
        size_t j = i + 1; Candidate representative = rows[i]; float mass = rows[i].logw;
        while (j < n && rows[j].key == rows[i].key && rows[j].recent == rows[i].recent) {
            mass = add_mass(mass, rows[j].logw);
            if (rows[j].logw > representative.logw) representative = rows[j];
            ++j;
        }
        representative.logw = mass; rows[merged++] = representative; i = j;
    }
    MixGroup *groups = checked_alloc(merged, sizeof(*groups)); size_t ng = 0;
    for (size_t i = 0; i < merged;) {
        size_t j = i + 1, rep = i; float mass = rows[i].logw;
        while (j < merged && rows[j].key == rows[i].key) {
            mass = add_mass(mass, rows[j].logw);
            if (rows[j].logw > rows[rep].logw) rep = j;
            ++j;
        }
        groups[ng++] = (MixGroup){(uint32_t)i, (uint32_t)j, (uint32_t)rep, mass}; i = j;
    }
    uint32_t *chosen = checked_alloc(ng, sizeof(*chosen));
    size_t keep = ng;
    if (ng > b->cap) {
        b->overflowed = 1; keep = b->cap;
        Ranked *ranked = checked_alloc(ng, sizeof(*ranked));
        for (size_t i = 0; i < ng; ++i) ranked[i] = (Ranked){log(-log(unit_open(&b->rng))) - groups[i].logw, (uint32_t)i};
        select_smallest(ranked, ng, keep);
        for (size_t i = 0; i < keep; ++i) chosen[i] = ranked[i].index;
        qsort(chosen, keep, sizeof(*chosen), by_index_u32); free(ranked);
    } else for (size_t i = 0; i < keep; ++i) chosen[i] = (uint32_t)i;
    size_t ncontexts = 0; float top = -INFINITY;
    for (size_t i = 0; i < keep; ++i) {
        const MixGroup *g = &groups[chosen[i]]; ncontexts += g->end - g->begin;
        if (g->logw > top) top = g->logw;
    }
    if (ncontexts > UINT32_MAX) abort();
    MixBoard *boards = checked_alloc(keep, sizeof(*boards));
    MixContext *contexts = checked_alloc(ncontexts, sizeof(*contexts)); size_t at = 0;
    for (size_t i = 0; i < keep; ++i) {
        const MixGroup *g = &groups[chosen[i]]; const Candidate *c = &rows[g->representative];
        boards[i].position = b->boards[c->parent].position;
        Undo undo; make_move(&boards[i].position, c->move, &undo);
        boards[i].begin = (uint32_t)at; boards[i].logw = g->logw - top;
        for (size_t j = g->begin; j < g->end; ++j) contexts[at++] = (MixContext){rows[j].recent, rows[j].logw - top};
        boards[i].end = (uint32_t)at;
    }
    assert(at == ncontexts);
    free(b->boards); free(b->contexts); free(groups); free(chosen); free(rows);
    b->boards = boards; b->contexts = contexts; b->count = keep; b->context_count = ncontexts;
    return keep;
}

static void mix_push(Candidate **rows, size_t *n, size_t *capacity, Candidate item) {
    if (*n == *capacity) {
        size_t next = *capacity ? *capacity * 2 : 4096;
        if (next < *capacity || next > SIZE_MAX / sizeof(Candidate)) abort();
        Candidate *grown = realloc(*rows, next * sizeof(Candidate));
        if (!grown) abort();
        *rows = grown; *capacity = next;
    }
    (*rows)[(*n)++] = item;
}

static size_t mix_opponent(Mixture *b, const char view[65]) {
    ViewMasks masks; view_masks(view, b->us, &masks);
    Candidate *rows = NULL; size_t n = 0, capacity = 0;
    for (size_t i = 0; i < b->count; ++i) {
        const MixBoard *board = &b->boards[i]; const Position *p = &board->position;
        MoveList moves; generate_moves(p, &moves);
        uint64_t keys[256] = {0}; int valid = 0;
        for (int j = 0; j < moves.count; ++j) {
            Position q = *p; Undo u; make_move(&q, moves.moves[j], &u);
            if (may_match(&q, &masks, b->us) && !mover_left_king_capturable(&q) && view_equal(&q, &masks, b->us)) {
                keys[j] = position_key(&q); ++valid;
            }
        }
        if (!valid) continue;
        /* Reuse expensive board/attack features across all recent histories. */
        float base[256], logits[256], masses[256][2];
        recent_logits(0, p, &moves, b->last_own, b->temporal, base);
        for (int j = 0; j < moves.count; ++j) masses[j][0] = masses[j][1] = -INFINITY;
        for (size_t h = board->begin; h < board->end; ++h) {
            const MixContext *ctx = &b->contexts[h]; TemporalHistory history = {0};
            history.side[p->side] = recent_unpack(ctx->recent); float top = -INFINITY;
            for (int j = 0; j < moves.count; ++j) {
                logits[j] = base[j] + (b->temporal ? temporal_sparse_score(learned_temporal + MM_FEATURES, &history, p, moves.moves[j]) : 0);
                if (logits[j] > top) top = logits[j];
            }
            double z = 0;
            for (int j = 0; j < moves.count; ++j) z += exp((double)(logits[j] - top));
            const float logz = top + (float)log(z);
            for (int j = 0; j < moves.count; ++j) if (keys[j]) {
                uint32_t next = recent_advance(ctx->recent, p, moves.moves[j]);
                int continued = (next >> 24) & 1;
                /* Temper EACH history-conditional transition before summing.
                 * (sum_h w_h p_h)^temp would define a different posterior. */
                float mass = ctx->logw + b->temperature * (logits[j] - logz);
                masses[j][continued] = add_mass(masses[j][continued], mass);
            }
        }
        for (int j = 0; j < moves.count; ++j) if (keys[j]) for (int c = 0; c < 2; ++c) {
            if (masses[j][c] == -INFINITY) continue;
            uint32_t recent = recent_advance(0, p, moves.moves[j]) | ((uint32_t)c << 24);
            mix_push(&rows, &n, &capacity, (Candidate){keys[j], (uint32_t)i, moves.moves[j], masses[j][c], recent});
        }
    }
    return mix_commit(b, rows, n);
}

static size_t mix_own(Mixture *b, Move move, const char view[65]) {
    b->last_own = move; ViewMasks masks; view_masks(view, b->us, &masks);
    Candidate *rows = NULL; size_t n = 0, capacity = 0;
    for (size_t i = 0; i < b->count; ++i) {
        const MixBoard *board = &b->boards[i]; Position q = board->position;
        MoveList legal; generate_moves(&q, &legal); int found = 0;
        for (int j = 0; j < legal.count; ++j) if (legal.moves[j] == move) found = 1;
        if (!found) continue;
        Undo u; make_move(&q, move, &u);
        if (!may_match(&q, &masks, b->us) || mover_left_king_capturable(&q) || !view_equal(&q, &masks, b->us)) continue;
        const uint64_t key = position_key(&q);
        for (size_t h = board->begin; h < board->end; ++h) {
            const MixContext *ctx = &b->contexts[h];
            mix_push(&rows, &n, &capacity, (Candidate){key, (uint32_t)i, move, ctx->logw, ctx->recent});
        }
    }
    return mix_commit(b, rows, n);
}
