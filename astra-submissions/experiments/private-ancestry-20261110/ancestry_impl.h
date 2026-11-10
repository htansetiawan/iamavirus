/* Included at the end of our isolated belief.c. No replay or truth reader. */
static void astra_pool_free(AstraPool *pool) {
    free(pool->items); free(pool->hist); free(pool->logw);
    memset(pool, 0, sizeof(*pool));
}

void astra_ancestry_disable(Belief *b) {
    if (!b->ancestry) return;
    astra_pool_free(&b->ancestry->pool);
    free(b->ancestry->origin);
    free(b->ancestry);
    b->ancestry = NULL;
}

int astra_ancestry_enable(Belief *b) {
    /* Enable only at initialization, before either side has moved. */
    if (b->ancestry || b->count != 1 || b->last_own) return 0;
    Position start; pos_start(&start);
    if (position_key(&start) != position_key(&b->items[0]) ||
        b->items[0].halfmove != 0) return 0;
    AstraAncestry *a = calloc(1, sizeof(*a));
    if (!a) return 0;
    char view[65]; observation(&start, b->us, view);
    a->own_now = history_mix(0, view_hash(view));
    a->natural = 1;
    b->ancestry = a;
    return 1;
}

size_t astra_ancestry_payload(const Belief *b) {
    const AstraAncestry *a = b->ancestry;
    if (!a) return 0;
    return sizeof(*a) + a->pool.capacity *
        (sizeof(Position) + sizeof(uint64_t) + sizeof(float)) +
        a->origin_capacity * sizeof(AstraOrigin);
}

int astra_ancestry_context(const Belief *b, size_t i, AstraContext *out) {
    const AstraAncestry *a = b->ancestry;
    if (!a || !a->natural || !a->origin || i >= b->count) return 0;
    const AstraOrigin o = a->origin[i];
    if (o.valid != 2 || o.parent >= a->pool.count) return 0;
    memset(out, 0, sizeof(*out));
    out->ancestor = a->pool.items[o.parent];
    out->current = b->items[i];
    out->own = a->own; out->opponent = o.opponent; out->parent = o.parent;
    out->opponent_before = a->pool.hist ? a->pool.hist[o.parent] : 0;
    out->opponent_now = b->hist ? b->hist[i] : 0;
    out->own_before = a->own_before; out->own_now = a->own_now;
    out->ancestor_logw = a->pool.logw ? a->pool.logw[o.parent] : 0;
    out->current_logw = b->logw ? b->logw[i] : 0;
    return 1;
}

static int astra_continued(const Position *p) {
    return king_square(p, WHITE) >= 0 && king_square(p, BLACK) >= 0 &&
           !mover_left_king_capturable(p);
}

static int astra_same_view(const Position *a, const Position *b, int side) {
    char x[65], y[65]; observation(a, side, x); observation(b, side, y);
    return !memcmp(x, y, 64);
}

size_t astra_ancestry_alternatives(const Belief *b, size_t i,
        AstraAlternativeFn callback, void *arg, size_t limit) {
    AstraContext c;
    if (!astra_ancestry_context(b, i, &c) || !limit) return 0;
    Position after = c.ancestor; Undo u; make_move(&after, c.own, &u);
    MoveList moves; generate_moves(&c.ancestor, &moves);
    size_t count = 0;
    const int us = b->us, them = us ^ 1;
    for (int j = 0; j < moves.count && count < limit; ++j) {
        const Move alternative = moves.moves[j];
        if (alternative == c.own) continue;
        Position q = c.ancestor; make_move(&q, alternative, &u);
        if (!astra_continued(&q) || !astra_same_view(&q, &after, them)) continue;
        MoveList replies; generate_moves(&q, &replies);
        int legal = 0;
        for (int r = 0; r < replies.count; ++r) legal |= replies.moves[r] == c.opponent;
        if (!legal) continue;
        char own_view[65]; observation(&q, us, own_view);
        uint64_t own_h = history_mix(history_mix(c.own_before, alternative), view_hash(own_view));
        make_move(&q, c.opponent, &u);
        if (!astra_continued(&q) || !astra_same_view(&q, &c.current, them)) continue;
        observation(&q, us, own_view);
        own_h = history_mix(own_h, view_hash(own_view));
        AstraAlternative result = {0};
        result.current = q; result.alternative_own = alternative;
        result.own_history = own_h; result.opponent_history = c.opponent_now;
        /* Deliberately no insertion into Belief and no probability assignment. */
        if (callback) callback(&result, arg);
        ++count;
    }
    return count;
}
