/* Inserted into the isolated v38 rules engine. Direction pairs are ordered
 * by increasing and decreasing square index so the first blocker is one
 * bit scan. Knights, kings and reverse pawn origins need no occupancy walk. */
static bb_t attack_ray[64][8];
static bb_t pawn_origin[2][64];

static void init_attack_queries(void) {
    static const int direction[8][2] = {
        {1,0}, {-1,0}, {0,1}, {0,-1}, {1,1}, {-1,-1}, {-1,1}, {1,-1}
    };
    for (int sq = 0; sq < 64; ++sq) {
        int file = sq % 8, rank = sq / 8;
        for (int d = 0; d < 8; ++d) {
            int df = direction[d][0], dr = direction[d][1];
            bb_t ray = 0;
            for (int f = file + df, r = rank + dr; on_board(f,r); f += df, r += dr)
                ray |= BIT(8*r+f);
            attack_ray[sq][d] = ray;
        }
        for (int color = WHITE; color <= BLACK; ++color) {
            int origin_rank = rank + (color == WHITE ? -1 : 1);
            bb_t origins = 0;
            for (int df = -1; df <= 1; df += 2)
                if (on_board(file+df, origin_rank)) origins |= BIT(8*origin_rank+file+df);
            pawn_origin[color][sq] = origins;
        }
    }
}

static int ray_attacked(const bb_t rays[4], bb_t sliders, bb_t occupied) {
    if (!sliders) return 0;
    for (int d = 0; d < 4; ++d) {
        if (!(rays[d] & sliders)) continue;
        const bb_t blocked = rays[d] & occupied;
        const bb_t nearest = (d & 1) ? BIT(63 - __builtin_clzll(blocked)) : (blocked & -blocked);
        if (nearest & sliders) return 1;
    }
    return 0;
}

int is_attacked(const Position *p, int sq, int by_color) {
    const bb_t pieces = p->by_color[by_color];
    const bb_t close = (pawn_origin[by_color][sq] & p->by_type[PAWN]) |
                       (knight_table[sq] & p->by_type[KNIGHT]) |
                       (king_table[sq] & p->by_type[KING]);
    if (pieces & close) return 1;
    const bb_t occupied = p->by_color[WHITE] | p->by_color[BLACK];
    const bb_t queen = p->by_type[QUEEN];
    return ray_attacked(attack_ray[sq], pieces & (p->by_type[ROOK] | queen), occupied) ||
           ray_attacked(attack_ray[sq]+4, pieces & (p->by_type[BISHOP] | queen), occupied);
}
