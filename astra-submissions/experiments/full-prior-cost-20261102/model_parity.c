/* Compare both public feature exports and bitwise logits with a separately
 * compiled original v37 model on every supplied snapshot world and legal move. */
#include "snapshot.h"
#include "movemodel.h"
#include <inttypes.h>

void reference_move_logits(const Position *, const MoveList *, Move, int, float *);
void reference_move_features(const Position *, Move, Move, int, float *);

int main(int argc, char **argv) {
    assert(argc == 2);
    fow_init(); zobrist_init();
    Belief b; snapshot_load(&b, argv[1]);
    uint64_t scored = 0, exported = 0;
    for (size_t i = 0; i < b.count; ++i) {
        const Position *p = &b.items[i]; MoveList list; generate_moves(p, &list);
        for (int full = 0; full <= 1; ++full) {
            float a[256], z[256];
            move_logits(p, &list, b.last_own, full, a);
            reference_move_logits(p, &list, b.last_own, full, z);
            assert(memcmp(a, z, list.count * sizeof(float)) == 0);
            scored += list.count;
            /* Public training exports still calculate every feature, including
             * the zero-weight hidden ones. Test each legal move independently. */
            for (int j = 0; j < list.count; ++j) {
                float x[MM_FEATURES], y[MM_FEATURES];
                move_features(p, list.moves[j], b.last_own, full, x);
                reference_move_features(p, list.moves[j], b.last_own, full, y);
                assert(memcmp(x, y, sizeof x) == 0); ++exported;
            }
        }
    }
    printf("{\"worlds\":%zu,\"logits_bit_identical\":%" PRIu64 ",\"feature_vectors_bit_identical\":%" PRIu64 "}\n", b.count, scored, exported);
    belief_free(&b);
    return 0;
}
