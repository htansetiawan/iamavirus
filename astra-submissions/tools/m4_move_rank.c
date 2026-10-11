/* Offline truth-parent move-prior audit. Never linked into an arena bot.
 * Input matches m4_prior_replay: game ID OUR_SIDE, then UCI BOARD WHITE BLACK.
 * Conditions moves from the true parent on OUR resulting observation. This
 * is not the full belief posterior; it separates local action likelihood
 * from missing/misweighted parent states. */
#include "movemodel.h"
#include <math.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    fow_init();
    Position p; Move previous=0;
    char line[512],id[9]="",uci[8],board[65],white[65],black[65];
    int us=0,ply=0,have=0;
    while(fgets(line,sizeof(line),stdin)) {
        if(!strncmp(line,"game ",5)) {
            if(sscanf(line,"game %8s %d",id,&us)!=2 || us<0 || us>1)return 2;
            pos_start(&p);previous=0;ply=0;have=1;continue;
        }
        if(!have || sscanf(line,"%7s %64s %64s %64s",uci,board,white,black)!=4)return 2;
        MoveList list;generate_moves(&p,&list);int actual=-1;
        for(int i=0;i<list.count;++i){char s[6];move_to_uci(list.moves[i],s);if(!strcmp(s,uci))actual=i;}
        if(actual<0)return 3;
        Position next=p;Undo undo;make_move(&next,list.moves[actual],&undo);
        char check[65];pos_to_board_string(&next,check);if(strcmp(check,board))return 4;
        observation(&next,WHITE,check);if(strcmp(check,white))return 4;
        observation(&next,BLACK,check);if(strcmp(check,black))return 4;
        if(p.side!=us) {
            const char *expected=us==WHITE?white:black;
            int match[256]={0},consistent=0;
            for(int i=0;i<list.count;++i){
                Position q=p;make_move(&q,list.moves[i],&undo);observation(&q,us,check);
                match[i]=!mover_left_king_capturable(&q)&&!strcmp(check,expected);
                consistent+=match[i];
            }
            int king=king_square(&next,us),attack=0,hidden_attackers=0;
            if(king>=0)for(int sq=0;sq<64;++sq)
                if(next.color[sq]==(us^1)&&(attacks_from(&next,sq)&(1ULL<<king))){
                    ++attack;if(expected[sq]=='?')++hidden_attackers;
                }
            for(int full=0;full<=1;++full){
                float z[256],top=-INFINITY;move_logits(&p,&list,previous,full,z);
                for(int i=0;i<list.count;++i)if(z[i]>top)top=z[i];
                double total=0,kept=0;int rank=1,conditional_rank=1,best=-1;
                for(int i=0;i<list.count;++i){
                    double w=exp((double)z[i]-top);total+=w;if(match[i]){kept+=w;if(best<0||z[i]>z[best])best=i;}
                    if(z[i]>z[actual]){++rank;if(match[i])++conditional_rank;}
                }
                double w=exp((double)z[actual]-top);
                printf("{\"game\":\"%s\",\"ply\":%d,\"move\":\"%s\",\"full\":%d,\"moves\":%d,\"consistent\":%d,\"actual_consistent\":%d,\"rank\":%d,\"conditional_rank\":%d,\"probability\":%.12g,\"conditional_probability\":%.12g,\"attacker_count\":%d,\"hidden_attackers\":%d",
                    id,ply+1,uci,full,list.count,consistent,match[actual],rank,conditional_rank,w/total,
                    kept&&match[actual]?w/kept:0,attack,hidden_attackers);
                char best_uci[6]="";if(best>=0)move_to_uci(list.moves[best],best_uci);
                printf(",\"conditional_best\":\"%s\",\"actual_features\":[",best_uci);
                float x[MM_FEATURES];move_features(&p,list.moves[actual],previous,full,x);
                for(int k=0;k<MM_FEATURES;++k)printf("%s%.9g",k?",":"",x[k]);
                printf("],\"best_features\":[");
                if(best>=0){move_features(&p,list.moves[best],previous,full,x);for(int k=0;k<MM_FEATURES;++k)printf("%s%.9g",k?",":"",x[k]);}
                printf("]}\n");
            }
        }
        previous=list.moves[actual];p=next;++ply;
    }
    return ferror(stdin)||ferror(stdout)?5:0;
}
