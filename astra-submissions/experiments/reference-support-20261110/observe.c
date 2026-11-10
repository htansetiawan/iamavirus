/* Read-only support receipt. Does not construct a range or change any policy. */
#include "observe.h"
#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static struct {
    int valid,best;
    uint64_t history;
    MoveList row,legal;
    double probability[256];
} reference;

int astra_reference_warm(int decision) {
    const char *v=getenv("ASTRA_REFERENCE_DECISION");
    return v && decision==atoi(v);
}
void astra_reference_legal(const MoveList *legal) { reference.legal=*legal; }
void astra_reference_capture(const Belief *b,const MoveList *moves,const double *x,int best) {
    if(!b->ancestry || moves->count<=0 || moves->count>256 || best<0 || best>=moves->count)exit(81);
    double total=0;
    for(int i=0;i<moves->count;++i){if(!isfinite(x[i]) || x[i]<0)exit(82);total+=x[i];}
    if(fabs(total-1)>1e-9)exit(83);
    reference.row=*moves;reference.best=best;reference.history=b->ancestry->own_now;
    memcpy(reference.probability,x,(size_t)moves->count*sizeof(double));reference.valid=1;
    fprintf(stderr,"astra-reference: {\"kind\":\"policy\",\"own_history\":\"%016" PRIx64 "\",\"rows\":[",reference.history);
    for(int i=0;i<moves->count;++i){char u[6];move_to_uci(moves->moves[i],u);
        fprintf(stderr,"%s{\"move\":\"%s\",\"reference\":%.17g,\"pure_search_play\":%d}",i?",":"",u,x[i],i==best);}
    fprintf(stderr,"],\"legal\":[");
    for(int i=0;i<reference.legal.count;++i){char u[6];move_to_uci(reference.legal.moves[i],u);fprintf(stderr,"%s\"%s\"",i?",":"",u);}
    fprintf(stderr,"]}\n");
}
static double prior(Move move,int *guarded,int *outside) {
    *guarded=*outside=0;
    for(int i=0;i<reference.row.count;++i)if(reference.row.moves[i]==move)return reference.probability[i];
    for(int i=0;i<reference.legal.count;++i)if(reference.legal.moves[i]==move){*guarded=1;return 0;}
    *outside=1;return 0;
}
static void position(const Position *p) {
    char board[65];pos_to_board_string(p,board);
    fprintf(stderr,"{\"board\":\"%s\",\"side\":%d,\"castle\":\"%016" PRIx64 "\",\"ep\":%d,\"halfmove\":%d}",
            board,p->side,p->castle_rooks,p->ep,p->halfmove);
}
typedef struct {size_t count,positive,guarded,outside;double mass;} Tally;
static void alias(const AstraAlternative *a,void *arg) {
    Tally *t=arg;int guarded,outside;double p=prior(a->alternative_own,&guarded,&outside);
    char move[6];move_to_uci(a->alternative_own,move);
    fprintf(stderr,"%s{\"move\":\"%s\",\"reference\":%.17g,\"guarded\":%d,\"outside\":%d,\"own_history\":\"%016" PRIx64 "\",\"opponent_history\":\"%016" PRIx64 "\",\"current\":",
            t->count?",":"",move,p,guarded,outside,a->own_history,a->opponent_history);
    position(&a->current);fprintf(stderr,"}");
    ++t->count;t->positive+=p>1e-6;t->guarded+=guarded;t->outside+=outside;t->mass+=p;
}
void astra_reference_dump(const Belief *b,int decision) {
    const char *v=getenv("ASTRA_REFERENCE_DECISION");if(!v || decision!=atoi(v)+1)return;
    if(!reference.valid || !b->ancestry)exit(84);
    size_t n=b->count<32?b->count:32,valid=0;
    for(size_t k=0;k<n;++k){size_t i=n==1?0:k*(b->count-1)/(n-1);AstraContext c;
        if(!astra_ancestry_context(b,i,&c))continue;
        if(c.own_before!=reference.history)exit(85);
        int guarded,outside;double actual=prior(c.own,&guarded,&outside);char own[6],reply[6];
        move_to_uci(c.own,own);move_to_uci(c.opponent,reply);
        fprintf(stderr,"astra-reference: {\"kind\":\"context\",\"index\":%zu,\"parent\":%u,\"own\":\"%s\",\"hypothesized_reply\":\"%s\",\"own_before\":\"%016" PRIx64 "\",\"own_now\":\"%016" PRIx64 "\",\"opponent_before\":\"%016" PRIx64 "\",\"opponent_now\":\"%016" PRIx64 "\",\"actual_reference\":%.17g,\"actual_guarded\":%d,\"actual_outside\":%d,\"ancestor\":",
                i,c.parent,own,reply,c.own_before,c.own_now,c.opponent_before,c.opponent_now,actual,guarded,outside);
        position(&c.ancestor);fprintf(stderr,",\"current\":");position(&c.current);fprintf(stderr,",\"alternatives\":[");
        Tally t={0};astra_ancestry_alternatives(b,i,alias,&t,256);
        fprintf(stderr,"],\"count\":%zu,\"positive\":%zu,\"guarded\":%zu,\"outside\":%zu,\"mass\":%.17g}\n",t.count,t.positive,t.guarded,t.outside,t.mass);
        ++valid;
    }
    fprintf(stderr,"astra-reference: {\"kind\":\"coverage\",\"native_worlds\":%zu,\"sampled\":%zu,\"valid\":%zu,\"recovered\":%d}\n",
            b->count,n,valid,!b->ancestry->natural);
}
