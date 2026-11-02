/* Independent transition enumeration in ordinary double-probability space. */
#include "belief.c"
#include <assert.h>
typedef struct {uint64_t key;double w;} Row;
static int cmp(const void *a,const void *b){uint64_t x=((const Row*)a)->key,y=((const Row*)b)->key;return (x>y)-(x<y);}
static Row *enumerate(const Belief *b,const double *prior,int own,Move move,const char *view,size_t *nr) {
 size_t cap=1024,n=0;Row *r=malloc(cap*sizeof(*r));char seen[65];
 for(size_t i=0;i<b->count;++i) {
  MoveList l;generate_moves(&b->items[i],&l);float logits[256];
  move_logits(&b->items[i],&l,b->last_own,b->count<=model_full_below,logits);
  double top=-INFINITY;for(int j=0;j<l.count;++j)if(logits[j]>top)top=logits[j];
  double z=0;for(int j=0;j<l.count;++j)z+=exp(logits[j]-top);
  unsigned counts[256]={0},N=hist_table?history_counts(b->hist[i],&l,counts):0;if(N<hist_min)N=0;
  for(int j=0;j<l.count;++j) {
   if(own&&l.moves[j]!=move)continue;
   Position p=b->items[i];Undo u;make_move(&p,l.moves[j],&u);
   if(prune_capturable&&mover_left_king_capturable(&p))continue;
   observation(&p,b->us,seen);if(memcmp(seen,view,64))continue;
   double likelihood=exp(logits[j]-top)/z;
   if(N)likelihood=(counts[j]+hist_n0*likelihood)/(N+hist_n0);
   if(n==cap){cap*=2;r=realloc(r,cap*sizeof(*r));assert(r);}
   r[n++]=(Row){position_key(&p),prior[i]*(own||!model_on?1:likelihood)};
  }
 }
 qsort(r,n,sizeof(*r),cmp);size_t m=0;
 for(size_t i=0;i<n;){size_t j=i+1;double w=r[i].w;while(j<n&&r[j].key==r[i].key)w+=r[j++].w;r[m++]=(Row){r[i].key,w};i=j;}
 *nr=m;return r;
}
static double maximum_error=0;static int comparisons=0,merges=0;
static double *verify(const Belief *b,Row *expected,size_t n) {
 double *next=malloc((b->count?b->count:1)*sizeof(*next)),total=0,actual=0;
 for(size_t i=0;i<b->count;++i){Row needle={position_key(&b->items[i]),0};Row *r=bsearch(&needle,expected,n,sizeof(*expected),cmp);assert(r);next[i]=r->w;total+=r->w;actual+=exp(b->logw1[i]);}
 for(size_t i=0;i<b->count;++i){next[i]/=total;double error=fabs(next[i]-exp(b->logw1[i])/actual);if(error>maximum_error)maximum_error=error;assert(error<3e-6);}
 ++comparisons;return next;
}
int main(void) {
 fow_init();zobrist_init();read_settings();threads_setting=1;model_full_below=10000;
 /* Powering and summing commute for one path, but not for merged paths. */
 assert(fabs(sqrt(.3*.3)-.3)<1e-12);
 assert(fabs(sqrt(.3*.3+.4*.4)-(.3+.4))>.19);
 HistRec records[2]={{77,0,20},{99,0,13}};
 for(int us=0;us<2;++us)for(int table=0;table<2;++table)for(int temp=1;temp<=2;++temp)for(int capped=0;capped<2;++capped) {
  model_temp=temp;hist_table=table?records:NULL;hist_n=table?2:0;
  int flip=us?56:0;Belief b;belief_init_start(&b,us,capped?19:200000);
  Position truth;pos_clear(&truth);pos_put(&truth,0^flip,us,KING);pos_put(&truth,1^flip,us,ROOK);
  pos_put(&truth,63^flip,us^1,KING);pos_put(&truth,61^flip,us^1,KNIGHT);pos_put(&truth,62^flip,us^1,KNIGHT);truth.side=us^1;
  b.items[0]=truth;b.hist[0]=77;double *prior=malloc(sizeof(double));prior[0]=1;
  records[0].move=MAKE_MOVE(62^flip,45^flip,NO_PIECE);records[1].move=MAKE_MOVE(63^flip,55^flip,NO_PIECE);
  const int seq[6][2]={{62,45},{0,8},{61,44},{8,0},{45,62},{0,8}};
  for(int t=0;t<6;++t){
   Move move=MAKE_MOVE(seq[t][0]^flip,seq[t][1]^flip,NO_PIECE);int own=truth.side==us;
   Undo u;make_move(&truth,move,&u);char view[65];observation(&truth,us,view);
   size_t n;Row *expected=enumerate(&b,prior,own,move,view,&n);
   if(own)belief_after_own(&b,move,view);else belief_after_opponent(&b,view);
   free(prior);prior=verify(&b,expected,n);free(expected);
   if(temp==1)for(size_t i=0;i<b.count;++i)assert(fabs(b.logw[i]-b.logw1[i])<1e-5);
   if(temp==2)for(size_t i=0;i<b.count;++i)if(fabs(b.logw[i]/2-b.logw1[i])>.01)merges++;
  }
  if(capped)assert(b.overflowed);
  /* In-place thinning retains precisely the second weight for that board. */
  if(b.count>5){size_t n=b.count;Row *old=malloc(n*sizeof(*old));for(size_t i=0;i<n;++i)old[i]=(Row){position_key(&b.items[i]),b.logw1[i]};qsort(old,n,sizeof(*old),cmp);belief_shrink(&b,5);for(size_t i=0;i<5;++i){Row needle={position_key(&b.items[i]),0};Row *r=bsearch(&needle,old,n,sizeof(*old),cmp);assert(r&&r->w==b.logw1[i]);}free(old);}
  free(prior);belief_free(&b);
 }
 assert(merges>0);hist_table=NULL;hist_n=0;
 /* Threaded merge with unequal incoming likelihoods, deliberately repeated
  * boards. This exercises both workers without needing a large chess trace. */
 threads_setting=2;model_temp=2;
 Belief b;belief_init_start(&b,WHITE,200000);Position start=b.items[0];
 b.count=b.capacity=5000;b.items=realloc(b.items,5000*sizeof(Position));b.hist=realloc(b.hist,5000*sizeof(uint64_t));b.logw=realloc(b.logw,5000*sizeof(float));b.logw1=realloc(b.logw1,5000*sizeof(float));
 double *prior=malloc(5000*sizeof(double));
 for(int i=0;i<5000;++i){b.items[i]=start;b.items[i].side=BLACK;b.hist[i]=i;b.logw1[i]=(float)(-i*.001);b.logw[i]=2*b.logw1[i];prior[i]=exp(b.logw1[i]);}
 Position after=b.items[0];Undo u;make_move(&after,MAKE_MOVE(52,36,NO_PIECE),&u);char view[65];observation(&after,WHITE,view);
 size_t n;Row *expected=enumerate(&b,prior,0,0,view,&n);belief_after_opponent(&b,view);free(prior);prior=verify(&b,expected,n);free(prior);free(expected);belief_free(&b);
 /* Threaded own update, no normalization ambiguity: each entry kept. */
 belief_init_start(&b,WHITE,200000);b.count=b.capacity=5000;b.items=realloc(b.items,5000*sizeof(Position));b.hist=realloc(b.hist,5000*sizeof(uint64_t));b.logw=realloc(b.logw,5000*sizeof(float));b.logw1=realloc(b.logw1,5000*sizeof(float));
 for(int i=0;i<5000;++i){b.items[i]=start;b.hist[i]=i;b.logw1[i]=(float)(-i*.001);b.logw[i]=2*b.logw1[i];}
 after=start;Move m=MAKE_MOVE(12,28,NO_PIECE);make_move(&after,m,&u);observation(&after,WHITE,view);assert(belief_after_own(&b,m,view)==5000);
 for(int i=0;i<5000;++i)assert(fabs(b.logw1[i]-(float)(-i*.001))<1e-7);belief_free(&b);
 /* Rebuild initializes the two measures identically; empty update frees both. */
 belief_init_start(&b,WHITE,200000);observation(&start,WHITE,view);int counts[6]={8,2,2,2,1,1};
 assert(belief_resample(&b,view,counts,start.castle_rooks,20,10000)>0);
 for(size_t i=0;i<b.count;++i)assert(b.logw1[i]==0&&b.logw[i]==0);
 memset(view,'-',64);view[64]=0;assert(belief_after_opponent(&b,view)==0);belief_free(&b);
 printf("{\"passed\":true,\"oracle_comparisons\":%d,\"max_error\":%.17g,\"merge_disagreements\":%d,\"threaded\":true,\"shrink_rebuild_empty\":true}\n",comparisons,maximum_error,merges);
 return 0;
}
