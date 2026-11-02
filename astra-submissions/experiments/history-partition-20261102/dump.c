/* Exact-prefix input only. Reuses the corrected, pinned experiment-250 filter. */
#include "../history-mixture-20261102/filter.c"

int main(void) {
 hm_load();int side,plies;assert(scanf("%d%d",&side,&plies)==2);
 assert((side==0||side==1)&&plies>=0&&plies<=64);
 HFilter rep,mix;hinit(&rep,side,0);hinit(&mix,side,1);char view[65],start[65];
 assert(scanf("%64s",view)==1);observation(&rep.boards[0].p,side,start);assert(!strcmp(start,view));
 for(int p=1;p<=plies;++p) {
  int own;unsigned move;assert(scanf("%d%u%64s",&own,&move,view)==3);
  assert(own==((p-1)%2==side));
  assert(hstep(&rep,(Move)move,own,view)!=SIZE_MAX);assert(hstep(&mix,(Move)move,own,view)!=SIZE_MAX);
  assert(rep.n<=4096&&mix.n<=4096&&mix.nh<=131072);
 }
 assert(rep.n==mix.n);printf("{\"states\":[");
 for(size_t i=0;i<mix.n;++i) {
  HBoard *a=&rep.boards[i],*b=&mix.boards[i];
  assert(position_key(&a->p)==position_key(&b->p)&&a->p.halfmove==b->p.halfmove);
  char text[65];pos_to_board_string(&b->p,text);
  printf("%s{\"key\":\"%llu\",\"half\":%d,\"board\":\"%s\",\"castle\":\"%llu\",\"ep\":%d,\"rep_history\":\"%llu\",\"rep_mass\":%.17g,\"histories\":[",
    i?",":"",(unsigned long long)position_key(&b->p),b->p.halfmove,text,(unsigned long long)b->p.castle_rooks,b->p.ep,
    (unsigned long long)rep.mass[a->begin].history,exp(rep.mass[a->begin].logw));
  for(size_t h=b->begin;h<b->end;++h)printf("%s[\"%llu\",%.17g]",h>b->begin?",":"",(unsigned long long)mix.mass[h].history,exp(mix.mass[h].logw));
  printf("]}");
 }
 printf("]}\n");hfree(&rep);hfree(&mix);return 0;
}
