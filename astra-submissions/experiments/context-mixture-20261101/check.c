/* Independent full-state/context enumeration: no radix grouping, marginal
 * logits reuse or context-bucket aggregation from the implementation. */
#include "api.c"
#include <assert.h>

typedef struct { Position p; uint32_t recent; double mass; } Atom;
typedef struct { Atom *rows; size_t n, capacity; } Oracle;

static void oracle_add(Oracle *o, const Position *p, uint32_t recent, double mass) {
    /* Deliberately slow independent reference, only for tiny trees. */
    for (size_t i = 0; i < o->n; ++i) if (position_key(&o->rows[i].p) == position_key(p) && o->rows[i].recent == recent) {
        o->rows[i].mass += mass; return;
    }
    if (o->n == o->capacity) {
        o->capacity = o->capacity ? o->capacity * 2 : 64;
        o->rows = realloc(o->rows, o->capacity * sizeof(Atom)); assert(o->rows);
    }
    o->rows[o->n++] = (Atom){*p, recent, mass};
}

static void oracle_step(Oracle *o, int us, Move own, Move last_own, const char *view, int temporal, float temperature) {
    Oracle next = {0}; double total = 0;
    for (size_t i = 0; i < o->n; ++i) {
        const Atom *a = &o->rows[i]; MoveList l; generate_moves(&a->p, &l);
        float logits[256]; recent_logits(a->recent, &a->p, &l, last_own, temporal, logits);
        double top = -INFINITY;
        for (int j = 0; j < l.count; ++j) if (logits[j] > top) top = logits[j];
        double z = 0;
        for (int j = 0; j < l.count; ++j) z += exp(logits[j] - top);
        double logz = top + log(z);
        for (int j = 0; j < l.count; ++j) {
            if (own && own != l.moves[j]) continue;
            Position p = a->p; Undo u; make_move(&p, l.moves[j], &u); char actual[65]; observation(&p, us, actual);
            if (strcmp(view, actual) || mover_left_king_capturable(&p)) continue;
            double mass = a->mass * (own ? 1 : exp(temperature * (logits[j] - logz)));
            oracle_add(&next, &p, own ? a->recent : recent_advance(a->recent, &a->p, l.moves[j]), mass);
            total += mass;
        }
    }
    for (size_t i = 0; i < next.n; ++i) next.rows[i].mass /= total;
    free(o->rows); *o = next;
}

static void check_equal(const Mixture *b, const Oracle *o, int capped) {
    double expected_total = 0, got_total = 0; size_t matched = 0;
    for (size_t i = 0; i < b->count; ++i) {
        const MixBoard *w = &b->boards[i];
        for (size_t j = w->begin; j < w->end; ++j) got_total += exp(b->contexts[j].logw);
        for (size_t j = 0; j < o->n; ++j) if (position_key(&w->position) == position_key(&o->rows[j].p)) {
            expected_total += o->rows[j].mass; ++matched;
        }
    }
    assert(matched == b->context_count);
    if (!capped) assert(matched == o->n);
    for (size_t i = 0; i < b->count; ++i) {
        const MixBoard *w = &b->boards[i]; double board_sum = 0;
        for (size_t j = w->begin; j < w->end; ++j) {
            const MixContext *c = &b->contexts[j]; size_t found = 0;
            for (size_t k = 0; k < o->n; ++k) if (position_key(&w->position) == position_key(&o->rows[k].p) && c->recent == o->rows[k].recent) {
                assert(fabs(exp(c->logw) / got_total - o->rows[k].mass / expected_total) < 3e-6); ++found;
            }
            assert(found == 1); board_sum += exp(c->logw);
        }
        assert(fabs(log(board_sum) - w->logw) < 3e-6);
    }
}

