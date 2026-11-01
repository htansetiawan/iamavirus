#!/usr/bin/env python3
"""Reproduce the isolated patch from immutable base files; never touch Fable's checkout."""
from pathlib import Path
root=Path(__file__).resolve().parent
h=(root/'base/belief.h').read_text()
h=h.replace('    float *logw;','    uint32_t *recent;  /* packed sufficient temporal context, per hypothetical path */\n    float *logw;',1)
(root/'native/belief.h').write_text(h)
s=(root/'base/belief.c').read_text()
def replace(old,new,n=1):
    global s
    assert s.count(old)==n,(old[:80],s.count(old),n)
    s=s.replace(old,new)
replace('#include "movemodel.h"','#include "movemodel.h"\n#include "../packed.h"')
replace('#define MAX_THREADS 8','#define MAX_THREADS 8\n\nstatic int astra_model = -1, astra_context_merge = 0;')
replace('uint64_t view_hash(const char view[65]) {','''/* Do not use history_mix(value|1): that would erase one context bit. */
static uint64_t context_key(const Position *p,uint32_t recent) {
    uint64_t k=position_key(p);
    if(!astra_context_merge)return k;
    k^=(uint64_t)recent*0x9e3779b97f4a7c15ULL;
    k=(k^(k>>30))*0xbf58476d1ce4e5b9ULL;
    k=(k^(k>>27))*0x94d049bb133111ebULL;
    return (k^(k>>31))|1;
}

uint64_t view_hash(const char view[65]) {''')
replace('    b->logw = malloc(b->capacity * sizeof(float));','    b->logw = malloc(b->capacity * sizeof(float));\n    b->recent = calloc(b->capacity,sizeof(uint32_t));')
replace('    free(b->logw);\n    free(b->set);','    free(b->logw);\n    free(b->recent);\n    free(b->set);')
replace('typedef struct { Position *items; uint64_t *hist; float *logw; size_t count, capacity; } Vec;',
        'typedef struct { Position *items; uint64_t *hist; float *logw; uint32_t *recent; size_t count, capacity; } Vec;')
replace('static void vec_push(Vec *v, const Position *p, uint64_t hist, float logw) {',
        'static void vec_push(Vec *v, const Position *p, uint64_t hist, float logw, uint32_t recent) {')
replace('        v->logw = realloc(v->logw, v->capacity * sizeof(float));',
        '        v->logw = realloc(v->logw, v->capacity * sizeof(float));\n        v->recent = realloc(v->recent,v->capacity*sizeof(uint32_t));')
replace('v->logw[v->count] = logw; ++v->count;', 'v->logw[v->count] = logw; v->recent[v->count] = recent; ++v->count;')
replace('    free(b->items); free(b->hist); free(b->logw);','    free(b->items); free(b->hist); free(b->logw); free(b->recent);')
replace('    b->logw = next->logw;','    b->logw = next->logw;\n    b->recent = next->recent;')
replace('    const char *e;\n    if ((e = getenv("MIST_MODEL")) && e[0] == \'0\') model_on = 0;',
'''    const char *e;
    if ((e = getenv("ASTRA_TEMPORAL_MODEL"))) astra_model=atoi(e);
    if ((e = getenv("ASTRA_CONTEXT_MERGE"))) astra_context_merge=atoi(e)!=0;
    if (astra_model < -1 || astra_model > 1) { fprintf(stderr,"bad ASTRA_TEMPORAL_MODEL\\n"); abort(); }
    if ((e = getenv("MIST_MODEL")) && e[0] == '0') model_on = 0;''')
replace('typedef struct { uint64_t key; uint32_t parent; Move move; float logw; } Candidate;',
'''typedef struct { uint64_t key; uint32_t parent; Move move; float logw; uint32_t recent; } Candidate;
_Static_assert(sizeof(Candidate)==24,"packed context must use original Candidate tail padding");''')
replace('                    move_logits(&b->items[i], &l, b->last_own, w->full, logit);',
'''                    if(astra_model>=0)
                        recent_logits(b->recent?b->recent[i]:0,&b->items[i],&l,b->last_own,astra_model,logit);
                    else move_logits(&b->items[i], &l, b->last_own, w->full, logit);''')
replace('                c->key = position_key(&p);',
'''                c->recent=recent_advance(b->recent?b->recent[i]:0,&b->items[i],l.moves[j]);
                c->key = context_key(&p,c->recent);''')
replace('        w->next->logw[k] = c->logw;','        w->next->logw[k] = c->logw;\n        w->next->recent[k] = c->recent;')
replace('    next.logw = malloc(next.capacity * sizeof(float));','    next.logw = malloc(next.capacity * sizeof(float));\n    next.recent = malloc(next.capacity * sizeof(uint32_t));')
replace('vec_push(&w->next, &p, h, b->logw ? b->logw[i] : 0.0f);','vec_push(&w->next, &p, h, b->logw ? b->logw[i] : 0.0f,b->recent?b->recent[i]:0);')
replace('            next.logw = realloc(next.logw, n * sizeof(float));','            next.logw = realloc(next.logw, n * sizeof(float));\n            next.recent = realloc(next.recent,n*sizeof(uint32_t));')
replace('                memcpy(next.logw + next.count, v->logw, v->count * sizeof(float));',
'''                memcpy(next.logw + next.count, v->logw, v->count * sizeof(float));
                memcpy(next.recent + next.count,v->recent,v->count*sizeof(uint32_t));''')
replace('            free(v->items); free(v->hist); free(v->logw);','            free(v->items); free(v->hist); free(v->logw); free(v->recent);')
replace('        if (b->logw) b->logw[k] = b->logw[keep[k]];',
        '        if (b->logw) b->logw[k] = b->logw[keep[k]];\n        if (b->recent) b->recent[k] = b->recent[keep[k]];')
replace('        if (b->logw) b->logw[k] = b->logw[i];',
        '        if (b->logw) b->logw[k] = b->logw[i];\n        if (b->recent) b->recent[k] = b->recent[i];')
replace('            if (b->logw) b->logw = realloc(b->logw, sizeof(float));',
        '            if (b->logw) b->logw = realloc(b->logw, sizeof(float));\n            if (b->recent) b->recent = realloc(b->recent,sizeof(uint32_t));')
replace('        if (b->hist) b->hist[0] = 0;','        if (b->hist) b->hist[0] = 0;\n        if (b->recent) b->recent[0] = 0;')
replace('            b->logw = realloc(b->logw, cap * sizeof(float));',
        '            b->logw = realloc(b->logw, cap * sizeof(float));\n            if (b->recent) b->recent = realloc(b->recent,cap*sizeof(uint32_t));')
replace('        if (b->hist) b->hist[b->count] = 0;','        if (b->hist) b->hist[b->count] = 0;\n        if (b->recent) b->recent[b->count] = 0;')
replace('vec_push(&next, &p, history_mix(0x7265, view_hash(theirs)), 0.0f);','vec_push(&next, &p, history_mix(0x7265, view_hash(theirs)), 0.0f,0);')
replace('if (next.count == 0) { free(next.items); free(next.hist); free(next.logw); return b->count; }',
        'if (next.count == 0) { free(next.items); free(next.hist); free(next.logw); free(next.recent); return b->count; }')
(root/'native/belief.c').write_text(s)
print('Patched isolated belief source; Candidate remains24bytes, context adds4bytes per retained world.')
