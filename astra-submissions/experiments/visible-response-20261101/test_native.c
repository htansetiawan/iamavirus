#include "response.h"
#include <assert.h>
#include <math.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    assert(argc==3);
    float *w=astra_response_load(argv[1]);assert(w);
    assert(!astra_response_load(argv[2]));
    uint8_t tokens[64]={0};uint16_t moves[256];double p[256];
    for(int i=0;i<256;++i)moves[i]=(uint16_t)(i%64|((i/4)%64)<<6|(i%5)<<12);
    assert(astra_response_probs(w,tokens,moves,256,p));double sum=0;
    for(int i=0;i<256;++i){assert(isfinite(p[i])&&p[i]>=0);sum+=p[i];}
    assert(fabs(sum-1)<1e-12);
    assert(astra_response_probs(w,tokens,moves,1,p)&&p[0]==1);
    assert(!astra_response_probs(w,tokens,moves,0,p));
    assert(!astra_response_probs(w,tokens,moves,257,p));
    tokens[1]=14;assert(!astra_response_probs(w,tokens,moves,256,p));tokens[1]=0;
    moves[0]=(uint16_t)(5<<12);assert(!astra_response_probs(w,tokens,moves,256,p));
    moves[0]=0;tokens[0]=6;assert(!astra_response_probs(w,tokens,moves,256,p));
    free(w);return 0;
}
