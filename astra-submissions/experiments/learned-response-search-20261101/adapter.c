#include "adapter.h"
#include <string.h>

int visible_pack(const char view[65], int side, const Move *moves, int n,
                 uint8_t tokens[64], uint16_t encoded[256]) {
    if (!view || !moves || !tokens || !encoded || (side != 0 && side != 1) || n < 1 || n > 256) return 0;
    const int flip = side ? 56 : 0;
    for (int s = 0; s < 64; ++s) {
        int value;
        if (view[s] == '?') value = 12;
        else if (view[s] == '-') value = 13;
        else {
            const char *pieces = "PNBRQKpnbrqk", *at = strchr(pieces, view[s]);
            if (!at || !view[s]) return 0;
            const int idx = (int)(at-pieces);
            value = idx%6 + ((idx/6 == side) ? 0 : 6);
        }
        tokens[s^flip] = (uint8_t)value;
    }
    for (int a = 0; a < n; ++a) {
        const int raw = moves[a] >> 12;
        if (raw != NO_PIECE && (raw < KNIGHT || raw > QUEEN)) return 0;
        const int from = MOVE_FROM(moves[a])^flip, to = MOVE_TO(moves[a])^flip;
        if (tokens[from] > 5) return 0;
        encoded[a] = (uint16_t)(from | (to<<6) | ((raw == NO_PIECE ? 0 : raw)<<12));
    }
    return 1;
}
