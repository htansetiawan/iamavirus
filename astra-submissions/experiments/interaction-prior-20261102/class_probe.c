/* Post-fit diagnostic only. No training or engine-policy change. */
#include "bridge.c"

int observation_class(Move actual, uint8_t compatible[256], char observed[65]) {
    MoveList list; generate_moves(&current, &list);
    Position target = current; Undo u;
    make_move(&target, actual, &u);
    observation(&target, current.side ^ 1, observed);
    for (int i = 0; i < list.count; ++i) {
        Position next = current; char view[65];
        make_move(&next, list.moves[i], &u);
        observation(&next, current.side ^ 1, view);
        compatible[i] = king_square(&next, current.side ^ 1) >= 0
            && !mover_left_king_capturable(&next) && !strcmp(view, observed);
    }
    return list.count;
}
