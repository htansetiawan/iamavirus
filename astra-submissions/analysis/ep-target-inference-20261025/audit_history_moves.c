#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/belief.h"

static int has(const MoveList *l, Move m) {
    for (int i = 0; i < l->count; ++i) if (l->moves[i] == m) return 1;
    return 0;
}

int main(void) {
    fow_init();
    char line[768], side_char, board[65], view[65], previous[65];
    unsigned long long castle;
    int ep;
    while (fgets(line, sizeof line, stdin)) {
        if (sscanf(line, " %c %llx %d %64s %64s %64s", &side_char, &castle, &ep,
                   board, view, previous) != 6 || strlen(board) != 64 ||
            strlen(view) != 64 || strlen(previous) != 64) return 2;
        const int side = side_char == 'b' ? BLACK : WHITE;
        Position truth;
        if (pos_from_board_string(&truth, board, side, (bb_t)castle, ep) != 0) return 3;
        MoveList legal, candidates;
        generate_moves(&truth, &legal);
        view_moves_with_history(view, previous[0] == '!' ? NULL : previous,
                                side, (bb_t)castle, &candidates);
        int false_count = 0, missed_count = 0, false_ep = 0, false_other = 0;
        int missed_ep = 0, missed_other = 0;
        for (int i = 0; i < candidates.count; ++i) if (!has(&legal, candidates.moves[i])) {
            ++false_count;
            const int from = MOVE_FROM(candidates.moves[i]), to = MOVE_TO(candidates.moves[i]);
            if (truth.piece[from] == PAWN && to == ep && truth.piece[to] == NO_PIECE) ++false_ep;
            else ++false_other;
        }
        for (int i = 0; i < legal.count; ++i) if (!has(&candidates, legal.moves[i])) {
            ++missed_count;
            const int from = MOVE_FROM(legal.moves[i]), to = MOVE_TO(legal.moves[i]);
            if (truth.piece[from] == PAWN && to == ep && truth.piece[to] == NO_PIECE) ++missed_ep;
            else ++missed_other;
        }
        printf("%d\t%d\t%d\t%d\t%d\t%d\t%d\n", candidates.count, false_count,
               missed_count, false_ep, false_other, missed_ep, missed_other);
    }
    return 0;
}
