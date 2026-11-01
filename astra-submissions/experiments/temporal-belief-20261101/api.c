/* The update API accepts ONLY our observations and own moves. Truth probes
 * are separate, const operations used after the update by the audit harness. */
#include "native/belief.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

static Move parse_move(const char *u) {
    if(!u || strlen(u)<4 || strlen(u)>5)return 0;
    for(int i=0;i<4;++i)if((i%2==0 && (u[i]<'a'||u[i]>'h')) || (i%2==1 && (u[i]<'1'||u[i]>'8')))return 0;
    int promo=NO_PIECE;
    if(u[4]){const char *s=strchr("nbrq",u[4]);if(!s)return 0;promo=(int)(s-"nbrq")+KNIGHT;}
    return MAKE_MOVE((u[1]-'1')*8+u[0]-'a',(u[3]-'1')*8+u[2]-'a',promo);
}
void *tb_create(int us,size_t cap,uint64_t seed) {
    fow_init();zobrist_init();Belief *b=malloc(sizeof(*b));if(!b)return NULL;
    belief_init_start(b,us,cap);b->rng=seed;return b;
}
void tb_free(void *handle){Belief *b=handle;belief_free(b);free(b);}
size_t tb_step(void *handle,const char *own_move,const char *view) {
    Belief *b=handle;if(!b->count)return 0;
    if(own_move && own_move[0])return belief_after_own(b,parse_move(own_move),view);
    return belief_after_opponent(b,view);
}
static uint64_t checksum_mix(uint64_t s,uint64_t value) {
    uint64_t z=s^(value+0x9e3779b97f4a7c15ULL);
    z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;
    z=(z^(z>>27))*0x94d049bb133111ebULL;
    return z^(z>>31);
}
uint64_t tb_checksum(const void *handle) {
    const Belief *b=handle;uint64_t s=checksum_mix(b->rng,((uint64_t)b->last_own<<32)|(unsigned)b->us);
    s=checksum_mix(s,b->cap);s=checksum_mix(s,(unsigned)b->overflowed);
    for(size_t i=0;i<b->count;++i){uint32_t bits;memcpy(&bits,&b->logw[i],sizeof(bits));
        s=checksum_mix(s,position_key(&b->items[i]));s=checksum_mix(s,b->hist[i]);
        s=checksum_mix(s,((uint64_t)bits<<32)|b->recent[i]);}
    return checksum_mix(s,b->count);
}

/* [count, unique placements-with-rights, truth share, truth+context share,
 * known-context share, entropy over full board states, ESS over entries,
 * has-ever-hit-cap, matching truth entries, matching truth+context entries].
 * Presence is counted separately from mass to distinguish underflow.
 * Read-only; truth data is never passed to an update. */
void tb_probe(const void *handle,const char *truth,int side,uint64_t castle,int ep,uint32_t context,double out[10]) {
    const Belief *b=handle;memset(out,0,10*sizeof(double));out[0]=(double)b->count;out[7]=b->overflowed;
    if(!b->count)return;
    uint64_t target=0;Position truepos;
    if(truth && pos_from_board_string(&truepos,truth,side,castle,ep)==0)target=position_key(&truepos);
    size_t capacity=16;while(capacity<2*b->count)capacity*=2;
    uint64_t *keys=calloc(capacity,sizeof(*keys));double *mass=calloc(capacity,sizeof(*mass));
    double total=0,square=0;
    for(size_t i=0;i<b->count;++i){
        uint64_t key=position_key(&b->items[i]);double w=exp((double)b->logw[i]);total+=w;square+=w*w;
        if(key==target){out[2]+=w;out[8]+=1;if(b->recent[i]==context){out[3]+=w;out[9]+=1;}}
        if(b->recent[i]&(1U<<23))out[4]+=w;
        size_t j=(key*0x9e3779b97f4a7c15ULL)&(capacity-1);
        while(keys[j] && keys[j]!=key)j=(j+1)&(capacity-1);
        if(!keys[j]){keys[j]=key;out[1]+=1;}mass[j]+=w;
    }
    if(total>0){out[2]/=total;out[3]/=total;out[4]/=total;out[6]=total*total/square;
        for(size_t i=0;i<capacity;++i)if(mass[i]>0){double q=mass[i]/total;out[5]-=q*log(q);}}
    free(keys);free(mass);
}
double tb_king_risk(const void *handle,const char *own_move) {
    const Belief *b=handle;if(!b->count)return NAN;Move m=parse_move(own_move);double total=0,loss=0;
    for(size_t i=0;i<b->count;++i){
        Position p=b->items[i];double w=exp((double)b->logw[i]);total+=w;
        MoveList legal;generate_moves(&p,&legal);int found=0;
        for(int j=0;j<legal.count;++j)if(legal.moves[j]==m){found=1;break;}
        if(!found){loss+=w;continue;}
        Undo u;make_move(&p,m,&u);
        if(king_square(&p,b->us^1)>=0 && mover_left_king_capturable(&p))loss+=w;
    }
    return total>0?loss/total:NAN;
}
