/* Isolated native component; no playing-filter hook and no learned scoring.
 * Reuses the pinned native prefilter and king-pruning rules. Unlike228's
 * oracle helper, the core receives the already permitted view, not the true
 * opponent action. Call once per hypothetical parent. Distinct output buffers.
 */
#include "belief.c"

static int valid_view(const char *view, int us) {
    if (!view || view[64] != '\0') return 0;
    int kings = 0;
    const char own_king = us == WHITE ? 'K' : 'k';
    for (int i = 0; i < 64; ++i) {
        if (!view[i] || !strchr("PNBRQKpnbrqk-?", view[i])) return 0;
        kings += view[i] == own_king;
    }
    return kings == 1;
}

/* Optional views is n x65 bytes. A null views pointer uses only the native
 * prefilter's surviving candidates for full observation construction. This
 * primitive checks native king-related continuation, not repetition/max-plies
 * or a complete hidden-history draw condition. Inputs and parent are const.
 */
int astra_observed_class(const Position *parent, int us, const char observed[65],
        Move moves[256], uint8_t capture[256], uint8_t consistent[256],
        uint8_t eligible[256], char *views) {
    if (!parent || parent->side < WHITE || parent->side > BLACK || us != (parent->side ^ 1)
        || !valid_view(observed, us) || !moves || !capture || !consistent || !eligible
        || king_square(parent, us) < 0 || king_square(parent, us ^ 1) < 0) return -1;
    MoveList list; generate_moves(parent, &list);
    ViewMasks vm; view_masks(observed, us, &vm);
    for (int i = 0; i < list.count; ++i) {
        Position next = *parent; Undo undo;
        make_move(&next, list.moves[i], &undo);
        const int cap = undo.captured_type != NO_PIECE;
        const int survives = king_square(&next, us) >= 0 && !mover_left_king_capturable(&next);
        const int prefiltered = survives && may_match(&next, &vm, us);
        char seen[65];
        if (views || prefiltered) observation(&next, us, seen);
        const int match = prefiltered && memcmp(seen, observed, 64) == 0;
        moves[i] = list.moves[i]; capture[i] = (uint8_t)cap;
        consistent[i] = (uint8_t)match; eligible[i] = (uint8_t)(match && !cap);
        if (views) memcpy(views + 65 * i, seen, 65);
    }
    return list.count;
}

/* Stateful test glue only. Real integration would pass b->items[i] directly
 * to the pure core, rather than reconstructing a true replay board. */
static Position test_parent;
static int test_ready;

int astra_test_set(const char *board, int side, uint64_t castle, int ep, int halfmove) {
    if (!board || side < WHITE || side > BLACK || ep < -1 || ep > 63 || halfmove < 0) return -1;
    fow_init(); Position next;
    if (pos_from_board_string(&next, board, side, castle, ep) != 0) return -1;
    next.halfmove = halfmove; test_parent = next; test_ready = 1;
    return 0;
}

int astra_test_state(char board[65], char white[65], char black[65],
                     uint64_t *castle, int *ep, int *halfmove) {
    if (!test_ready) return -1;
    pos_to_board_string(&test_parent, board);
    observation(&test_parent, WHITE, white); observation(&test_parent, BLACK, black);
    *castle = test_parent.castle_rooks; *ep = test_parent.ep; *halfmove = test_parent.halfmove;
    return test_parent.side;
}

int astra_test_step(Move move) {
    if (!test_ready) return -1;
    MoveList list; generate_moves(&test_parent, &list);
    for (int i = 0; i < list.count; ++i) if (list.moves[i] == move) {
        Undo undo; make_move(&test_parent, move, &undo);
        return mover_left_king_capturable(&test_parent);
    }
    return -1;
}

int astra_test_class(int us, const char observed[65], Move moves[256],
        uint8_t capture[256], uint8_t consistent[256], uint8_t eligible[256], char *views) {
    if (!test_ready) return -1;
    return astra_observed_class(&test_parent, us, observed, moves, capture, consistent, eligible, views);
}

#ifdef ASTRA_CLASS_UNIT
#include <assert.h>
int main(void) {
    char board[65], white[65], black[65], all_views[256 * 65];
    uint64_t castle; int ep, halfmove;
    Move moves[256]; uint8_t cap[256], match[256], eligible[256];
    assert(astra_test_set("RNBQKBNRPPPPPPPP--------------------------------pppppppprnbqkbnr",
                         WHITE, UINT64_C(0x8100000000000081), -1, 0) == 0);
    assert(astra_test_state(board, white, black, &castle, &ep, &halfmove) == WHITE);
    assert(astra_test_class(WHITE, white, moves, cap, match, eligible, all_views) == -1);
    for (int target = 0; target < 20; ++target) {
        MoveList list; generate_moves(&test_parent, &list); Position next = test_parent; Undo u;
        make_move(&next, list.moves[target], &u); char view[65]; observation(&next, BLACK, view);
        Position before = test_parent;
        int n = astra_test_class(BLACK, view, moves, cap, match, eligible, all_views);
        assert(n == 20 && match[target] && eligible[target] && !cap[target]);
        assert(memcmp(&before, &test_parent, sizeof(Position)) == 0);
        uint8_t cap2[256], match2[256], eligible2[256]; Move moves2[256];
        assert(astra_test_class(BLACK, view, moves2, cap2, match2, eligible2, NULL) == n);
        assert(memcmp(moves, moves2, (size_t)n * sizeof(Move)) == 0);
        assert(memcmp(cap, cap2, (size_t)n) == 0 && memcmp(match, match2, (size_t)n) == 0
               && memcmp(eligible, eligible2, (size_t)n) == 0);
    }
    puts("native observed-class unit passes20targets, both paths, parent nonmutation and invalid side");
    return 0;
}
#endif
