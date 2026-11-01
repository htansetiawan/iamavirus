#include "response.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

float *astra_response_load(const char *path) {
    const uint32_t endian = 1;
    if (sizeof(float) != 4 || *(const unsigned char *)&endian != 1) return NULL;
    FILE *f = fopen(path, "rb"); if (!f) return NULL;
    char magic[8]; uint32_t version, n;
    if (fread(magic,1,8,f)!=8 || memcmp(magic,"ASTRARP1",8) ||
        fread(&version,4,1,f)!=1 || version!=1 || fread(&n,4,1,f)!=1 || n!=ASTRA_RESPONSE_FLOATS) {
        fclose(f); return NULL;
    }
    float *w=malloc((size_t)n*sizeof(float));
    if (!w || fread(w,sizeof(float),n,f)!=n || fgetc(f)!=EOF) {free(w);fclose(f);return NULL;}
    fclose(f);
    for (uint32_t i=0;i<n;++i) if (!isfinite(w[i])) {free(w);return NULL;}
    return w;
}

int astra_response_logits(const float *w, const uint8_t tokens[64],
                          const uint16_t *moves, int count, float *out) {
    if (!w || count<1 || count>256) return 0;
    for (int s=0;s<64;++s) if (tokens[s]>13) return 0;
    for (int a=0;a<count;++a) if ((moves[a]>>12)>4 || tokens[moves[a]&63]>5) return 0;
    const float *w1=w, *b1=w+57344, *w2=w+57408, *b2=w+61504;
    const float *wa=w+61568, *ba=w+68288, *wo=w+68352, bo=w[68416];
    float h1[64],h2[64],base[64];
    /* One-hot input: gather 64 active columns rather than multiply 896. */
    for (int i=0;i<64;++i) {
        float v=b1[i]; for (int s=0;s<64;++s) v+=w1[i*896+s*14+tokens[s]];
        h1[i]=v>0?v:0;
    }
    for (int i=0;i<64;++i) {
        float v=b2[i]; for (int j=0;j<64;++j) v+=w2[i*64+j]*h1[j];
        h2[i]=v>0?v:0;
    }
    /* Board contribution is shared by every candidate, not recomputed. */
    for (int i=0;i<64;++i) {
        float v=ba[i]; for (int j=0;j<64;++j) v+=wa[i*105+j]*h2[j];
        base[i]=v;
    }
    for (int a=0;a<count;++a) {
        int fr=moves[a]&63,to=(moves[a]>>6)&63,pr=moves[a]>>12;
        int fx=fr%8,fy=fr/8,tx=to%8,ty=to/8,dx=tx-fx,dy=ty-fy;
        float geom[8]={fx/7.0f,fy/7.0f,tx/7.0f,ty/7.0f,dx/7.0f,dy/7.0f,
                        (abs(dx)>abs(dy)?abs(dx):abs(dy))/7.0f,
                        (fabsf(tx-3.5f)+fabsf(ty-3.5f))/7.0f};
        float value=bo;
        for (int i=0;i<64;++i) {
            const float *p=wa+i*105;
            float v=base[i]+p[64+tokens[fr]]+p[78+tokens[to]];
            for (int j=0;j<8;++j) v+=p[92+j]*geom[j];
            v+=p[100+pr]; if (v>0) value+=wo[i]*v;
        }
        out[a]=value;
    }
    return 1;
}

int astra_response_probs(const float *w, const uint8_t tokens[64],
                         const uint16_t *moves, int count, double *out) {
    float logits[256]; if (!astra_response_logits(w,tokens,moves,count,logits)) return 0;
    float max=logits[0];for (int a=1;a<count;++a) if (logits[a]>max) max=logits[a];
    double total=0;
    for (int a=0;a<count;++a) {out[a]=exp((double)logits[a]-max);total+=out[a];}
    if (!isfinite(total) || total<=0) return 0;
    for (int a=0;a<count;++a) out[a]/=total;
    return 1;
}
