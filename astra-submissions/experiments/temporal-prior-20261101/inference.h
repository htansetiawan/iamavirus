#ifndef ASTRA_TEMPORAL_INFERENCE_H
#define ASTRA_TEMPORAL_INFERENCE_H
#include "temporal.h"
#include "learned.h"

/* At most seven nonzero temporal features: evaluate directly, without a
 * 52-column scan or allocation. Uses only the supplied hypothesis history. */
static float temporal_sparse_score(const float *theta,const TemporalHistory *h,const Position *p,Move m) {
    const RecentOwn *r=&h->side[p->side];
    if(!r->known)return 0;
    int type=p->piece[MOVE_FROM(m)];float z=theta[r->type*6+type];
    if(MOVE_FROM(m)!=MOVE_TO(r->move) || type!=r->type)return z;
    z+=theta[36+type];
    if(r->captured_value)z+=theta[42+type];
    if(MOVE_TO(m)==MOVE_FROM(r->move))z+=theta[48];
    if(r->continued)z+=theta[49];
    if(r->captured_value && temporal_capture_value(p,m)>0)z+=theta[50];
    z+=theta[51]*((float)r->captured_value/9.0f);
    return z;
}
static void temporal_logits(const TemporalHistory *h,const Position *p,const MoveList *moves,Move previous,int temporal,float *out) {
    const float *theta=temporal?learned_temporal:learned_static;
    bb_t vis=visible_squares(p,p->side);float x[MM_FEATURES];
    for(int i=0;i<moves->count;++i) {
        Move m=moves->moves[i];move_features_obs(p,m,previous,1,vis,x);
        float z=0;for(int j=0;j<MM_FEATURES;++j)z+=theta[j]*x[j];
        int type=p->piece[MOVE_FROM(m)];
        z+=theta[MM_FEATURES+TP_FEATURES+type*64+move_mirror_square(p->side,MOVE_FROM(m))];
        z+=theta[MM_FEATURES+TP_FEATURES+384+type*64+move_mirror_square(p->side,MOVE_TO(m))];
        if(temporal)z+=temporal_sparse_score(theta+MM_FEATURES,h,p,m);
        out[i]=z;
    }
}
#endif
