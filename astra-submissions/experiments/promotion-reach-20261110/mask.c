/* Fixed-population arithmetic comparison; no belief update or search. */
#define main unused_native_protocol_main
#include "main.c"
#undef main
#include "ledger.h"

int main(void) {
    fow_init(); zobrist_init();
    size_t n; int us;
    if (scanf("%zu %d", &n, &us) != 2 || n == 0 || n > 200000) return 2;
    Belief b = {0}; b.count = n; b.us = us;
    b.items = calloc(n, sizeof(Position)); b.logw = malloc(n * sizeof(float));
    if (!b.items || !b.logw) return 3;
    for (size_t i = 0; i < n; ++i) {
        char board[65]; int side, ep, halfmove; unsigned long long castle;
        if (scanf("%64s %d %llx %d %d %f", board, &side, &castle, &ep, &halfmove, &b.logw[i]) != 6) return 4;
        if (pos_from_board_string(&b.items[i], board, side, castle, ep) < 0) return 5;
        b.items[i].halfmove = halfmove;
    }
    MoveList moves; generate_moves(&b.items[0], &moves);
    for (int a = 0; a < moves.count; ++a) {
        double k1,kt,q1,qt,n1,nt;char text[6];move_to_uci(moves.moves[a],text);
        king_risks(&b,moves.moves[a],20000,2.0,&k1,&kt);
        queen_risks(&b,moves.moves[a],20000,2.0,4,&q1,&qt);
        ledger_queen_risks(&b,moves.moves[a],20000,2.0,4,&n1,&nt);
        printf("{\"move\":\"%s\",\"king\":[%.17g,%.17g],\"old_queen\":[%.17g,%.17g],\"ledger_queen\":[%.17g,%.17g]}\n",text,k1,kt,q1,qt,n1,nt);
    }
    free(b.items);free(b.logw);return 0;
}
