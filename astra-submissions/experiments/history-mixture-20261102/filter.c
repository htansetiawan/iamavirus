/* Bounded history-preserving filter. Includes immutable v37 helpers only. */
#include "belief.c"
#include <assert.h>
#include <limits.h>

typedef struct { uint64_t history; float logw; } HMass;
typedef struct { Position p; uint32_t begin,end; float logw; } HBoard;
typedef struct {
 HBoard *boards; HMass *mass; size_t n,nh;
 int us,mixture; Move last_own; size_t peak_candidates;
 unsigned long lookups,hits;
} HFilter;
typedef struct { uint64_t key,history; uint32_t parent; Move move; int half; float logw; } HCandidate;

static void *halloc(size_t n,size_t width) {
 if(width && n>SIZE_MAX/width) abort();
 void *p=calloc(n?n:1,width);if(!p)abort();return p;
}
static int hcmp(const void *a,const void *b) {
 const HCandidate *x=a,*y=b;
 if(x->key!=y->key)return x->key<y->key?-1:1;
 if(x->half!=y->half)return x->half<y->half?-1:1;
 if(x->history!=y->history)return x->history<y->history?-1:1;
 return 0;
}
static int same_board(const HCandidate *a,const HCandidate *b) {return a->key==b->key && a->half==b->half;}
static void hfree(HFilter *b) {free(b->boards);free(b->mass);memset(b,0,sizeof(*b));}
static void hinit(HFilter *b,int us,int mixture) {
 memset(b,0,sizeof(*b));b->us=us;b->mixture=mixture;b->n=b->nh=1;
 b->boards=halloc(1,sizeof(HBoard));b->mass=halloc(1,sizeof(HMass));
 pos_start(&b->boards[0].p);b->boards[0].end=1;
 char view[65];observation(&b->boards[0].p,us^1,view);
 b->mass[0].history=history_mix(0,view_hash(view));
}

/* Rebuild boards once per state, retain their contiguous history mass rows. */
static size_t hcommit(HFilter *b,HCandidate *r,size_t n) {
 if(n>b->peak_candidates)b->peak_candidates=n;
 if(n>1)qsort(r,n,sizeof(*r),hcmp);
 size_t m=0;
 for(size_t i=0;i<n;) {
  size_t j=i+1;HCandidate best=r[i];float total=r[i].logw;
  while(j<n && same_board(&r[i],&r[j]) && r[i].history==r[j].history) {
   total=log_add(total,r[j].logw);if(r[j].logw>best.logw)best=r[j];++j;
  }
  best.logw=total;r[m++]=best;i=j;
 }
 size_t groups=0,nh=0;float top=-INFINITY;
 for(size_t i=0;i<m;) {
  size_t j=i+1;float total=r[i].logw;
  while(j<m && same_board(&r[i],&r[j]))total=log_add(total,r[j++].logw);
  if(total>top)top=total;++groups;nh+=b->mixture?j-i:1;i=j;
 }
 HBoard *boards=halloc(groups,sizeof(*boards));HMass *mass=halloc(nh,sizeof(*mass));
 size_t bi=0,hi=0;
 for(size_t i=0;i<m;) {
  size_t j=i+1,rep=i;float total=r[i].logw;
  while(j<m && same_board(&r[i],&r[j])) {total=log_add(total,r[j].logw);if(r[j].logw>r[rep].logw)rep=j;++j;}
  HBoard *w=&boards[bi++];w->p=b->boards[r[rep].parent].p;Undo u;make_move(&w->p,r[rep].move,&u);
  assert(w->p.halfmove==r[rep].half);w->begin=(uint32_t)hi;w->logw=total-top;
  if(b->mixture)for(size_t k=i;k<j;++k)mass[hi++]=(HMass){r[k].history,r[k].logw-top};
  else mass[hi++]=(HMass){r[rep].history,total-top};
  w->end=(uint32_t)hi;i=j;
 }
 free(b->boards);free(b->mass);free(r);b->boards=boards;b->mass=mass;b->n=groups;b->nh=nh;return groups;
}
static int hpush(HCandidate **r,size_t *n,size_t *cap,HCandidate c) {
 if(*n>=1000000)return 0;
 if(*n==*cap) {size_t next=*cap?*cap*2:1024;void *p=realloc(*r,next*sizeof(**r));if(!p)abort();*r=p;*cap=next;}
 (*r)[(*n)++]=c;return 1;
}

