/* Isolated supervised exporter. True boards/views validate and label data;
 * they never become additional model features. Output binary: 4 int32 header
 * [magic, static F, temporal F, row F]; then 9 int32 + n*row F float32 per turn. */
#include "temporal.h"
#include <stdio.h>
#include <stdlib.h>

static int die(const char *s,int game,int ply) {
    fprintf(stderr,"ERROR game=%d ply=%d %s\n",game,ply,s);return 2;
}
static int equal_frame(const Position *p,const char *b,const char *w,const char *k) {
    char actual[65];
    pos_to_board_string(p,actual);if(strcmp(actual,b))return 0;
    observation(p,WHITE,actual);if(strcmp(actual,w))return 0;
    observation(p,BLACK,actual);return strcmp(actual,k)==0;
}
int main(int argc,char **argv) {
    if(argc!=3)return die("usage: extract input.txt output.bin",-1,-1);
    FILE *in=fopen(argv[1],"r"),*out=fopen(argv[2],"wb");
    if(!in||!out)return die("cannot open files",-1,-1);
    const int F=MM_FEATURES+TP_FEATURES+4;
    const int32_t header[4]={0x54503131,MM_FEATURES,TP_FEATURES,F};
    if(fwrite(header,sizeof(int32_t),4,out)!=4)return 2;
    fow_init(); Position p; TemporalHistory history={0};
    Move previous=0; int game=-1,ply=0,ids[2]={-1,-1};
    long games=0,frames=0,positions=0,actions=0;
    char line[1024]; float x[256*(39+TP_FEATURES+4)];
    _Static_assert(MM_FEATURES==39,"update schema explicitly when static features change");
    while(fgets(line,sizeof(line),in)) {
        if(!strncmp(line,"game ",5)) {
            if(sscanf(line+5,"%d %d %d",&game,&ids[0],&ids[1])!=3)return die("bad header",game,ply);
            pos_start(&p);memset(&history,0,sizeof(history));previous=0;ply=0;++games;
            continue;
        }
        char uci[8],board[65],white[65],black[65];
        if(sscanf(line,"%7s %64s %64s %64s",uci,board,white,black)!=4 || game<0)
            return die("bad frame",game,ply);
        if(!strcmp(uci,"initial")) {
            if(ply || !equal_frame(&p,board,white,black))return die("initial mismatch",game,ply);
            ++frames;continue;
        }
        MoveList moves;generate_moves(&p,&moves);int played=-1;
        for(int i=0;i<moves.count;++i) {char u[6];move_to_uci(moves.moves[i],u);if(!strcmp(u,uci))played=i;}
        if(played<0)return die("illegal recorded move",game,ply);
        Position actual=p;Undo undo;make_move(&actual,moves.moves[played],&undo);
        if(!equal_frame(&actual,board,white,black))return die("board/view mismatch",game,ply);
        ++frames;
        if(ids[p.side]>=0) {
            const bb_t vis=visible_squares(&p,p.side);
            const char *observed=p.side==WHITE?black:white;
            for(int i=0;i<moves.count;++i) {
                float *row=x+i*F;
                move_features_obs(&p,moves.moves[i],previous,1,vis,row);
                temporal_features(&history,&p,moves.moves[i],row+MM_FEATURES);
                const int j=MM_FEATURES+TP_FEATURES;
                row[j]=(float)p.piece[MOVE_FROM(moves.moves[i])];
                row[j+1]=(float)move_mirror_square(p.side,MOVE_FROM(moves.moves[i]));
                row[j+2]=(float)move_mirror_square(p.side,MOVE_TO(moves.moves[i]));
                Position q=p;make_move(&q,moves.moves[i],&undo);char v[65];observation(&q,p.side^1,v);
                row[j+3]=king_square(&q,p.side^1)>=0 && !mover_left_king_capturable(&q) && !strcmp(v,observed);
            }
            const RecentOwn *r=&history.side[p.side];
            const int32_t h[9]={game,ply,p.side,ids[p.side],moves.count,played,r->known?r->type:-1,r->captured_value,r->continued};
            if(fwrite(h,sizeof(int32_t),9,out)!=9 || fwrite(x,sizeof(float),(size_t)moves.count*F,out)!=(size_t)moves.count*F)
                return die("write failed",game,ply);
            ++positions;actions+=moves.count;
            if(actions*(long)F*4L+positions*36L>1500000000L)return die("feature size cap",game,ply);
        }
        temporal_advance(&history,&p,moves.moves[played]);
        previous=moves.moves[played];p=actual;++ply;
    }
    if(ferror(in)||fclose(out))return die("I/O failed",game,ply);
    fclose(in);
    fprintf(stderr,"{\"games\":%ld,\"frames_validated\":%ld,\"positions\":%ld,\"actions\":%ld,\"static\":%d,\"temporal\":%d}\n",games,frames,positions,actions,MM_FEATURES,TP_FEATURES);
    return 0;
}
