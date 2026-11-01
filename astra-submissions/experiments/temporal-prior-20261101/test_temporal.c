#include "temporal.h"
#include <assert.h>
#include <stdio.h>

static Move move(const Position *p,const char *uci) {
    MoveList l;generate_moves(p,&l);
    for(int i=0;i<l.count;++i){char s[6];move_to_uci(l.moves[i],s);if(!strcmp(s,uci))return l.moves[i];}
    fprintf(stderr,"missing move %s\n",uci);assert(0);return 0;
}
static void play(Position *p,TemporalHistory *h,const char *uci) {
    Move m=move(p,uci);temporal_advance(h,p,m);Undo u;make_move(p,m,&u);
}
static void features(const Position *p,const TemporalHistory *h,const char *uci,float *x) {
    temporal_features(h,p,move(p,uci),x);
}
int main(void) {
    fow_init();Position p;pos_start(&p);TemporalHistory h={0};float x[TP_FEATURES],y[TP_FEATURES];
    features(&p,&h,"g1f3",x);for(int i=0;i<TP_FEATURES;++i)assert(x[i]==0);
    play(&p,&h,"g1f3");features(&p,&h,"g8f6",x);
    for(int i=0;i<TP_FEATURES;++i)assert(x[i]==0); /* other side has no own history */
    play(&p,&h,"g8f6");features(&p,&h,"f3g1",x);
    assert(x[KNIGHT*6+KNIGHT]==1 && x[36+KNIGHT]==1 && x[48]==1 && x[49]==0);
    features(&p,&h,"b1c3",y);assert(y[36+KNIGHT]==0 && y[48]==0);
    play(&p,&h,"f3g1");play(&p,&h,"f6g8");features(&p,&h,"g1f3",x);assert(x[49]==1);
    /* Mirrored colour has identical temporal representation. */
    play(&p,&h,"g1f3");features(&p,&h,"g8f6",y);
    for(int i=0;i<TP_FEATURES;++i)assert(x[i]==y[i]);
    /* En-passant is a capture despite an empty destination. */
    pos_clear(&p);p.side=WHITE;pos_put(&p,0,WHITE,KING);pos_put(&p,63,BLACK,KING);
    pos_put(&p,36,WHITE,PAWN);pos_put(&p,35,BLACK,PAWN);p.ep=43;memset(&h,0,sizeof(h));
    play(&p,&h,"e5d6");assert(h.side[WHITE].captured_value==1);
    play(&p,&h,"h8g8");features(&p,&h,"d6d7",x);
    assert(x[42+PAWN]==1 && x[50]==0 && x[51]>0.11f && x[51]<0.12f);
    /* Promotion history follows the new piece type, not its former pawn. */
    pos_clear(&p);p.side=WHITE;pos_put(&p,0,WHITE,KING);pos_put(&p,56,BLACK,KING);
    pos_put(&p,52,WHITE,PAWN);memset(&h,0,sizeof(h));
    play(&p,&h,"e7e8q");play(&p,&h,"a8b8");features(&p,&h,"e8e7",x);
    assert(x[QUEEN*6+QUEEN]==1 && x[36+QUEEN]==1 && x[36+PAWN]==0);
    /* Castling's relocated rook is not the previously moved king. */
    pos_clear(&p);p.side=WHITE;pos_put(&p,4,WHITE,KING);pos_put(&p,7,WHITE,ROOK);
    pos_put(&p,60,BLACK,KING);p.castle_rooks=1ULL<<7;memset(&h,0,sizeof(h));
    play(&p,&h,"e1g1");play(&p,&h,"e8d8");features(&p,&h,"f1e1",x);
    assert(x[KING*6+ROOK]==1 && x[36+ROOK]==0);
    /* Prior-capture value and consecutive capture are action-dependent. */
    pos_clear(&p);p.side=WHITE;pos_put(&p,0,WHITE,KING);pos_put(&p,63,BLACK,KING);
    pos_put(&p,8,WHITE,ROOK);pos_put(&p,16,BLACK,QUEEN);pos_put(&p,18,BLACK,BISHOP);
    memset(&h,0,sizeof(h));play(&p,&h,"a2a3");play(&p,&h,"h8g8");
    features(&p,&h,"a3c3",x);assert(x[42+ROOK]==1 && x[50]==1 && x[51]==1);
    features(&p,&h,"a3b3",y);assert(y[50]==0);
    puts("temporal feature invariants: both colours, history isolation, continuity, captures, EP, promotion, castling pass");
    return 0;
}