/* Return SIZE_MAX on generation bound, leaving the original belief intact. */
static size_t hstep(HFilter *b,Move own,int is_own,const char *view) {
 HCandidate *rows=NULL;size_t n=0,cap=0;char seen[65],theirs[65];
 read_settings();
 for(size_t i=0;i<b->n;++i) {
  const HBoard *parent=&b->boards[i];MoveList legal;generate_moves(&parent->p,&legal);
  float logits[256]={0},logz=0;
  if(!is_own && model_on) {
   move_logits(&parent->p,&legal,b->last_own,b->n<=model_full_below,logits);
   float top=-INFINITY;for(int j=0;j<legal.count;++j)if(logits[j]>top)top=logits[j];
   double z=0;for(int j=0;j<legal.count;++j)z+=exp((double)(logits[j]-top));
   logz=top+(float)log(z);
  }
  uint64_t keys[256],observations[256];int half[256],valid[256]={0};
  for(int j=0;j<legal.count;++j) {
   if(is_own && legal.moves[j]!=own)continue;
   Position p=parent->p;Undo u;make_move(&p,legal.moves[j],&u);
   if(prune_capturable && mover_left_king_capturable(&p))continue;
   observation(&p,b->us,seen);if(memcmp(seen,view,64))continue;
   observation(&p,b->us^1,theirs);valid[j]=1;keys[j]=position_key(&p);half[j]=p.halfmove;observations[j]=view_hash(theirs);
  }
  for(size_t k=parent->begin;k<parent->end;++k) {
   const HMass *h=&b->mass[k];unsigned counts[256]={0},N=0;
   if(!is_own && model_on && hist_table) {++b->lookups;N=history_counts(h->history,&legal,counts);if(N<hist_min)N=0;else ++b->hits;}
   for(int j=0;j<legal.count;++j)if(valid[j]) {
    float lw=h->logw;
    if(!is_own && model_on)lw+=N?model_temp*logf(((float)counts[j]+hist_n0*expf(logits[j]-logz))/((float)N+hist_n0)):model_temp*(logits[j]-logz);
    uint64_t hist=is_own?h->history:history_mix(h->history,legal.moves[j]);
    hist=history_mix(hist,observations[j]);
    HCandidate c={keys[j],hist,(uint32_t)i,legal.moves[j],half[j],lw};
    if(!hpush(&rows,&n,&cap,c)) {free(rows);return SIZE_MAX;}
   }
  }
 }
 if(is_own)b->last_own=own;
 return hcommit(b,rows,n);
}

void hm_load(void) {fow_init();zobrist_init();read_settings();}
void *hm_new(int us,int mixture) {HFilter *b=halloc(1,sizeof(*b));hinit(b,us,mixture);return b;}
void hm_free(void *ptr) {HFilter *b=ptr;hfree(b);free(b);}
size_t hm_step(void *ptr,unsigned short move,int own,const char *view) {return hstep(ptr,move,own,view);}
void hm_stats(const void *ptr,double out[8]) {
 const HFilter *b=ptr;double total=0,discarded=0;size_t largest=0;
 for(size_t i=0;i<b->n;++i) {
  const HBoard *w=&b->boards[i];double mass=0,best=0;
  for(size_t j=w->begin;j<w->end;++j) {double v=exp(b->mass[j].logw);mass+=v;if(v>best)best=v;}
  total+=mass;discarded+=mass-best;if(w->end-w->begin>largest)largest=w->end-w->begin;
 }
 out[0]=b->n;out[1]=b->nh;out[2]=largest;out[3]=total>0?discarded/total:0;
 out[4]=b->n*sizeof(HBoard)+b->nh*sizeof(HMass);out[5]=b->peak_candidates;out[6]=b->lookups;out[7]=b->hits;
}
double hm_probe(const void *ptr,const char *text,int side,uint64_t castle,int ep,int half,int full) {
 const HFilter *b=ptr;Position p;if(pos_from_board_string(&p,text,side,castle,ep))return -1;
 uint64_t key=position_key(&p);double total=0,hit=0;
 for(size_t i=0;i<b->n;++i) {double w=exp(b->boards[i].logw);total+=w;if(position_key(&b->boards[i].p)==key && (!full || b->boards[i].p.halfmove==half))hit+=w;}
 return total>0?hit/total:0;
}
size_t hm_export(const void *ptr,uint64_t *keys,int *half,uint64_t *hist,double *mass,size_t capacity) {
 const HFilter *b=ptr;if(capacity<b->nh)return b->nh;size_t at=0;
 for(size_t i=0;i<b->n;++i)for(size_t j=b->boards[i].begin;j<b->boards[i].end;++j) {
  keys[at]=position_key(&b->boards[i].p);half[at]=b->boards[i].p.halfmove;hist[at]=b->mass[j].history;mass[at]=exp(b->mass[j].logw);++at;
 }
 return at;
}
