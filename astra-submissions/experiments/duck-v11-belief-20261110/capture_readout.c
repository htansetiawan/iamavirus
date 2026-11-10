/* The production caller runs this after printing the selected move. */
#include "belief.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int decode(const char *text, Move *move) {
    size_t n = strlen(text);
    if (n != 4 && n != 5) return 0;
    int squares[2];
    for (int i = 0; i < 2; ++i) {
        int file = text[2*i]-'a', rank = text[2*i+1]-'1';
        if (file < 0 || file > 7 || rank < 0 || rank > 7) return 0;
        squares[i] = rank*8+file;
    }
    int promotion = NO_PIECE;
    if (n == 5) {
        const char types[] = "pnbrqk";
        const char *type = strchr(types, text[4]);
        if (!type || type-types < KNIGHT || type-types > QUEEN) return 0;
        promotion = (int)(type-types);
    }
    *move = MAKE_MOVE(squares[0], squares[1], promotion);
    return 1;
}

static int legal(const Position *position, Move move) {
    MoveList moves;
    generate_moves(position, &moves);
    for (int i = 0; i < moves.count; ++i) if (moves.moves[i] == move) return 1;
    return 0;
}

/* Bit 0 is occupancy by the recorded kind of attacker. Bit 1 is the
 * recorded capture, with the actor and then the capturer surviving. */
static int capture_flags(const Position *position, Move own, Move reply, int type) {
    int source = MOVE_FROM(reply);
    int opponent = position->side ^ 1;
    if (position->piece[source] != type || position->color[source] != opponent) return 0;
    if (!legal(position, own)) return 1;
    Position child = *position;
    Undo undo;
    make_move(&child, own, &undo);
    if (mover_left_king_capturable(&child) || child.piece[source] != type ||
        child.color[source] != opponent || !legal(&child, reply)) return 1;
    make_move(&child, reply, &undo);
    if (undo.captured_type == NO_PIECE || undo.captured_color != position->side ||
        mover_left_king_capturable(&child)) return 1;
    return 3;
}

int astra_capture_flags(const char *board, int side, uint64_t castle, int ep,
                        const char *own_text, const char *reply_text, int type) {
    Position position;
    Move own, reply;
    if (pos_from_board_string(&position, board, side, castle, ep) != 0 ||
        !decode(own_text, &own) || !decode(reply_text, &reply)) return -1;
    return capture_flags(&position, own, reply, type);
}

void astra_capture_readout(const Belief *belief, double temperature) {
    const char *own_text = getenv("ASTRA_RECORDED_MOVE");
    const char *reply_text = getenv("ASTRA_RECORDED_CAPTURE");
    const char *attacker = getenv("ASTRA_RECORDED_ATTACKER");
    if (!own_text || !reply_text || !attacker) return;
    const char types[] = "pnbrqk";
    const char *kind = *attacker ? strchr(types, *attacker) : NULL;
    Move own, reply;
    if (!kind || !decode(own_text, &own) || !decode(reply_text, &reply) || temperature <= 0) return;
    size_t occupancy = 0, replies = 0;
    double total[2] = {0}, piece[2] = {0}, capture[2] = {0};
    for (size_t i = 0; i < belief->count; ++i) {
        double logw = belief->logw ? belief->logw[i] : 0;
        double weight[2] = {exp(logw/temperature), exp(logw)};
        int flags = capture_flags(&belief->items[i], own, reply, (int)(kind-types));
        occupancy += (flags & 1) != 0;
        replies += (flags & 2) != 0;
        for (int j = 0; j < 2; ++j) {
            total[j] += weight[j];
            if (flags & 1) piece[j] += weight[j];
            if (flags & 2) capture[j] += weight[j];
        }
    }
    if (total[0] <= 0 || total[1] <= 0) return;
    fprintf(stderr, "astra: exact-capture {\"worlds\":%zu,\"piece_worlds\":%zu,"
            "\"capture_worlds\":%zu,\"piece_fitted\":%.17g,\"piece_sharpened\":%.17g,"
            "\"capture_fitted\":%.17g,\"capture_sharpened\":%.17g}\n",
            belief->count, occupancy, replies, piece[0]/total[0], piece[1]/total[1],
            capture[0]/total[0], capture[1]/total[1]);
}