static void exercise(int temporal, float temperature, size_t cap) {
    Mixture b; mix_init(&b, WHITE, 100000, 53, temporal, temperature);
    free(b.boards); free(b.contexts);
    b.count = 2; b.context_count = 6;
    b.boards = checked_alloc(2, sizeof(MixBoard)); b.contexts = checked_alloc(6, sizeof(MixContext));
    Position actual; pos_clear(&actual); actual.side = BLACK;
    pos_put(&actual, 0, WHITE, KING); pos_put(&actual, 7, WHITE, ROOK);
    pos_put(&actual, 60, BLACK, KING); pos_put(&actual, 42, BLACK, KNIGHT);
    RecentOwn r0 = {MAKE_MOVE(57, 42, NO_PIECE), 1, KNIGHT, 3, 1};
    RecentOwn r1 = {MAKE_MOVE(61, 60, NO_PIECE), 1, KING, 0, 0};
    Oracle oracle = {0};
    for (int i = 0; i < 2; ++i) {
        Position p = actual;
        if (i) { pos_remove(&p, 42); pos_put(&p, 45, BLACK, KNIGHT); }
        b.boards[i] = (MixBoard){p, (uint32_t)(3 * i), (uint32_t)(3 * i + 3), 0};
        double mass = 0;
        for (int j = 0; j < 3; ++j) {
            MixContext c = {j == 0 ? recent_pack(r0) : j == 1 ? recent_pack(r1) : 0, (float)(-.4 * i - .7 * j)};
            b.contexts[3 * i + j] = c; oracle_add(&oracle, &p, c.recent, exp(c.logw)); mass += exp(c.logw);
        }
        b.boards[i].logw = (float)log(mass);
    }
    const char *actions[] = {"c6b4", "h1h2", "e8e7", "h2h1"};
    Move last = 0;
    for (int k = 0; k < 4; ++k) {
        Move move = parse_uci(actions[k]); int own = actual.side == WHITE;
        Undo u; make_move(&actual, move, &u); assert(!mover_left_king_capturable(&actual));
        char view[65]; observation(&actual, WHITE, view);
        if (k == 3) b.cap = cap;
        oracle_step(&oracle, WHITE, own ? move : 0, last, view, temporal, temperature);
        if (own) { mix_own(&b, move, view); last = move; } else mix_opponent(&b, view);
        assert(b.count && b.count <= b.cap); check_equal(&b, &oracle, k == 3 && cap == 1);
        uint64_t before = tb_checksum(&b); double probe[10]; char truth[65]; pos_to_board_string(&actual, truth);
        tb_probe(&b, truth, actual.side, actual.castle_rooks, actual.ep, 0, probe);
        assert(tb_checksum(&b) == before);
    }
    if (cap == 1) assert(b.count == 1 && b.context_count > 1 && b.overflowed);
    /* Empty update and destruction must work without indexing unallocated rows. */
    char impossible[65]; memset(impossible, '-', 64); impossible[64] = 0;
    mix_opponent(&b, impossible); assert(!b.count && !b.context_count); mix_free(&b); free(oracle.rows);
}

static void static_parity(void) {
    Mixture mixture; mix_init(&mixture, WHITE, 100000, 19, 0, 2);
    Belief original; belief_init_start(&original, WHITE, 100000);
    astra_model = 0; astra_context_merge = 0; settings_read = 1; model_on = 1; model_temp = 2; threads_setting = 1;
    Position actual; pos_start(&actual);
    const char *moves[] = {"d2d4", "d7d5", "b1c3", "g8f6"};
    for (int k = 0; k < 4; ++k) {
        Move m = parse_uci(moves[k]); Undo u; make_move(&actual, m, &u); char view[65]; observation(&actual, WHITE, view);
        if (k % 2 == 0) { belief_after_own(&original, m, view); mix_own(&mixture, m, view); }
        else { belief_after_opponent(&original, view); mix_opponent(&mixture, view); }
        assert(mixture.count == original.count); double total1 = 0, total2 = 0;
        for (size_t i = 0; i < original.count; ++i) total1 += exp(original.logw[i]);
        for (size_t i = 0; i < mixture.count; ++i) total2 += exp(mixture.boards[i].logw);
        for (size_t i = 0; i < mixture.count; ++i) {
            int found = 0;
            for (size_t j = 0; j < original.count; ++j) if (position_key(&mixture.boards[i].position) == position_key(&original.items[j])) {
                assert(fabs(exp(mixture.boards[i].logw) / total2 - exp(original.logw[j]) / total1) < 3e-6); ++found;
            }
            assert(found == 1);
        }
    }
    mix_free(&mixture); belief_free(&original);
}

int main(void) {
    fow_init(); zobrist_init();
    for (int model = 0; model < 2; ++model) for (int temp = 1; temp < 3; ++temp) {
        exercise(model, (float)temp, 100000); exercise(model, (float)temp, 1);
    }
    static_parity();
    printf("PASS independent multistep joint-context posterior; static/temporal; temp1/2; board cap preserves all contexts; const probe; empty filter; original static parity. Board=%zu context=%zu candidate=%zu\n", sizeof(MixBoard), sizeof(MixContext), sizeof(Candidate));
    return 0;
}
