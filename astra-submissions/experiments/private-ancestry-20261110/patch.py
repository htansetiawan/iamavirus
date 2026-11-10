"""Deterministic narrow changes to the immutable v38 belief, in a private copy."""
from pathlib import Path


def change(text, old, new, count=1):
    assert text.count(old) == count, (old[:90], text.count(old), count)
    return text.replace(old, new)


def apply(src):
    p = src / 'belief.h'
    h = p.read_text().replace('#include "fow.h"', '#include "fow.h"\n#include "ancestry_types.h"')
    h = change(h, '    int overflowed;\n', '    int overflowed;\n    AstraAncestry *ancestry;\n')
    h = change(h, 'void zobrist_init(void);', '''int astra_ancestry_enable(Belief *b);
void astra_ancestry_disable(Belief *b);
size_t astra_ancestry_payload(const Belief *b);
int astra_ancestry_context(const Belief *b, size_t i, AstraContext *out);
size_t astra_ancestry_alternatives(const Belief *b, size_t i,
        AstraAlternativeFn callback, void *arg, size_t limit);
void zobrist_init(void);''')
    p.write_text(h)
    p = src / 'belief.c'; s = p.read_text()
    s = change(s, '#define MAX_THREADS 8', '#define MAX_THREADS 8\nstatic void astra_pool_free(AstraPool *pool);')
    s = change(s, 'void belief_free(Belief *b) {', 'void belief_free(Belief *b) {\n    astra_ancestry_disable(b);')
    s = change(s, 'size_t count, capacity; } Vec;', 'size_t count, capacity; AstraOrigin *origin; int track; } Vec;')
    s = change(s, '        v->items = realloc(v->items, v->capacity * sizeof(Position));',
               '        if (v->track) v->origin = realloc(v->origin, v->capacity * sizeof(AstraOrigin));\n        v->items = realloc(v->items, v->capacity * sizeof(Position));')
    s = change(s, '    v->items[v->count] = *p;', '    if (v->track) v->origin[v->count] = (AstraOrigin){0};\n    v->items[v->count] = *p;')
    s = change(s, 'static size_t commit(Belief *b, Vec *next) {', '''static size_t commit(Belief *b, Vec *next) {
    if (b->ancestry) {
        free(b->ancestry->origin);
        b->ancestry->origin = next->origin;
        b->ancestry->origin_capacity = next->origin ? next->capacity : 0;
    }''')
    s = change(s, '        w->next->logw[k] = c->logw;', '''        w->next->logw[k] = c->logw;
        if (w->next->origin && b->ancestry->origin) {
            AstraOrigin o = b->ancestry->origin[c->parent];
            if (o.valid == 1 && o.parent < b->ancestry->pool.count) {
                o.opponent = c->move; o.valid = 2;
                w->next->origin[k] = o;
            }
        }''')
    s = change(s, '    next.count = keep;\n', '''    next.count = keep;
    if (b->ancestry && b->ancestry->natural)
        next.origin = calloc(next.capacity, sizeof(AstraOrigin));
''')
    s = change(s, '    free(cand);\n    return commit(b, &next);', '''    free(cand);
    if (b->ancestry)
        b->ancestry->own_now = history_mix(b->ancestry->own_now, view_hash(view));
    return commit(b, &next);''')
    s = change(s, '        vec_push(&w->next, &p, h, b->logw ? b->logw[i] : 0.0f);   /* distinct positions stay distinct */', '''        vec_push(&w->next, &p, h, b->logw ? b->logw[i] : 0.0f);   /* distinct positions stay distinct */
        if (w->next.track) w->next.origin[w->next.count - 1] =
            (AstraOrigin){ .parent = (uint32_t)i, .valid = 1 };''')
    s = change(s, 'w[t].view = view; w[t].m = m;', 'w[t].view = view; w[t].m = m;\n        w[t].next.track = b->ancestry && b->ancestry->natural;')
    s = change(s, '            next.items = realloc(next.items, n * sizeof(Position));',
               '            if (next.track) next.origin = realloc(next.origin, n * sizeof(AstraOrigin));\n            next.items = realloc(next.items, n * sizeof(Position));')
    s = change(s, '                memcpy(next.items + next.count, v->items, v->count * sizeof(Position));',
               '                if (next.track) memcpy(next.origin + next.count, v->origin, v->count * sizeof(AstraOrigin));\n                memcpy(next.items + next.count, v->items, v->count * sizeof(Position));')
    s = change(s, '            free(v->items); free(v->hist); free(v->logw);',
               '            free(v->items); free(v->hist); free(v->logw); free(v->origin);')
    s = change(s, '    return commit(b, &next);\n}\n\n\nsize_t belief_shrink', '''    if (b->ancestry) {
        AstraAncestry *a = b->ancestry;
        astra_pool_free(&a->pool);
        a->own_before = a->own_now; a->own = m;
        a->own_now = history_mix(history_mix(a->own_now, m), view_hash(view));
        if (a->natural) {
            a->pool = (AstraPool){b->items, b->hist, b->logw, b->count, b->capacity};
            b->items = NULL; b->hist = NULL; b->logw = NULL;
        }
    }
    return commit(b, &next);
}


size_t belief_shrink''')
    s = change(s, '        b->items[k] = b->items[keep[k]];',
               '        if (b->ancestry && b->ancestry->origin)\n            b->ancestry->origin[k] = b->ancestry->origin[keep[k]];\n        b->items[k] = b->items[keep[k]];')
    s = change(s, 'size_t belief_resample(Belief *b, const char view[65], const int their[6], bb_t our_castle, size_t target, size_t tries) {', '''size_t belief_resample(Belief *b, const char view[65], const int their[6], bb_t our_castle, size_t target, size_t tries) {
    if (b->ancestry) {
        b->ancestry->natural = 0;
        astra_pool_free(&b->ancestry->pool);
        free(b->ancestry->origin); b->ancestry->origin = NULL;
        b->ancestry->origin_capacity = 0;
    }''')
    s += '\n#include "ancestry_impl.h"\n'
    p.write_text(s)
