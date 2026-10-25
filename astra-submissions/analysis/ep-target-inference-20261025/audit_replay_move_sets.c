#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/belief.h"

static int has(const MoveList *list, Move move) {
    for (int i = 0; i < list->count; ++i) if (list->moves[i] == move) return 1;
    return 0;
}

static void print_examples(const MoveList *list, const MoveList *other) {
    int shown = 0;
    for (int i = 0; i < list->count && shown < 8; ++i) {
        if (has(other, list->moves[i])) continue;
        char uci[6];
        move_to_uci(list->moves[i], uci);
        if (shown) putchar(',');
        fputs(uci, stdout);
        ++shown;
    }
    if (!shown) putchar('-');
}

int main(void) {
    fow_init();
    char line[512], side_char, board[65], view[65];
    unsigned long long castle;
    int ep;
    while (fgets(line, sizeof(line), stdin)) {
        if (sscanf(line, " %c %llx %d %64s %64s", &side_char, &castle, &ep, board, view) != 5 ||
            strlen(board) != 64 || strlen(view) != 64) return 2;
        const int side = side_char == 'b' ? BLACK : WHITE;
        Position truth;
        if (pos_from_board_string(&truth, board, side, (bb_t)castle, ep) != 0) return 3;
        MoveList legal, candidates;
        generate_moves(&truth, &legal);
        view_moves(view, side, (bb_t)castle, &candidates);
        int false_count = 0, missed_count = 0;
        int false_ep = 0, false_other = 0, missed_ep = 0, missed_other = 0;
        for (int i = 0; i < candidates.count; ++i) if (!has(&legal, candidates.moves[i])) {
            ++false_count;
            int from = MOVE_FROM(candidates.moves[i]), to = MOVE_TO(candidates.moves[i]);
            if (truth.piece[from] == PAWN && to == ep && truth.piece[to] == NO_PIECE) ++false_ep;
            else ++false_other;
        }
        for (int i = 0; i < legal.count; ++i) if (!has(&candidates, legal.moves[i])) {
            ++missed_count;
            int from = MOVE_FROM(legal.moves[i]), to = MOVE_TO(legal.moves[i]);
            if (truth.piece[from] == PAWN && to == ep && truth.piece[to] == NO_PIECE) ++missed_ep;
            else ++missed_other;
        }
        printf("%d\t%d\t%d\t%d\t%d\t%d\t%d\t", candidates.count, false_count, missed_count,
               false_ep, false_other, missed_ep, missed_other);
        print_examples(&candidates, &legal);
        putchar('\t');
        print_examples(&legal, &candidates);
        putchar('\n');
    }
    return 0;
}
