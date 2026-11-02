#include "belief.c"
#include <assert.h>
#include "guard_reference.h"
void db_init(int table,int threads) {fow_init();zobrist_init();read_settings();threads_setting=threads;if(!table){free(hist_table);hist_table=NULL;hist_n=0;}}
void *db_new(int us,size_t cap) {Belief *b=malloc(sizeof(*b));belief_init_start(b,us,cap);return b;}
void db_free(void *ptr) {belief_free(ptr);free(ptr);}
size_t db_step(void *ptr,Move move,int own,const char *view) {return own?belief_after_own(ptr,move,view):belief_after_opponent(ptr,view);}
size_t db_count(const Belief *b) {return b->count;}
int db_overflowed(const Belief *b) {return b->overflowed;}
void db_export(const Belief *b,uint64_t *keys,uint64_t *hist,float *sharp,float *flat,int *half,char *boards) {
 for(size_t i=0;i<b->count;++i) {
  keys[i]=position_key(&b->items[i]);hist[i]=b->hist[i];sharp[i]=b->logw[i];half[i]=b->items[i].halfmove;
  pos_to_board_string(&b->items[i],boards+65*i);
#if DUAL
  flat[i]=b->logw1[i];
#else
  flat[i]=b->logw[i]/model_temp;
#endif
 }
}
/* Diagnostic only: exact scan over all retained boards, no stride. */
int db_risks(const Belief *b,const char *view,Move *moves,double *flat,double *sharp,double *qflat,double *qsharp) {
 MoveList l;view_moves(view,b->us,b->items[0].castle_rooks,&l);
 for(int j=0;j<l.count;++j) {
  moves[j]=l.moves[j];king_risks(b,l.moves[j],20000,model_temp,&flat[j],&sharp[j]);
  queen_risks(b,l.moves[j],20000,model_temp,4,&qflat[j],&qsharp[j]);
 }
 return l.count;
}
uint64_t db_key(const char *board,int side,uint64_t castle,int ep) {Position p;assert(!pos_from_board_string(&p,board,side,castle,ep));return position_key(&p);}
