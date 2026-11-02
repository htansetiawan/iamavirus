/* Offline exporter; baseline belief changes only through permitted inputs.
 * Includes the immutable, exact-output optimized v37 implementation. */
#include "belief.c"
#include <assert.h>

typedef struct {
    uint64_t key, castle;
    float x[26], base;
    uint32_t history_count;
    uint16_t move;
    int8_t ep, side;
    int32_t halfmove;
    char board[65];
} ExportRow;

static Belief state;
static ExportRow rows[256], position_row;

static void fields(ExportRow *row, const Position *p) {
    row->key = position_key(p); row->castle = p->castle_rooks;
    row->ep = (int8_t)p->ep; row->side = (int8_t)p->side;
    row->halfmove = p->halfmove;
    pos_to_board_string(p, row->board);
}

void pl_load(void) { fow_init(); zobrist_init(); read_settings(); }
void pl_start(int us) {
    if (state.items) belief_free(&state);
    belief_init_start(&state, us, 200000);
}
void pl_free(void) { if (state.items) belief_free(&state); }
size_t pl_count(void) { return state.count; }
int pl_capped(void) { return state.overflowed; }
size_t pl_own(Move move, const char *view) { return belief_after_own(&state, move, view); }
size_t pl_opponent(const char *view) { return belief_after_opponent(&state, view); }

const ExportRow *pl_position(size_t i) {
    assert(i < state.count);
    memset(&position_row, 0, sizeof position_row);
    fields(&position_row, &state.items[i]);
    position_row.base = state.logw[i];
    return &position_row;
}

const ExportRow *pl_parent(size_t i, const char *view, int *n,
                          float *parent_weight, unsigned *history_n) {
    assert(i < state.count && state.count <= 256);
    const Position *p = &state.items[i];
    assert(p->side == (state.us ^ 1));
    MoveList legal; generate_moves(p, &legal);
    float logits[256]; unsigned counts[256] = {0};
    move_logits(p, &legal, state.last_own, 1, logits);
    *history_n = history_counts(state.hist[i], &legal, counts);
    *parent_weight = state.logw[i]; *n = legal.count;
    memset(rows, 0, sizeof rows);
    for (int j = 0; j < legal.count; ++j) {
        ExportRow *row = &rows[j];
        float all[MM_FEATURES];
        move_features(p, legal.moves[j], state.last_own, 1, all);
        memcpy(row->x, all, sizeof row->x);
        row->base = logits[j]; row->history_count = counts[j]; row->move = legal.moves[j];
        Position next = *p; Undo undo; char observed[65];
        make_move(&next, legal.moves[j], &undo);
        observation(&next, state.us, observed);
        if (!mover_left_king_capturable(&next) && !strcmp(view, observed)) fields(row, &next);
    }
    return rows;
}
