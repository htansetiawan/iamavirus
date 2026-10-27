/* Run against the immutable r3 main.c, not the moving engine checkout.
 * This is a characterization of a confirmed bug, not a test asserting safety.
 * ENGINE_MAIN must name the frozen source file at compile time.
 */
#define main unused_engine_main
#include ENGINE_MAIN
#undef main
#include <assert.h>

int main(void) {
    fow_init();
    Position p;
    const char *board = "-R----K-P----PP--------P----PB-p--b-----q-----p--p-R-p----r-k---";
    assert(pos_from_board_string(&p, board, WHITE, 0, -1) == 0);
    Belief b = {0}; b.items = &p; b.count = 1; b.us = WHITE;
    Move moves[2] = {MAKE_MOVE(1, 3, NO_PIECE), MAKE_MOVE(51, 49, NO_PIECE)};
    double k[2], kt[2], ku[2], q[2], qt[2], qu[2], r[2], rt[2], ru[2];
    for (int i = 0; i < 2; ++i) {
        king_risks(&b, moves[i], 20000, 2.0, &k[i], &kt[i], &ku[i]);
        queen_risks(&b, moves[i], 20000, 2.0, 4, &q[i], &qt[i], &qu[i]);
        piece_risks(&b, moves[i], 20000, 2.0, 3, 4, &r[i], &rt[i], &ru[i]);
    }
    int out[2], kqout[2]; GuardStats st;
    guard_rule(2, k, kt, ku, q, qt, qu, r, rt, ru, .9, .758, .02, -1, out, kqout, &st);
    Position after = p; Undo u, v;
    make_move(&after, moves[0], &u);
    assert(!mover_left_king_capturable(&after));
    make_move(&after, MAKE_MOVE(60, 51, NO_PIECE), &v); /* ...Ke8xd7 */
    const int opponent_loses = mover_left_king_capturable(&after);
    printf("{\"rd1_piece_risk\":%.1f,\"rxb7_piece_risk\":%.1f,"
           "\"rd1_v35_excluded\":%d,\"rd1_r3_excluded\":%d,"
           "\"rxb7_r3_excluded\":%d,\"opponent_Kxd7_loses_immediately\":%d}\n",
           r[0], r[1], kqout[0], out[0], out[1], opponent_loses);
    assert(r[0] == 1.0 && r[1] == 0.0);
    assert(!kqout[0] && out[0] && !out[1] && opponent_loses);
    return 0;
}
