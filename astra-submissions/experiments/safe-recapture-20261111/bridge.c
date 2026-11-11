/* main_probe.c is generated from the exact v38 source and adds one helper
 * copy. The deployed caller, weights and control/observer binaries stay intact. */
#define main unused_original_protocol_main
#include "main_probe.c"
#undef main

void astra_initialize(void) {
    fow_init();
    zobrist_init();
}

static int decode_legal(const Position *p, const char *text, Move *out) {
    MoveList moves;
    generate_moves(p, &moves);
    for (int i = 0; i < moves.count; ++i) {
        char uci[6];
        move_to_uci(moves.moves[i], uci);
        if (strcmp(text, uci) == 0) { *out = moves.moves[i]; return 1; }
    }
    return 0;
}

/* bit0: original queen risk; bit1: safe-recapture-only risk; bit2: own king loss. */
int astra_flags(const char *board, int side, uint64_t castle, int ep,
                int halfmove, const char *text, int threshold) {
    Position p;
    if (pos_from_board_string(&p, board, side, castle, ep) < 0) return -1;
    p.halfmove = halfmove;
    Move move;
    if (!decode_legal(&p, text, &move)) return -2;
    Belief belief = {0};
    belief.items = &p; belief.count = 1; belief.us = side;
    double old, old_sharp, amended, amended_sharp;
    queen_risks(&belief, move, 1, 2.0, threshold, &old, &old_sharp);
    astra_queen_risks(&belief, move, 1, 2.0, threshold, &amended, &amended_sharp);
    if (old != old_sharp || amended != amended_sharp) return -3;
    Undo undo;
    make_move(&p, move, &undo);
    return (old > .5) | ((amended > .5) << 1) | (mover_left_king_capturable(&p) << 2);
}

/* Target-specific versus full FOW recapture enumeration on a capture child. */
int astra_recapture_flags(const char *board, int side, uint64_t castle,
                          int ep, int halfmove, int target) {
    Position p;
    if (target < 0 || target >= 64 || pos_from_board_string(&p, board, side, castle, ep) < 0) return -1;
    p.halfmove = halfmove;
    return astra_safe_recapture(&p, target) | (astra_exhaustive_recapture(&p, target) << 1);
}
