#include "belief.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static Move find(const Position *p,const char *s) {
    MoveList l;generate_moves(p,&l);
    for(int i=0;i<l.count;++i){char t[6];move_to_uci(l.moves[i],t);if(!strcmp(s,t))return l.moves[i];}
    assert(!"fixture move must be legal");return 0;
}
static int equal(const Position *p,const Position *q) {
    return !memcmp(p->by_color,q->by_color,sizeof p->by_color) &&
           !memcmp(p->by_type,q->by_type,sizeof p->by_type) &&
           !memcmp(p->piece,q->piece,sizeof p->piece) &&
           !memcmp(p->color,q->color,sizeof p->color) && p->side==q->side &&
           p->castle_rooks==q->castle_rooks && p->ep==q->ep && p->halfmove==q->halfmove;
}
static void check(const Belief *b) {
    for(size_t i=0;i<b->count;++i){
        AstraContext c;assert(astra_ancestry_context(b,i,&c));
        Position p=c.ancestor;Undo u;
        MoveList moves;generate_moves(&p,&moves);int legal=0;
        for(int j=0;j<moves.count;++j)legal|=moves.moves[j]==c.own;
        assert(legal);make_move(&p,c.own,&u);assert(!mover_left_king_capturable(&p));
        char ours[65],theirs[65];observation(&p,b->us,ours);observation(&p,b->us^1,theirs);
        uint64_t own=history_mix(history_mix(c.own_before,c.own),view_hash(ours));
        uint64_t opponent=history_mix(c.opponent_before,view_hash(theirs));
        generate_moves(&p,&moves);legal=0;
        for(int j=0;j<moves.count;++j)legal|=moves.moves[j]==c.opponent;
        assert(legal);make_move(&p,c.opponent,&u);assert(!mover_left_king_capturable(&p));
        observation(&p,b->us,ours);observation(&p,b->us^1,theirs);
        own=history_mix(own,view_hash(ours));
        opponent=history_mix(history_mix(opponent,c.opponent),view_hash(theirs));
        assert(own==c.own_now && opponent==c.opponent_now && equal(&p,&c.current));
    }
}

/* This constructor is TEST ONLY. Production enable accepts the standard start.
 * Fixtures set an explicit initial history for a small legal two-ply game. */
static void fixture(Position p,const char *own,const char *reply,int us) {
    fprintf(stderr,"fixture %s %s color=%d\n",own,reply,us);
    Belief b;belief_init_start(&b,us,200000);b.items[0]=p;
    char view[65];observation(&p,us^1,view);b.hist[0]=history_mix(0,view_hash(view));
    b.ancestry=calloc(1,sizeof(AstraAncestry));b.ancestry->natural=1;
    observation(&p,us,view);b.ancestry->own_now=history_mix(0,view_hash(view));
    Move a=find(&p,own);Undo u;make_move(&p,a,&u);assert(!mover_left_king_capturable(&p));
    observation(&p,us,view);assert(belief_after_own(&b,a,view)>0);
    Move r=find(&p,reply);make_move(&p,r,&u);assert(!mover_left_king_capturable(&p));
    observation(&p,us,view);assert(belief_after_opponent(&b,view)>0);check(&b);
    if(b.count>1){belief_shrink(&b,b.count/2);check(&b);}
    astra_ancestry_disable(&b);assert(!b.ancestry);belief_free(&b);
}
int main(void){
    fow_init();zobrist_init();Position p;char board[65];
    /* White EP, then a king reply. */
    memset(board,'-',64);board[64]=0;board[4]='K';board[63]='k';board[36]='P';board[35]='p';
    assert(!pos_from_board_string(&p,board,WHITE,0,43));fixture(p,"e5d6","h8g8",WHITE);
    /* Black EP. */
    memset(board,'-',64);board[4]='K';board[63]='k';board[27]='p';board[28]='P';
    assert(!pos_from_board_string(&p,board,BLACK,0,20));fixture(p,"d4e3","e1d1",BLACK);
    /* Both castling directions/colors. */
    memset(board,'-',64);board[4]='K';board[0]='R';board[7]='R';board[60]='k';board[48]='p';
    assert(!pos_from_board_string(&p,board,WHITE,UINT64_C(129),-1));fixture(p,"e1g1","a7a6",WHITE);
    fixture(p,"e1c1","a7a6",WHITE);
    memset(board,'-',64);board[4]='K';board[60]='k';board[56]='r';board[63]='r';board[8]='P';
    assert(!pos_from_board_string(&p,board,BLACK,(UINT64_C(1)<<56)|(UINT64_C(1)<<63),-1));
    fixture(p,"e8g8","a2a3",BLACK);fixture(p,"e8c8","a2a3",BLACK);
    /* Promotion, underpromotion and captures. */
    memset(board,'-',64);board[4]='K';board[63]='k';board[48]='P';
    assert(!pos_from_board_string(&p,board,WHITE,0,-1));fixture(p,"a7a8q","h8g7",WHITE);
    fixture(p,"a7a8n","h8g7",WHITE);
    memset(board,'-',64);board[4]='K';board[63]='k';board[26]='B';board[35]='p';
    assert(!pos_from_board_string(&p,board,WHITE,0,-1));fixture(p,"c4d5","h8h7",WHITE);
    /* Actual start, cap, shrink and next-turn ownership replacement. */
    Belief b;belief_init_start(&b,WHITE,7);assert(astra_ancestry_enable(&b));
    assert(!astra_ancestry_enable(&b));pos_start(&p);
    const char *moves[]={"e2e4","a7a6","d2d4","b7b6"};
    for(int j=0;j<4;++j){Move m=find(&p,moves[j]);Undo u;make_move(&p,m,&u);observation(&p,WHITE,board);
        if(!(j&1))assert(belief_after_own(&b,m,board));else{assert(belief_after_opponent(&b,board));check(&b);}
        if(b.count>4)belief_shrink(&b,4);
    }
    assert(b.overflowed);check(&b);
    int their[6]={8,2,2,2,1,1};
    belief_resample(&b,board,their,UINT64_C(129),4,200);
    assert(!b.ancestry->natural && !b.ancestry->pool.items && !b.ancestry->origin);
    AstraContext c;assert(!astra_ancestry_context(&b,0,&c));belief_free(&b);
    puts("ancestry units passed: EP both colors, castle both wings/colors, promotion, underpromotion, capture, cap, shrink, replacement, recovery exclusion");
    return 0;
}
