/* Offline true-parent features, exactly the input representation of the
 * existing belief prior. This is not an observation-only opponent policy. */
#include "../deployed-prior-comparison-20261102/prior.c"
#include "quiet.h"

int quiet_features(uint16_t moves[256],float x[256*26],float full[256],float cheap[256],
                   unsigned counts[256],unsigned *total,uint8_t surprise[256]) {
    MoveList l;generate_moves(&current,&l);char victim[65];observation(&current,current.side^1,victim);
    move_logits(&current,&l,previous,1,full);move_logits(&current,&l,previous,0,cheap);
    *total=history_counts(histories[current.side],&l,counts);
    for(int j=0;j<l.count;++j){float f[MM_FEATURES];move_features(&current,l.moves[j],previous,1,f);
        moves[j]=l.moves[j];memcpy(x+26*j,f,26*sizeof(float));
        surprise[j]=f[MM_CAPTURE]>0 && victim[MOVE_FROM(l.moves[j])]=='?';}
    return l.count;
}
void quiet_logp(const float *x,const float *base,int n,int F,const float *lin,const float *q,float *out) {
    astra_quiet_logp(x,base,n,F,lin,q,out);
}
