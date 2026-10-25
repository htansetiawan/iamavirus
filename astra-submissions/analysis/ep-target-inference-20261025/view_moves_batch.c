#include <stdio.h>
#include <string.h>

#include "src/belief.h"

int main(void) {
    char line[256], view[65], wanted[6], side_char;
    unsigned long long castle;
    fow_init();
    while (fgets(line, sizeof line, stdin)) {
        if (sscanf(line, " %c %llx %5s %64s", &side_char, &castle, wanted, view) != 4 ||
            strlen(view) != 64) {
            puts("ERR");
            continue;
        }
        const int side = side_char == 'b' ? BLACK : WHITE;
        MoveList moves;
        view_moves(view, side, (bb_t)castle, &moves);
        int found = 0;
        for (int i = 0; i < moves.count; ++i) {
            char uci[6];
            move_to_uci(moves.moves[i], uci);
            if (strcmp(uci, wanted) == 0) { found = 1; break; }
        }
        puts(found ? "1" : "0");
    }
    return 0;
}
