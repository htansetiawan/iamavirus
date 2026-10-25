/* Semantic fixtures for the appended research feature. Compile against the
 * patched v35 src/ tree produced by build_hidden_slider_zone_candidate.py. */
#include "fow.h"
#include "movemodel.h"

#include <math.h>
#include <stdio.h>

static int features_for(Position *p, int from, int to, int full, float out[MM_FEATURES]) {
    MoveList legal;
    generate_moves(p, &legal);
    const Move wanted = MAKE_MOVE(from, to, NO_PIECE);
    int found = 0;
    for (int i = 0; i < legal.count; ++i) if (legal.moves[i] == wanted) found = 1;
    if (!found) return 0;
    move_features(p, wanted, 0, full, out);
    return 1;
}

static void base(Position *p) {
    pos_clear(p);
    p->side = WHITE;
    p->castle_rooks = 0;
    p->ep = -1;
    pos_put(p, 0, WHITE, ROOK);  /* a1 */
    pos_put(p, 7, WHITE, KING);  /* h1 */
    pos_put(p, 60, BLACK, KING); /* e8 */
}

int main(void) {
    fow_init();
    float x[MM_FEATURES];
    char view[65];
    Position p, q;

    /* Ra1-a7 is hidden from the lone king on e8 but attacks e7, a king-zone
     * square. It sets up a concealed attack without giving check. */
    base(&p);
    if (!features_for(&p, 0, 48, 1, x)) return 1;
    q = p; Undo u; make_move(&q, MAKE_MOVE(0, 48, NO_PIECE), &u);
    observation(&q, BLACK, view);
    if (view[48] != '?' || x[MM_CHECK] != 0 || x[MM_KING_ZONE] <= 0 ||
        x[MM_HIDDEN_SLIDER_ZONE] != x[MM_KING_ZONE]) {
        fprintf(stderr, "hidden case failed: view=%c check=%.3f zone=%.3f hidden=%.3f\n",
                view[48], x[MM_CHECK], x[MM_KING_ZONE], x[MM_HIDDEN_SLIDER_ZONE]);
        return 2;
    }
    if (!features_for(&p, 0, 48, 0, x) || x[MM_HIDDEN_SLIDER_ZONE] <= 0) {
        fprintf(stderr, "cheap hidden case failed: hidden=%.3f\n", x[MM_HIDDEN_SLIDER_ZONE]);
        return 3;
    }

    /* A black rook on b7 sees a7, so the same geometry is not concealed. */
    base(&p); pos_put(&p, 49, BLACK, ROOK);
    if (!features_for(&p, 0, 48, 1, x)) return 4;
    q = p; make_move(&q, MAKE_MOVE(0, 48, NO_PIECE), &u);
    observation(&q, BLACK, view);
    if (view[48] == '?' || x[MM_HIDDEN_SLIDER_ZONE] != 0) {
        fprintf(stderr, "visible control failed: view=%c hidden=%.3f\n",
                view[48], x[MM_HIDDEN_SLIDER_ZONE]);
        return 5;
    }
    if (!features_for(&p, 0, 48, 0, x) || x[MM_HIDDEN_SLIDER_ZONE] != 0) return 6;

    /* A hidden move with no attack into the king zone must not fire. */
    base(&p);
    if (!features_for(&p, 0, 40, 1, x)) return 7; /* Ra1-a6 */
    if (x[MM_HIDDEN_SLIDER_ZONE] != 0) {
        fprintf(stderr, "non-zone control failed: hidden=%.3f\n", x[MM_HIDDEN_SLIDER_ZONE]);
        return 8;
    }
    if (!features_for(&p, 0, 40, 0, x) || x[MM_HIDDEN_SLIDER_ZONE] != 0) return 9;
    puts("hidden-slider-zone fixtures passed");
    return 0;
}
