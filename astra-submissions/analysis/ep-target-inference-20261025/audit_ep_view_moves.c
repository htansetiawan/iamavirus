#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "src/belief.h"
static uint32_t rs=0x4f735f11U;
static uint32_t rnd(void){rs^=rs<<13;rs^=rs>>17;rs^=rs<<5;return rs;}
static int has(const MoveList*l,Move m){for(int i=0;i<l->count;i++)if(l->moves[i]==m)return 1;return 0;}
static void base_view_moves(const char view[65],int us,bb_t castle,MoveList*out){
  char board[65];for(int sq=0;sq<64;sq++)board[sq]=view[sq]=='?'?'-':view[sq];board[64]=0;
  Position p;out->count=0;if(pos_from_board_string(&p,board,us,castle,-1))return;
  MoveList all;generate_moves(&p,&all);
  for(int i=0;i<all.count;i++){Move m=all.moves[i];int from=MOVE_FROM(m),to=MOVE_TO(m);if(view[to]=='?')continue;
    int lo=from<to?from:to,hi=from<to?to:from,ok=1;
    if(p.piece[from]==PAWN&&hi-lo==16&&view[lo+8]=='?')ok=0;
    if(p.piece[from]==KING&&hi-lo==2){int home=us==WHITE?0:56;int a=to>from?home+5:home+1,z=to>from?home+6:home+3;for(int sq=a;sq<=z;sq++)if(view[sq]=='?')ok=0;}
    if(ok)out->moves[out->count++]=m;
  }
  int dr=us==WHITE?8:-8,fifth=us==WHITE?4:3;char enemy=us==WHITE?'p':'P';
  for(bb_t pawns=p.by_type[PAWN]&p.by_color[us];pawns;pawns&=pawns-1){int from=__builtin_ctzll(pawns),f=from%8;if(from/8!=fifth)continue;for(int df=-1;df<=1;df+=2){if(f+df<0||f+df>7)continue;int beside=from+df,to=beside+dr;if(view[beside]==enemy&&view[to]=='-'&&!is_attacked(&p,beside,us))out->moves[out->count++]=MAKE_MOVE(from,to,NO_PIECE);}}
}
int main(int argc,char**argv){unsigned long positions=0,ep_possible=0,base_omitted=0,patched_recovered=0,base_extra=0,patched_extra=0,ambiguous_obs=0,unique_obs=0,added=0;int games=argc>1?atoi(argv[1]):500;uint32_t seed=argc>2?(uint32_t)strtoul(argv[2],NULL,10):1332956945U;rs=seed;
  for(int g=0;g<games;g++){Position p;pos_start(&p);for(int ply=0;ply<240;ply++){
    char view[65];observation(&p,p.side,view);MoveList truth,base,patched;generate_moves(&p,&truth);base_view_moves(view,p.side,p.castle_rooks,&base);view_moves(view,p.side,p.castle_rooks,&patched);int nadd=patched.count-base.count;positions++;added+=nadd;
    for(int i=0;i<truth.count;i++){Move m=truth.moves[i];int from=MOVE_FROM(m),to=MOVE_TO(m);if(p.piece[from]==PAWN&&to==p.ep&&p.piece[to]==NO_PIECE){ep_possible++;if(!has(&base,m)){base_omitted++;if(has(&patched,m))patched_recovered++;}Position q=p;q.ep=-1;char alt[65];observation(&q,q.side,alt);if(!memcmp(view,alt,64))ambiguous_obs++;else unique_obs++;}}
    for(int i=0;i<base.count;i++)if(!has(&truth,base.moves[i]))base_extra++;
    for(int i=0;i<patched.count;i++)if(!has(&truth,patched.moves[i]))patched_extra++;
    if (!truth.count || king_square(&p, 0) < 0 || king_square(&p, 1) < 0) break;
    Move m = truth.moves[rnd() % truth.count];
    Undo u;
    make_move(&p, m, &u);
    if (king_square(&p, 0) < 0 || king_square(&p, 1) < 0) break;
  }}
  printf("{\"seed\":%u,\"games\":%d,\"positions\":%lu,\"legal_ep_actions\":%lu,\"base_omitted_ep\":%lu,\"patched_recovered_ep\":%lu,\"ep_current_observation_ambiguous_without_right\":%lu,\"ep_current_observation_distinguishable_without_right\":%lu,\"inferred_candidates_added\":%lu,\"base_illegal_candidates\":%lu,\"patched_illegal_candidates\":%lu}\n",seed,games,positions,ep_possible,base_omitted,patched_recovered,ambiguous_obs,unique_obs,added,base_extra,patched_extra);
  return patched_extra?1:0;
}
