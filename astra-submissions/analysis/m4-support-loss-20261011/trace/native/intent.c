/* Experimental offline prior, not linked into the active arena engine.
 * Scalar ABI permits direct C/Python parity testing of frozen feature rows. */
#include "movemodel.h"
#include <math.h>
#include <stddef.h>

int m4_intent_scores(int n,const float *features,const float *base,const float *gate,float *out) {
    if(n<1||n>256)return 0;
    int kind[256],count[3]={0};double forward[3]={0},centre[3]={0};
    for(int a=0;a<n;++a) {
        const float *x=features+(size_t)a*MM_FEATURES;
        int g=x[MM_CHECK]>0?0:(x[MM_CAPTURE]>0||x[MM_PROMOTE_QUEEN]>0||x[MM_UNDERPROMOTE]>0)?1:2;
        kind[a]=g;++count[g];forward[g]+=x[MM_FORWARD];centre[g]+=x[MM_CENTRE];
        out[a]=0;for(int k=0;k<MM_FEATURES;++k)out[a]+=base[k]*x[k];
    }
    double correction[3]={0};
    for(int g=0;g<3;++g)if(count[g]) {
        double ln=log(count[g]);
        correction[g]=(g==0?gate[0]:0)+(g==1?gate[1]:0)+gate[2]*ln+
            (g==0?gate[3]*ln:0)+(g==1?gate[4]*ln:0)+
            gate[5]*forward[g]/count[g]+gate[6]*centre[g]/count[g];
    }
    for(int a=0;a<n;++a)out[a]+=(float)correction[kind[a]];
    return 1;
}

void m4_intent_logits(const Position *p,const MoveList *l,Move previous,
                      const float *base,const float *gate,float *out) {
    float x[256][MM_FEATURES];
    for(int a=0;a<l->count;++a)move_features(p,l->moves[a],previous,1,x[a]);
    m4_intent_scores(l->count,&x[0][0],base,gate,out);
}
