#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "build/src/belief.h"
#include "collector.h"

static void setup(Position *p,int dangerous,int black){
    int x=black?56:0;
    pos_clear(p);p->side=black;
    pos_put(p,4^x,black,KING);pos_put(p,8^x,black,PAWN);
    pos_put(p,63^x,black^1,KING);pos_put(p,(dangerous?60:56)^x,black^1,ROOK);
}

int main(void){
    fow_init();
    for(int black=0;black<2;++black){
        Position p[2];setup(&p[0],1,black);setup(&p[1],0,black);
        int x=black?56:0;
        float lw[2]={(float)log(.25),0};Belief b={0};b.items=p;b.count=2;b.logw=lw;
        MoveList a={0};a.count=3;a.moves[0]=MAKE_MOVE(8^x,16^x,NO_PIECE);
        a.moves[1]=MAKE_MOVE(4^x,3^x,NO_PIECE);a.moves[2]=MAKE_MOVE(8^x,32^x,NO_PIECE);
        AstraKingRisk out[256];astra_king_risks(&b,&a,2,out);
        assert(fabs(out[0].flat-1.0/3)<2e-8 && fabs(out[0].sharp-.2)<2e-8);
        assert(out[0].uniform==.5 && out[0].invalid==0 && out[0].scanned==2);
        assert(out[1].sharp==0 && out[1].invalid==0);
        assert(out[2].sharp==0 && fabs(out[2].invalid-1)<1e-12);
        /* Capturing their king takes priority over exposing our king. */
        b.count=1;pos_remove(&p[0],63^x);pos_put(&p[0],12^x,black^1,KING);
        a.count=1;a.moves[0]=MAKE_MOVE(4^x,12^x,NO_PIECE);
        astra_king_risks(&b,&a,2,out);assert(out[0].sharp==0 && out[0].invalid==0);
        b.count=0;astra_king_risks(&b,&a,2,out);assert(out[0].scanned==0 && out[0].sharp==0);
    }
    puts("collector: both colours, posterior weighting, safe/fatal, illegal move and king-capture precedence pass");
    return 0;
}
