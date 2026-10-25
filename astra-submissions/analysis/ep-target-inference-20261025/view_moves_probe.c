#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "src/belief.h"

int main(int argc, char **argv) {
    if (argc != 4 || strlen(argv[1]) != 64) return 2;
    fow_init();
    char view[65];
    memcpy(view, argv[1], 64);
    view[64] = '\0';
    const int side = argv[2][0] == 'b' ? BLACK : WHITE;
    const bb_t castle = (bb_t)strtoull(argv[3], NULL, 0);
    MoveList moves;
    view_moves(view, side, castle, &moves);
    for (int i = 0; i < moves.count; ++i) {
        char uci[6];
        move_to_uci(moves.moves[i], uci);
        puts(uci);
    }
    return 0;
}
