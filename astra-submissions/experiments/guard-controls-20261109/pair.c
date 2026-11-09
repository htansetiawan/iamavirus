#define _POSIX_C_SOURCE 200809L
#include "gtcfr.h"
#include "sfeval.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static uint64_t fingerprint(const Belief *b) {
    uint64_t h=1469598103934665603ULL;
    const unsigned char *p=(const unsigned char *)b->items;
    for(size_t i=0;i<b->count*sizeof(*b->items);++i){h^=p[i];h*=1099511628211ULL;}
    if(b->logw){p=(const unsigned char *)b->logw;for(size_t i=0;i<b->count*sizeof(*b->logw);++i){h^=p[i];h*=1099511628211ULL;}}
    return h;
}
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+1e-9*t.tv_nsec;}

/* One immutable belief; same sampling seed and fresh SF processes for both.
 * The baseline alone supplies the emitted protocol move. No truth is read.
 */
int astra_guard_pair(const Belief *b,const GtcfrParams *params,SearchResult *out,
                     const Move *alternative,int alternative_count) {
    if(!getenv("ASTRA_GUARD_PAIR"))return gtcfr_decide(b,params,out);
    const int first=atoi(getenv("ASTRA_GUARD_PAIR"))!=0;
    const int same=getenv("ASTRA_PAIR_SAME")!=NULL;
    const uint64_t before=fingerprint(b);
    const char *sf=getenv("MIST_STOCKFISH");
    const char *budget=getenv("ASTRA_PAIR_SECONDS");
    int base_ok=0;
    for(int step=0;step<2;++step){
        int arm=step==0?first:!first;GtcfrParams p=*params;SearchResult answer;
        p.seconds=budget?atof(budget):2.5;
        if(arm&&!same){p.avoid=alternative;p.avoid_count=alternative_count;}
        if(sf){sf_stop();if(!sf_start(sf)){fprintf(stderr,"pair: SF startup failed\n");exit(3);}}
        double started=now();int ok=gtcfr_decide(b,&p,&answer);
        uint64_t after=fingerprint(b);
        fprintf(stderr,"astra: pair arm=%d ok=%d elapsed=%.9f belief=%llu unchanged=%d\n",
                arm,ok,now()-started,(unsigned long long)before,before==after);
        if(before!=after)exit(4);
        if(!arm){*out=answer;base_ok=ok;}
    }
    if(sf)sf_stop();return base_ok;
}
