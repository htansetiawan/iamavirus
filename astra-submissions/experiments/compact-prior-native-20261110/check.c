#define _POSIX_C_SOURCE 200809L
#include "movemodel.h"
#include <math.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

void original_move_features(const Position *, Move, Move, int, float *);
void original_move_logits(const Position *, const MoveList *, Move, int, float *);
void compact_full_logp(const Position *, const MoveList *, Move, int, float *, float *);

typedef struct { Position board; MoveList moves; Move previous; } Sample;
static Sample samples[12000];
static int sample_count;
static volatile float benchmark_result;

static void normalize(float *out, int n) {
    float top = -INFINITY;
    for (int j = 0; j < n; ++j) if (out[j] > top) top = out[j];
    double sum = 0.0;
    for (int j = 0; j < n; ++j) sum += exp((double)(out[j] - top));
    float normalizer = top + (float)log(sum);
    for (int j = 0; j < n; ++j) out[j] -= normalizer;
}

int check_parent(const char *text, int side, uint64_t castle, int ep, int halfmove,
                 Move previous, int keep, Move *moves, float *base, float *logp,
                 float *residual, uint32_t *special) {
    Position board;
    if (pos_from_board_string(&board, text, side, castle, ep)) return -1;
    board.halfmove = halfmove;
    MoveList list;
    generate_moves(&board, &list);
    if (!list.count) return 0;
    float a[MM_FEATURES], b[MM_FEATURES], zero[256], fast[256];
    for (int j = 0; j < list.count; ++j) {
        Move move = list.moves[j];
        moves[j] = move;
        original_move_features(&board, move, previous, 1, a);
        move_features(&board, move, previous, 1, b);
        if (memcmp(a, b, sizeof a)) return -2;
        special[0] += MOVE_PROMO(move) != NO_PIECE;
        special[1] += a[MM_CASTLE] > 0;
        special[2] += board.piece[MOVE_FROM(move)] == PAWN && MOVE_TO(move) == board.ep;
    }
    original_move_logits(&board, &list, previous, 1, base);
    move_logits(&board, &list, previous, 1, fast);
    if (memcmp(base, fast, (size_t)list.count * sizeof(float))) return -3;
    normalize(base, list.count);
    compact_full_logp(&board, &list, previous, 0, zero, NULL);
    if (memcmp(base, zero, (size_t)list.count * sizeof(float))) return -4;
    compact_full_logp(&board, &list, previous, 1, logp, residual);
    for (int j = 0; j < list.count; ++j) {
        original_move_features(&board, list.moves[j], previous, 1, a);
        if (a[MM_CAPTURE] > 0 && memcmp(base + j, logp + j, sizeof(float))) return -5;
    }
    if (keep) {
        if (sample_count == (int)(sizeof samples / sizeof *samples)) return -6;
        samples[sample_count++] = (Sample){board, list, previous};
    }
    return list.count;
}

/* Actual full logits and normalizer, with the same pre-generated lists. */
double time_parents(int arm) {
    struct timespec start, end;
    float out[256], checksum = 0;
    if (clock_gettime(CLOCK_THREAD_CPUTIME_ID, &start)) return -1;
    for (int i = 0; i < sample_count; ++i) {
        const Sample *sample = samples + i;
        if (arm == 2) compact_full_logp(&sample->board, &sample->moves, sample->previous, 1, out, NULL);
        else {
            if (arm == 0) original_move_logits(&sample->board, &sample->moves, sample->previous, 1, out);
            else move_logits(&sample->board, &sample->moves, sample->previous, 1, out);
            normalize(out, sample->moves.count);
        }
        checksum += out[i % sample->moves.count];
    }
    benchmark_result = checksum;
    if (clock_gettime(CLOCK_THREAD_CPUTIME_ID, &end)) return -1;
    return (double)(end.tv_sec - start.tv_sec) + 1e-9 * (end.tv_nsec - start.tv_nsec);
}
