/* Native FP32 query-attention value. Fixed stack buffers, no heap allocation.
 * Input: 64 * 5 uint8 categorical features in experiment237 canonical order.
 * Both kings must occur exactly once in a nonterminal hypothesis. Caller
 * handles terminal states using the rules; this predictor is not a referee.
 */
#include <math.h>
#include <stddef.h>
#include <stdint.h>

static float bounded_residual(float a, float b, float z) {
    float s=fmaxf(-1.0f,fminf(1.0f,z/4.0f));
    return z+2.0f*tanhf((a+b*s)/2.0f);
}


enum { D=32, Q=4, H=2, HD=16, F=64, TABLE=(64*13+64*4+64+64)*D };

static void linear(const float *x, const float *w, const float *b,
                   float *y, int input, int output) {
    for (int j=0;j<output;j++) {
        float v=b[j];
        for (int i=0;i<input;i++) v += x[i]*w[j*input+i];
        y[j]=v;
    }
}

static void norm(const float *x, const float *w, const float *b, float *y) {
    float mean=0, var=0;
    for (int i=0;i<D;i++) mean += x[i];
    mean /= D;
    for (int i=0;i<D;i++) { float a=x[i]-mean; var += a*a; }
    float inv=1.0f/sqrtf(var/D+1e-5f);
    for (int i=0;i<D;i++) y[i]=(x[i]-mean)*inv*w[i]+b[i];
}

static void embeddings(const float *w, const uint8_t *x, const float *bias,
                       float z[64][D]) {
    const float *vision=w+64*13*D, *castle=vision+64*4*D, *ep=castle+64*D;
    for (int s=0;s<64;s++) {
        const uint8_t *a=x+s*5;
        const float *p=w+(13*s+a[0])*D, *v=vision+(4*s+a[1]+2*a[2])*D;
        for (int j=0;j<D;j++)
            z[s][j]=p[j]+v[j]+a[3]*castle[s*D+j]+a[4]*ep[s*D+j]+(bias?bias[j]:0);
    }
}

size_t fow_residual_query_floats(void) {
    return 3*TABLE+2*D+Q*D+D+2*(4*D+2*(D*D+D)+(D*F+F)+(F*D+D))+2*D+(Q+1)*D*F+F+2*F+2;
}

float fow_residual_query_logit(const float *w, const uint8_t *x, uint8_t half, float base_z) {
    float token[64][D], keys[64][D], values[64][D], z[Q][D];
    embeddings(w,x,NULL,token); w+=TABLE;
    embeddings(w,x,w+TABLE,keys); w+=TABLE+D;
    embeddings(w,x,w+TABLE,values); w+=TABLE+D;
    const float *latent=w; w+=Q*D;
    const float *half_weight=w; w+=D;
    int kings[2]={-1,-1};
    for (int s=0;s<64;s++) {
        if (x[s*5]==6) kings[0]=s;
        if (x[s*5]==12) kings[1]=s;
    }
    if (kings[0]<0 || kings[1]<0) return NAN;
    for (int q=0;q<Q;q++) for (int j=0;j<D;j++)
        z[q][j]=latent[q*D+j]+(half/100.0f)*half_weight[j]+(q<2?token[kings[q]][j]:0);
    for (int round=0;round<2;round++) {
        const float *n1w=w;w+=D;const float *n1b=w;w+=D;
        const float *qw=w;w+=D*D;const float *qb=w;w+=D;
        const float *ow=w;w+=D*D;const float *ob=w;w+=D;
        const float *n2w=w;w+=D;const float *n2b=w;w+=D;
        const float *f1w=w;w+=D*F;const float *f1b=w;w+=F;
        const float *f2w=w;w+=F*D;const float *f2b=w;w+=D;
        for (int q=0;q<Q;q++) {
            float n[D], query[D], att[D], temp[D], hidden[F];
            norm(z[q],n1w,n1b,n); linear(n,qw,qb,query,D,D);
            for (int h=0;h<H;h++) {
                float score[64], best=-INFINITY, total=0;
                for (int s=0;s<64;s++) {
                    float v=0;
                    for (int j=0;j<HD;j++) v+=query[h*HD+j]*keys[s][h*HD+j];
                    score[s]=v/4.0f;
                    if (score[s]>best) best=score[s];
                }
                for (int s=0;s<64;s++) {score[s]=expf(score[s]-best);total+=score[s];}
                for (int j=0;j<HD;j++) {
                    float v=0;
                    for (int s=0;s<64;s++) v+=(score[s]/total)*values[s][h*HD+j];
                    att[h*HD+j]=v;
                }
            }
            linear(att,ow,ob,temp,D,D);
            for (int j=0;j<D;j++) z[q][j]+=temp[j];
            norm(z[q],n2w,n2b,n);linear(n,f1w,f1b,hidden,D,F);
            for (int j=0;j<F;j++) if (hidden[j]<0) hidden[j]=0;
            linear(hidden,f2w,f2b,temp,F,D);
            for (int j=0;j<D;j++) z[q][j]+=temp[j];
        }
    }
    const float *nw=w;w+=D;const float *nb=w;w+=D;
    float summary[(Q+1)*D], hidden[F], result[2];
    for (int q=0;q<Q;q++) norm(z[q],nw,nb,summary+q*D);
    for (int j=0;j<D;j++) {float v=0;for(int s=0;s<64;s++)v+=token[s][j];summary[Q*D+j]=v/8;}
    const float *hw=w;w+=(Q+1)*D*F;const float *hb=w;w+=F;
    linear(summary,hw,hb,hidden,(Q+1)*D,F);
    for(int j=0;j<F;j++)if(hidden[j]<0)hidden[j]=0;
    linear(hidden,w,w+2*F,result,F,2);return bounded_residual(result[0],result[1],base_z);
}


double fow_residual_query_batch(const float *w,const uint8_t *x,const uint8_t *h,
                              const float *z,int n,int repeats) {
    double sum=0;
    for(int r=0;r<repeats;r++)for(int i=0;i<n;i++)
        sum+=fow_residual_query_logit(w,x+320*i,h[i],z[i]);
    return sum;
}
