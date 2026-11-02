/* Independent flat-history enumeration; never groups before transitions. */
#include "filter.c"

typedef struct {Position p;uint64_t hist;double weight;} Oracle;
typedef struct {uint64_t key,hist;int half;double weight;} Expected;
static int ec(const void *a,const void *b) {
 const Expected *x=a,*y=b;
 if(x->hist!=y->hist)return x->hist<y->hist?-1:1;
 if(x->key!=y->key)return x->key<y->key?-1:1;
 return (x->half>y->half)-(x->half<y->half);
}
static void compare(const HFilter *b,Oracle *o,size_t n) {
 Expected *expected=halloc(n,sizeof(*expected)),*actual=halloc(b->nh,sizeof(*actual));
 double sum=0,total=0;size_t at=0;
 for(size_t i=0;i<n;++i){expected[i]=(Expected){position_key(&o[i].p),o[i].hist,o[i].p.halfmove,o[i].weight};sum+=o[i].weight;}
 qsort(expected,n,sizeof(*expected),ec);
 size_t count=0;
 for(size_t i=0;i<n;) {size_t j=i+1;double w=expected[i].weight;while(j<n&&!ec(&expected[i],&expected[j]))w+=expected[j++].weight;expected[count]=expected[i];expected[count++].weight=w/sum;i=j;}
 assert(count==b->nh);
 for(size_t i=0;i<b->n;++i)for(size_t j=b->boards[i].begin;j<b->boards[i].end;++j){double w=exp(b->mass[j].logw);actual[at++]=(Expected){position_key(&b->boards[i].p),b->mass[j].history,b->boards[i].p.halfmove,w};total+=w;}
 qsort(actual,at,sizeof(*actual),ec);
 for(size_t i=0;i<count;++i){assert(!ec(&actual[i],&expected[i]));assert(fabs(actual[i].weight/total-expected[i].weight)<2e-6);}
 free(expected);free(actual);
}
static size_t oracle_step(Oracle **o,size_t n,int us,int own,Move played,const char *view) {
 Oracle *next=halloc(100000,sizeof(*next));size_t nn=0;
 for(size_t i=0;i<n;++i) {
  MoveList legal;generate_moves(&(*o)[i].p,&legal);float logits[256];
  move_logits(&(*o)[i].p,&legal,own?0:played,1,logits);
  float top=-INFINITY;for(int j=0;j<legal.count;++j)if(logits[j]>top)top=logits[j];
  double z=0;for(int j=0;j<legal.count;++j)z+=exp((double)(logits[j]-top));
  float logz=top+(float)log(z);unsigned counts[256]={0},N=hist_table?history_counts((*o)[i].hist,&legal,counts):0;if(N<hist_min)N=0;
  for(int j=0;j<legal.count;++j) {
   if(own&&legal.moves[j]!=played)continue;
   Position p=(*o)[i].p;Undo u;char seen[65],theirs[65];make_move(&p,legal.moves[j],&u);
   if(mover_left_king_capturable(&p))continue;
   observation(&p,us,seen);if(memcmp(seen,view,64))continue;
   observation(&p,us^1,theirs);uint64_t h=(*o)[i].hist;
   if(!own)h=history_mix(h,legal.moves[j]);h=history_mix(h,view_hash(theirs));
   double w=(*o)[i].weight;
   if(!own)w*=exp(N?model_temp*logf(((float)counts[j]+hist_n0*expf(logits[j]-logz))/((float)N+hist_n0)):model_temp*(logits[j]-logz));
   assert(nn<100000);next[nn++]=(Oracle){p,h,w};
  }
 }
 free(*o);*o=next;return nn;
}
static void board_marginal_parity(const HFilter *a,const HFilter *b) {
 assert(a->n==b->n);double ta=0,tb=0;
 for(size_t i=0;i<a->n;++i){ta+=exp(a->boards[i].logw);tb+=exp(b->boards[i].logw);}
 for(size_t i=0;i<a->n;++i){assert(position_key(&a->boards[i].p)==position_key(&b->boards[i].p));assert(a->boards[i].p.halfmove==b->boards[i].p.halfmove);assert(fabs(exp(a->boards[i].logw)/ta-exp(b->boards[i].logw)/tb)<2e-6);}
}
int main(void) {
 hm_load();threads_setting=1;hist_n0=4;hist_min=3;size_t comparisons=0;int divergent=0;
 HistRec synthetic[2]={{77,0,20},{99,0,20}};
 for(int us=0;us<2;++us)for(int table=0;table<2;++table)for(int temp=1;temp<=2;++temp) {
  model_temp=(float)temp;model_on=1;hist_table=table?synthetic:NULL;hist_n=table?2:0;
  int flip=us?56:0;Position truth;pos_clear(&truth);
  pos_put(&truth,0^flip,us,KING);pos_put(&truth,1^flip,us,ROOK);
  pos_put(&truth,63^flip,us^1,KING);pos_put(&truth,61^flip,us^1,KNIGHT);pos_put(&truth,62^flip,us^1,KNIGHT);truth.side=us^1;
  HFilter b,representative;hinit(&b,us,1);b.boards[0].p=truth;b.boards[0].end=2;b.nh=2;free(b.mass);b.mass=halloc(2,sizeof(HMass));
  b.mass[0]=(HMass){77,logf(.3f)};b.mass[1]=(HMass){99,logf(.7f)};
  hinit(&representative,us,0);representative.boards[0].p=truth;representative.mass[0].history=99;
  Oracle *o=halloc(2,sizeof(*o));o[0]=(Oracle){truth,77,.3};o[1]=(Oracle){truth,99,.7};size_t n=2;
  synthetic[0].move=MAKE_MOVE(62^flip,45^flip,NO_PIECE);synthetic[1].move=MAKE_MOVE(63^flip,55^flip,NO_PIECE);
  const int sequence[6][2]={{62,45},{0,8},{61,44},{8,0},{45,62},{0,8}};Move last_own=0;
  for(int turn=0;turn<6;++turn) {
   Move move=MAKE_MOVE(sequence[turn][0]^flip,sequence[turn][1]^flip,NO_PIECE);int own=truth.side==us;
   Undo undo;make_move(&truth,move,&undo);char view[65];observation(&truth,us,view);
   size_t result=hstep(&b,move,own,view);assert(result!=SIZE_MAX);
   hstep(&representative,move,own,view);
   n=oracle_step(&o,n,us,own,own?move:last_own,view);if(own)last_own=move;
   compare(&b,o,n);++comparisons;
   if(!table)board_marginal_parity(&b,&representative);
   else if(b.n==representative.n)for(size_t i=0;i<b.n;++i)if(fabs(b.boards[i].logw-representative.boards[i].logw)>.01)divergent=1;
  }
  assert(b.nh>b.n);free(o);hfree(&b);hfree(&representative);
 }
 assert(divergent);
 /* Continuation itself proves that our last move did not lose our king.
  * Compare this deduction directly with immutable v37, both colours. */
 for(int us=0;us<2;++us) {
  int flip=us?56:0;Position p;pos_clear(&p);
  pos_put(&p,0^flip,us,KING);pos_put(&p,1^flip,us,ROOK);
  pos_put(&p,56^flip,us^1,ROOK);pos_put(&p,63^flip,us^1,KING);p.side=us;
  Move m=MAKE_MOVE(1^flip,9^flip,NO_PIECE);Position after=p;Undo u;make_move(&after,m,&u);
  assert(mover_left_king_capturable(&after));char view[65];observation(&after,us,view);
  HFilter own;hinit(&own,us,1);own.boards[0].p=p;
  Belief legacy;belief_init_start(&legacy,us,100);legacy.items[0]=p;
  assert(hstep(&own,m,1,view)==0);assert(belief_after_own(&legacy,m,view)==0);
  hfree(&own);belief_free(&legacy);
 }
 hist_table=NULL;hist_n=0;
 HFilter b;hinit(&b,0,1);char impossible[65];memset(impossible,'-',64);impossible[64]=0;
 assert(hstep(&b,MAKE_MOVE(12,28,NO_PIECE),1,impossible)==0);assert(b.n==0&&b.nh==0);hfree(&b);
 printf("PASS %zu independent weighted-history comparisons; both colours; temperature1/2; empirical histories alter predictions; no-table board parity; empty update. Board=%zu history=%zu candidate=%zu\n",comparisons,sizeof(HBoard),sizeof(HMass),sizeof(HCandidate));
 return 0;
}
