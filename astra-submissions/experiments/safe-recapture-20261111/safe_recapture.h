/* Immediate recapture feasibility, not a full exchange evaluator.
 * Caller p is the position after the opponent captured on target.
 * An attack is only a necessary condition: moving a pinned defender or the
 * king can lose immediately. Enumerate only pieces attacking this target.
 */
static int astra_safe_recapture(const Position *p, int target) {
    const bb_t destination = (bb_t)1 << target;
    bb_t pieces = p->by_color[p->side];
    while (pieces) {
        const int from = __builtin_ctzll(pieces);
        pieces &= pieces - 1;
        if (!(attacks_from(p, from) & destination)) continue;
        int promotion = NO_PIECE;
        if (p->piece[from] == PAWN &&
            target / 8 == (p->side == WHITE ? 7 : 0)) promotion = QUEEN;
        Position after = *p;
        Undo undo;
        make_move(&after, MAKE_MOVE(from, target, promotion), &undo);
        if (undo.captured_type == KING || !mover_left_king_capturable(&after)) return 1;
    }
    return 0;
}

/* Independent native enumeration used by the probe, not proposed for runtime. */
static int astra_exhaustive_recapture(const Position *p, int target) {
    MoveList moves;
    generate_moves(p, &moves);
    for (int i = 0; i < moves.count; ++i) {
        if (MOVE_TO(moves.moves[i]) != target) continue;
        Position after = *p;
        Undo undo;
        make_move(&after, moves.moves[i], &undo);
        if (undo.captured_type == KING || !mover_left_king_capturable(&after)) return 1;
    }
    return 0;
}
