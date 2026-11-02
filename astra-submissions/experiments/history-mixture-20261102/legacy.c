#include "belief.c"
#include <assert.h>
void lg_load(void){fow_init();zobrist_init();read_settings();}
void *lg_new(int us){Belief *b=malloc(sizeof(*b));belief_init_start(b,us,200000);return b;}
void lg_free(void *ptr){belief_free(ptr);free(ptr);}
size_t lg_step(void *ptr,unsigned short move,int own,const char *view){return own?belief_after_own(ptr,move,view):belief_after_opponent(ptr,view);}
size_t lg_count(const void *ptr){return ((const Belief*)ptr)->count;}
int lg_capped(const void *ptr){return ((const Belief*)ptr)->overflowed;}
void lg_export(const void *ptr,uint64_t *keys,int *half,double *mass){
 const Belief *b=ptr;for(size_t i=0;i<b->count;++i){keys[i]=position_key(&b->items[i]);half[i]=b->items[i].halfmove;mass[i]=exp(b->logw[i]);}
}
uint64_t lg_truth_key(const char *text,int side,uint64_t castle,int ep){
 Position p;assert(!pos_from_board_string(&p,text,side,castle,ep));return position_key(&p);
}
