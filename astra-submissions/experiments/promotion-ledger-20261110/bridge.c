/* Compare original, incomplete root credit, and full promotion ledger. */
#define main unused_original_protocol_main
#include "main.c"
#undef main

static void root_credit_queen_risks(const Belief *b, Move m, size_t cap, double temp, int threshold, double *r1, double *rt) {
    const size_t stride = b->count > cap ? (b->count + cap - 1) / cap : 1;
    double t1 = 0, l1 = 0, tt = 0, lt = 0;
    for (size_t i = 0; i < b->count; i += stride) {
        const double lw = b->logw ? (double)b->logw[i] : 0.0;
        const double wt = exp(lw), w1 = exp(lw / temp);
        Position p = b->items[i];
        t1 += w1; tt += wt;
        const int to = MOVE_TO(m);
        if (p.piece[to] == KING && p.color[to] != p.side) continue;   /* takes the king: won */
        int got = p.piece[to] != NO_PIECE && p.color[to] != p.side ? piece_pawns[p.piece[to]] : 0;
        if (!got && p.piece[MOVE_FROM(m)] == PAWN && to == p.ep) got = 1;
        const int promotion = MOVE_PROMO(m);
        if (p.piece[MOVE_FROM(m)] == PAWN && promotion != NO_PIECE)
            got += piece_pawns[promotion] - piece_pawns[PAWN];
        Undo u;
        make_move(&p, m, &u);
        if (mover_left_king_capturable(&p)) continue;
        const int us = p.side ^ 1;
        int best = 0;
        for (int sq = 0; sq < 64; ++sq) {
            if (p.piece[sq] != QUEEN || p.color[sq] != us || !is_attacked(&p, sq, p.side)) continue;
            MoveList l; generate_moves(&p, &l);
            for (int j = 0; j < l.count; ++j) {
                if (MOVE_TO(l.moves[j]) != sq) continue;
                int gain = piece_pawns[QUEEN];
                Position q = p; Undo v; make_move(&q, l.moves[j], &v);
                if (is_attacked(&q, sq, us)) gain -= piece_pawns[p.piece[MOVE_FROM(l.moves[j])]];
                if (gain > best) best = gain;
            }
        }
        if (best - got >= threshold) { l1 += w1; lt += wt; }
    }
    *r1 = t1 > 0 ? l1 / t1 : 0;
    *rt = tt > 0 ? lt / tt : 0;
}

static void ledger_queen_risks(const Belief *b, Move m, size_t cap, double temp, int threshold, double *r1, double *rt) {
    const size_t stride = b->count > cap ? (b->count + cap - 1) / cap : 1;
    double t1 = 0, l1 = 0, tt = 0, lt = 0;
    for (size_t i = 0; i < b->count; i += stride) {
        const double lw = b->logw ? (double)b->logw[i] : 0.0;
        const double wt = exp(lw), w1 = exp(lw / temp);
        Position p = b->items[i];
        t1 += w1; tt += wt;
        const int to = MOVE_TO(m);
        if (p.piece[to] == KING && p.color[to] != p.side) continue;   /* takes the king: won */
        int got = p.piece[to] != NO_PIECE && p.color[to] != p.side ? piece_pawns[p.piece[to]] : 0;
        if (!got && p.piece[MOVE_FROM(m)] == PAWN && to == p.ep) got = 1;
        const int promotion = MOVE_PROMO(m);
        if (p.piece[MOVE_FROM(m)] == PAWN && promotion != NO_PIECE)
            got += piece_pawns[promotion] - piece_pawns[PAWN];
        Undo u;
        make_move(&p, m, &u);
        if (mover_left_king_capturable(&p)) continue;
        const int us = p.side ^ 1;
        int best = 0;
        for (int sq = 0; sq < 64; ++sq) {
            if (p.piece[sq] != QUEEN || p.color[sq] != us || !is_attacked(&p, sq, p.side)) continue;
            MoveList l; generate_moves(&p, &l);
            for (int j = 0; j < l.count; ++j) {
                if (MOVE_TO(l.moves[j]) != sq) continue;
                int gain = piece_pawns[QUEEN];
                const int promotion = MOVE_PROMO(l.moves[j]);
                if (p.piece[MOVE_FROM(l.moves[j])] == PAWN && promotion != NO_PIECE)
                    gain += piece_pawns[promotion] - piece_pawns[PAWN];
                Position q = p; Undo v; make_move(&q, l.moves[j], &v);
                if (is_attacked(&q, sq, us)) gain -= piece_pawns[q.piece[sq]];
                if (gain > best) best = gain;
            }
        }
        if (best - got >= threshold) { l1 += w1; lt += wt; }
    }
    *r1 = t1 > 0 ? l1 / t1 : 0;
    *rt = tt > 0 ? lt / tt : 0;
}

int main(void) {
    fow_init(); zobrist_init();
    char board[65], move_text[8]; int side, ep, threshold, index=0;
    unsigned long long castle;
    while (scanf("%64s %d %llx %d %7s %d",board,&side,&castle,&ep,move_text,&threshold)==6) {
        Position p; if(pos_from_board_string(&p,board,side,castle,ep)<0)return 2;
        MoveList legal; generate_moves(&p,&legal); Move move=0; int found=0;
        for(int i=0;i<legal.count;++i){char u[6];move_to_uci(legal.moves[i],u);if(strcmp(u,move_text)==0){move=legal.moves[i];found=1;break;}}
        if(!found)return 3;
        Belief b={0};b.items=&p;b.count=1;b.us=side;
        double a,c,d,e,f,g;queen_risks(&b,move,1,2.0,threshold,&a,&c);root_credit_queen_risks(&b,move,1,2.0,threshold,&d,&e);ledger_queen_risks(&b,move,1,2.0,threshold,&f,&g);
        printf("{\"case\":%d,\"old\":[%.17g,%.17g],\"root_credit\":[%.17g,%.17g],\"ledger\":[%.17g,%.17g]}\n",index++,a,c,d,e,f,g);
    }
    return 0;
}
