/* Stream candidate move features from an archived mist-c source tree.
 * Input TSV: key, board64, side, castling-bitboard-hex, en-passant-square,
 * previous-UCI-or-dash, observed-UCI. Output is one row per legal candidate:
 * key, observed-UCI, candidate-UCI, then MM_FEATURES floats.
 */
#define _POSIX_C_SOURCE 200809L
#include "fow.h"
#include "movemodel.h"

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int square(const char *s) {
    if (!s || s[0] < 'a' || s[0] > 'h' || s[1] < '1' || s[1] > '8') return -1;
    return (s[0] - 'a') + 8 * (s[1] - '1');
}

static int parse_uci(const char *s, Move *out) {
    if (!s || strlen(s) < 4 || strlen(s) > 5) return 0;
    const int from = square(s), to = square(s + 2);
    if (from < 0 || to < 0) return 0;
    int promo = NO_PIECE;
    if (s[4]) {
        switch (s[4]) {
            case 'n': promo = KNIGHT; break;
            case 'b': promo = BISHOP; break;
            case 'r': promo = ROOK; break;
            case 'q': promo = QUEEN; break;
            default: return 0;
        }
    }
    *out = MAKE_MOVE(from, to, promo);
    return 1;
}

static char *field(char **cursor) {
    if (!*cursor) return NULL;
    char *start = *cursor;
    char *tab = strchr(start, '\t');
    if (tab) { *tab = '\0'; *cursor = tab + 1; }
    else *cursor = NULL;
    return start;
}

int main(void) {
    fow_init();
    char *line = NULL;
    size_t capacity = 0;
    ssize_t length;
    while ((length = getline(&line, &capacity, stdin)) >= 0) {
        while (length > 0 && (line[length - 1] == '\n' || line[length - 1] == '\r'))
            line[--length] = '\0';
        char *rest = line;
        char *key = field(&rest), *board = field(&rest), *side_s = field(&rest);
        char *castle_s = field(&rest), *ep_s = field(&rest), *previous_s = field(&rest);
        char *actual = field(&rest);
        if (!key || !board || !side_s || !castle_s || !ep_s || !previous_s || !actual || rest) {
            fprintf(stderr, "bad input TSV row\n"); return 2;
        }
        const int side = atoi(side_s), ep = atoi(ep_s);
        errno = 0;
        char *end = NULL;
        const uint64_t castle = strtoull(castle_s, &end, 16);
        if (errno || !end || *end || (side != WHITE && side != BLACK) || strlen(board) != 64 || ep < -1 || ep > 63) {
            fprintf(stderr, "invalid position fields for %s\n", key); return 2;
        }
        Position p;
        if (pos_from_board_string(&p, board, side, castle, ep) != 0) {
            fprintf(stderr, "invalid board for %s\n", key); return 2;
        }
        Move previous = 0;
        if (strcmp(previous_s, "-") != 0 && !parse_uci(previous_s, &previous)) {
            fprintf(stderr, "invalid previous move for %s\n", key); return 2;
        }
        MoveList moves;
        generate_moves(&p, &moves);
        int label_found = 0;
        float features[MM_FEATURES];
        printf("@%s\t%s\t%d\n", key, actual, moves.count);
        fflush(stdout);
        for (int i = 0; i < moves.count; ++i) {
            char uci[6];
            move_to_uci(moves.moves[i], uci);
            if (strcmp(uci, actual) == 0) label_found = 1;
            move_features(&p, moves.moves[i], previous, 1, features);
            printf("%s\t%s\t%s", key, actual, uci);
            for (int j = 0; j < MM_FEATURES; ++j) printf("\t%.7g", features[j]);
            putchar('\n');
        }
        if (!label_found) {
            fprintf(stderr, "observed move %s absent from legal list for %s\n", actual, key);
            return 3;
        }
    }
    free(line);
    return ferror(stdin) ? 1 : 0;
}
