#define _POSIX_C_SOURCE 200809L
#include "fow.h"
#include <time.h>
#include <stdint.h>

int reference_attack(const Position *p, int sq, int color);

enum { MAX_POSITIONS = 32000 };
static Position cases[MAX_POSITIONS];
static int count;
static volatile uint64_t sink;

static int check_position(const Position *p) {
    for (int sq = 0; sq < 64; ++sq)
        for (int color = WHITE; color <= BLACK; ++color)
            if (reference_attack(p, sq, color) != is_attacked(p, sq, color)) return 0;
    return 1;
}

int probe(const char *board, int side, uint64_t castling, int ep, int halfmove,
          int test_children, int keep) {
    Position p;
    if (pos_from_board_string(&p, board, side, castling, ep)) return -1;
    p.halfmove = halfmove;
    if (!check_position(&p)) return -2;
    if (keep) {
        if (count >= MAX_POSITIONS) return -3;
        cases[count++] = p;
    }
    if (!test_children) return 0;
    MoveList moves;
    generate_moves(&p, &moves);
    for (int j = 0; j < moves.count; ++j) {
        Undo undo;
        make_move(&p, moves.moves[j], &undo);
        if (!check_position(&p)) return -4;
        unmake_move(&p, moves.moves[j], &undo);
    }
    return moves.count;
}

typedef int (*Attack)(const Position *, int, int);

/* The common harness measures the attack calls in move_features and the
 * king-safety guards, including shared make/unmake and move generation. */
static uint64_t workload(Attack attack) {
    uint64_t result = 0;
    for (int i = 0; i < count; ++i) {
        Position p = cases[i];
        const int own = p.side, other = own ^ 1;
        MoveList moves;
        generate_moves(&p, &moves);
        for (int j = 0; j < moves.count; ++j) {
            Move move = moves.moves[j];
            const int from = MOVE_FROM(move), to = MOVE_TO(move);
            int source = p.piece[from];
            if (source != PAWN && source != KING) result += attack(&p, from, other);
            Undo undo;
            make_move(&p, move, &undo);
            int their_king = king_square(&p, other), our_king = king_square(&p, own);
            if (their_king >= 0) result += attack(&p, their_king, own);
            if (attack(&p, to, other)) result += 1 + attack(&p, to, own);
            if (our_king >= 0) result += attack(&p, our_king, other);
            unmake_move(&p, move, &undo);
        }
    }
    return result;
}

double measure(int reverse, uint64_t *checksum) {
    struct timespec start, end;
    if (clock_gettime(CLOCK_THREAD_CPUTIME_ID, &start)) return -1;
    *checksum = workload(reverse ? is_attacked : reference_attack);
    sink = *checksum;
    if (clock_gettime(CLOCK_THREAD_CPUTIME_ID, &end)) return -1;
    return (double)(end.tv_sec-start.tv_sec) + 1e-9*(end.tv_nsec-start.tv_nsec);
}
