#define _POSIX_C_SOURCE 200809L
#include "gtcfr.h"
#include "sfeval.h"
#include "front.h"
Move astra_front_effective(const Belief *,const Front *,const char *,const MoveList *,Move);
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int cached_gtcfr_decide(const Belief *,const GtcfrParams *,SearchResult *);
int last_gtcfr_decide(const Belief *,const GtcfrParams *,SearchResult *);
int astra_sf_restarts(void);
static double seconds(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
static uint64_t bytes(uint64_t h,const void *v,size_t size){const unsigned char *p=v;for(size_t i=0;i<size;++i){h^=p[i];h*=1099511628211ULL;}return h;}
static uint64_t fingerprint(const Belief *b){
 uint64_t h=bytes(1469598103934665603ULL,b->items,b->count*sizeof(*b->items));
 if(b->logw)h=bytes(h,b->logw,b->count*sizeof(*b->logw));
 if(b->hist)h=bytes(h,b->hist,b->count*sizeof(*b->hist));
 h=bytes(h,&b->rng,sizeof(b->rng));h=bytes(h,&b->count,sizeof(b->count));
 h=bytes(h,&b->last_own,sizeof(b->last_own));return bytes(h,&b->us,sizeof(b->us));
}
int astra_three_way(const Belief *b,const GtcfrParams *parameters,const Front *front,const char *view,const MoveList *allowed,SearchResult *out){
 static const int orders[6][3]={{0,1,2},{0,2,1},{1,0,2},{1,2,0},{2,0,1},{2,1,0}};
 const int blocks=getenv("ASTRA_COST_BLOCKS")?atoi(getenv("ASTRA_COST_BLOCKS")):6;
 const int rotate=getenv("ASTRA_COST_ROTATE")?atoi(getenv("ASTRA_COST_ROTATE")):0;
 const char *sf=getenv("MIST_STOCKFISH");
 if(blocks<1||blocks>6)exit(7);
 const uint64_t initial=fingerprint(b);
 const GtcfrParams p=*parameters;
 const uint64_t mask=bytes(1469598103934665603ULL,p.avoid,(size_t)p.avoid_count*sizeof(Move));
 int saved=0;
 for(int block=0;block<blocks;++block){
  for(int step=0;step<3;++step){
   const int arm=orders[(block+rotate)%6][step];SearchResult result;
   if(sf&&*sf){sf_stop();if(!sf_start(sf)||sf_workers()!=2){fputs("astra cost: Stockfish startup failed\n",stderr);exit(3);}}
   long before_calls,after_calls;double before_sf,after_sf;sf_stats(&before_calls,&before_sf);
   const double started=seconds();
   const int ok=arm==0?gtcfr_decide(b,&p,&result):arm==1?cached_gtcfr_decide(b,&p,&result):last_gtcfr_decide(b,&p,&result);
   const double elapsed=seconds()-started;
   sf_stats(&after_calls,&after_sf);
   const uint64_t after=fingerprint(b);
   const int restarts=sf&&*sf?astra_sf_restarts():0;
   if(!ok||after!=initial||restarts||(sf&&*sf&&!sf_ready())){fputs("astra cost: invalid result, mutated belief or Stockfish failure\n",stderr);exit(4);}
   char move[6],raw[6];move_to_uci(result.move,raw);result.move=astra_front_effective(b,front,view,allowed,result.move);move_to_uci(result.move,move);
   fprintf(stderr,"astra-three {\"block\":%d,\"step\":%d,\"arm\":%d,\"move\":\"%s\",\"raw_move\":\"%s\",\"value\":%.17g,\"probability\":%.17g,\"nodes\":%d,\"iterations\":%d,\"samples\":%d,\"our_moves\":%d,\"infosets\":%d,\"seconds\":%.9f,\"budget\":%.17g,\"seed\":%llu,\"population\":%zu,\"belief\":\"%016llx\",\"mask\":\"%016llx\",\"avoid_count\":%d,\"sf_calls\":%ld,\"sf_seconds\":%.9f,\"sf_restarts\":%d}\n",block,step,arm,move,raw,result.value,result.probability,result.nodes,result.iterations,result.samples,result.our_moves,result.opponent_infosets,elapsed,p.seconds,p.seed,b->count,(unsigned long long)initial,(unsigned long long)mask,p.avoid_count,after_calls-before_calls,after_sf-before_sf,restarts);
   if(arm==0&&!saved){*out=result;saved=1;}
  }
 }
 if(sf&&*sf)sf_stop();return saved;
}
