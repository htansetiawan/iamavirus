/* OFFLINE ORACLE MINER. Input is a completed replay's true ancestor. This is
 * not an arena bot, belief updater or runtime observation-only generator.
 * All alternative histories share the actual prefix until the varied move. */
#include "fow.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int parse_move(const Position *p,const char *uci,Move *out) {
    MoveList list;generate_moves(p,&list);
    for(int i=0;i<list.count;++i){char s[6];move_to_uci(list.moves[i],s);if(!strcmp(s,uci)){*out=list.moves[i];return 1;}}
    return 0;
}
static int continued(const Position *p) {
    return king_square(p,WHITE)>=0 && king_square(p,BLACK)>=0 && !mover_left_king_capturable(p);
}
static int same_view(const Position *a,const Position *b,int side) {
    char x[65],y[65];observation(a,side,x);observation(b,side,y);return !memcmp(x,y,64);
}
static void print_position(const Position *p) {
    char board[65];pos_to_board_string(p,board);
    printf("{\"board\":\"%s\",\"side\":%d,\"castle\":\"%016" PRIx64 "\",\"ep\":%d,\"halfmove\":%d}",
           board,p->side,p->castle_rooks,p->ep,p->halfmove);
}
static int reply_safe(Position *p,Move move) {
    const int enemy=p->side^1;Undo u;make_move(p,move,&u);
    const int safe=king_square(p,enemy)<0 || !mover_left_king_capturable(p);
    unmake_move(p,move,&u);return safe;
}

int main(void) {
    fow_init();
    char board[65],a_text[6],b_text[6];int side,ep,halfmove;uint64_t castle;
    long context=0;
    while(scanf("%64s%d%" SCNx64 "%d%d%5s%5s",board,&side,&castle,&ep,&halfmove,a_text,b_text)==7) {
        Position before;
        if((side!=0&&side!=1)||strlen(board)!=64||pos_from_board_string(&before,board,side,castle,ep))return 2;
        before.halfmove=halfmove;
        Move a,b;Undo u;
        if(!parse_move(&before,a_text,&a))return 3;
        Position after_a=before;make_move(&after_a,a,&u);if(!continued(&after_a))return 4;
        if(!parse_move(&after_a,b_text,&b))return 5;
        Position actual=after_a;make_move(&actual,b,&u);if(!continued(&actual))return 6;
        const int us=side,them=side^1;
        MoveList previous,current;generate_moves(&before,&previous);generate_moves(&actual,&current);
        int aliases=0,distinct=0,common=0,hidden_danger=0,witnesses=0;
        for(int i=0;i<previous.count;++i) {
            const Move alternative=previous.moves[i];if(alternative==a)continue;
            Position q=before;make_move(&q,alternative,&u);
            if(!continued(&q)||!same_view(&q,&after_a,them))continue;
            char move_text[6];move_to_uci(b,move_text);Move checked;
            if(!parse_move(&q,move_text,&checked)||checked!=b)continue;
            make_move(&q,b,&u);
            if(!continued(&q)||!same_view(&q,&actual,them))continue;
            ++aliases;
            char qb[65],pb[65];pos_to_board_string(&q,qb);pos_to_board_string(&actual,pb);
            if(!memcmp(qb,pb,64))continue;
            ++distinct;
            for(int j=0;j<current.count;++j) {
                const Move c=current.moves[j];
                if(actual.piece[MOVE_FROM(c)]!=q.piece[MOVE_FROM(c)])continue;
                char c_text[6];move_to_uci(c,c_text);Move qc;
                if(!parse_move(&q,c_text,&qc)||qc!=c)continue;
                Position p1=actual,q1=q;
                make_move(&p1,c,&u);make_move(&q1,c,&u);
                if(!continued(&p1)||!continued(&q1)||!same_view(&p1,&q1,them))continue;
                ++common;
                const int kp=king_square(&p1,them),kq=king_square(&q1,them);
                const int danger_p=is_attacked(&p1,kp,us),danger_q=is_attacked(&q1,kq,us);
                if(danger_p==danger_q)continue;
                ++hidden_danger;
                MoveList rp,rq;generate_moves(&p1,&rp);generate_moves(&q1,&rq);
                /* Both states must offer the opponent exactly the same action
                 * row; differing action order/EP semantics are excluded. */
                if(rp.count!=rq.count||memcmp(rp.moves,rq.moves,(size_t)rp.count*sizeof(Move)))continue;
                int different=0,intersection=0,np=0,nq=0;
                int safe_p[256],safe_q[256];
                for(int z=0;z<rp.count;++z) {
                    safe_p[z]=reply_safe(&p1,rp.moves[z]);safe_q[z]=reply_safe(&q1,rq.moves[z]);
                    different+=safe_p[z]!=safe_q[z];intersection+=safe_p[z]&&safe_q[z];np+=safe_p[z];nq+=safe_q[z];
                }
                if(!different)continue;
                ++witnesses;
                char alt_text[6],view[65];move_to_uci(alternative,alt_text);observation(&p1,them,view);
                printf("{\"kind\":\"witness\",\"context\":%ld,\"actual_previous\":\"%s\",\"alternative_previous\":\"%s\","
                       "\"same_opponent_move\":\"%s\",\"common_current_move\":\"%s\",\"shared_opponent_view\":\"%s\","
                       "\"actual_danger\":%d,\"alternative_danger\":%d,\"safe_counts\":[%d,%d],\"safe_intersection\":%d,"
                       "\"reach_weights\":null,\"ancestor\":",context,a_text,alt_text,b_text,c_text,view,danger_p,danger_q,np,nq,intersection);
                print_position(&before);printf(",\"actual_root\":");print_position(&actual);
                printf(",\"alternative_root\":");print_position(&q);printf(",\"replies\":[");
                for(int z=0;z<rp.count;++z){char s[6];move_to_uci(rp.moves[z],s);
                    printf("%s{\"uci\":\"%s\",\"actual_safe\":%d,\"alternative_safe\":%d}",z?",":"",s,safe_p[z],safe_q[z]);}
                printf("]}\n");
            }
        }
        printf("{\"kind\":\"summary\",\"context\":%ld,\"private_history_aliases\":%d,\"distinct_placements\":%d,"
               "\"common_action_aliases\":%d,\"different_royal_danger\":%d,\"witnesses\":%d}\n",
               context,aliases,distinct,common,hidden_danger,witnesses);
        ++context;
    }
    return (ferror(stdin)||fflush(stdout)||ferror(stdout))?7:0;
}
