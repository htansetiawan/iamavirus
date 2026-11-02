/* Native fixtures use the actual static queen_risks function. */
#define main mist_protocol_main
#include ASTRA_MAIN_SOURCE
#undef main

static Move uci_move(const Position *p, const char *uci) {
    MoveList moves; generate_moves(p,&moves);
    for (int i=0;i<moves.count;++i) {
        char u[6];move_to_uci(moves.moves[i],u);
        if (!strcmp(u,uci)) return moves.moves[i];
    }
    fprintf(stderr,"fixture move missing: %s\n",uci);exit(3);
}
static void measure(const char *name, Position p, const char *uci, int expected, int flip) {
    Move m=uci_move(&p,uci);
    if (flip) {
        Position q;pos_clear(&q);q.side=p.side^1;
        for (int s=0;s<64;++s) if(p.piece[s]!=NO_PIECE)pos_put(&q,63-s,p.color[s]^1,p.piece[s]);
        p=q;m=MAKE_MOVE(63-MOVE_FROM(m),63-MOVE_TO(m),MOVE_PROMO(m));
    }
    Belief b={0};float weight=0;b.items=&p;b.count=1;b.logw=&weight;b.us=p.side;
    double risk,sharp;queen_risks(&b,m,20000,2,4,&risk,&sharp);
    char board[65],u[6];pos_to_board_string(&p,board);move_to_uci(m,u);
    printf("{\"name\":\"%s\",\"flipped\":%d,\"board\":\"%s\",\"side\":%d,\"move\":\"%s\",\"expected\":%d,\"risk\":%.17g,\"sharp\":%.17g}\n",name,flip,board,p.side,u,expected,risk,sharp);
}
int main(void) {
    fow_init();zobrist_init();
    for(int flip=0;flip<2;++flip) {
        Position p;pos_clear(&p);p.side=WHITE;
        pos_put(&p,6,WHITE,KING);pos_put(&p,60,BLACK,KING);pos_put(&p,43,WHITE,QUEEN);pos_put(&p,3,WHITE,ROOK);
        measure("king_captures_defended_queen",p,"d6d7",0,flip);
        pos_remove(&p,3);measure("king_captures_undefended_queen",p,"d6d7",1,flip);
        pos_clear(&p);p.side=WHITE;pos_put(&p,6,WHITE,KING);pos_put(&p,60,BLACK,KING);
        pos_put(&p,4,WHITE,ROOK);pos_put(&p,52,BLACK,KNIGHT);pos_put(&p,29,WHITE,QUEEN);
        measure("pinned_knight_captures_queen",p,"f4f5",0,flip);
        pos_remove(&p,60);pos_put(&p,59,BLACK,KING);measure("free_knight_captures_queen",p,"f4f5",1,flip);
    }
    return 0;
}
