/* Input: color, cap, seed; then own UCI + our view, opponent our view,
 * or a fixed shrink instruction. It has no true-board/hidden-move reader. */
#include "belief.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <time.h>
#ifdef PAIR
void base_zobrist_init(void);
void base_belief_init_start(Belief *,int,size_t);
void base_belief_free(Belief *);
size_t base_belief_after_own(Belief *,Move,const char *);
size_t base_belief_after_opponent(Belief *,const char *);
size_t base_belief_shrink(Belief *,size_t);
static int same(const Belief *a,const Belief *b) {
    if(a->count!=b->count || a->capacity!=b->capacity || a->cap!=b->cap ||
       a->rng!=b->rng || a->us!=b->us || a->last_own!=b->last_own ||
       a->overflowed!=b->overflowed || a->set_size!=b->set_size || a->set_count!=b->set_count)return 0;
    if(memcmp(a->hist,b->hist,a->count*sizeof(uint64_t)) ||
       memcmp(a->logw,b->logw,a->count*sizeof(float)) ||
       memcmp(a->set,b->set,a->set_size*sizeof(uint64_t)))return 0;
    for(size_t i=0;i<a->count;++i){const Position *p=&a->items[i],*q=&b->items[i];
        if(memcmp(p->by_color,q->by_color,sizeof p->by_color) ||
           memcmp(p->by_type,q->by_type,sizeof p->by_type) ||
           memcmp(p->piece,q->piece,sizeof p->piece) || memcmp(p->color,q->color,sizeof p->color) ||
           p->side!=q->side || p->castle_rooks!=q->castle_rooks || p->ep!=q->ep || p->halfmove!=q->halfmove)return 0;
    }
    return 1;
}
#endif

static double cpu(void) {
    struct timespec t; clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &t);
    return t.tv_sec + 1e-9 * t.tv_nsec;
}
static uint64_t mix(uint64_t h, uint64_t x) {
    for (int k = 0; k < 8; ++k) { h ^= (x >> (8*k)) & 255; h *= UINT64_C(1099511628211); }
    return h;
}
static uint64_t digest(const Belief *b) {
    uint64_t h = UINT64_C(1469598103934665603);
    for (size_t i = 0; i < b->count; ++i) {
        const Position *p = &b->items[i];
        for (int c = 0; c < 2; ++c) h = mix(h, p->by_color[c]);
        for (int t = 0; t < 6; ++t) h = mix(h, p->by_type[t]);
        for (int s = 0; s < 64; ++s) h = mix(mix(h, (uint8_t)p->piece[s]), (uint8_t)p->color[s]);
        h = mix(mix(mix(mix(h, p->side), p->castle_rooks), (uint32_t)p->ep), p->halfmove);
        h = mix(h, b->hist ? b->hist[i] : 0);
        uint32_t bits = 0; if (b->logw) memcpy(&bits, &b->logw[i], sizeof bits);
        h = mix(h, bits);
    }
    return h;
}
static void position(const Position *p) {
    char board[65]; pos_to_board_string(p, board);
    printf("{\"board\":\"%s\",\"side\":%d,\"castle\":\"%016" PRIx64 "\",\"ep\":%d,\"halfmove\":%d}",
           board,p->side,p->castle_rooks,p->ep,p->halfmove);
}
static Move uci(const char *s) {
    int promotion = NO_PIECE;
    if (s[4]) {
        static const char letters[] = "nbrq";
        const char *found = strchr(letters, s[4]);
        if (!found) exit(31);
        promotion = KNIGHT + (int)(found - letters);
    }
    if (strlen(s) < 4 || s[0] < 'a' || s[0] > 'h' || s[2] < 'a' || s[2] > 'h' ||
        s[1] < '1' || s[1] > '8' || s[3] < '1' || s[3] > '8') exit(32);
    return MAKE_MOVE(s[0]-'a'+8*(s[1]-'1'),s[2]-'a'+8*(s[3]-'1'),promotion);
}
#ifdef TRACK
static void alternative(const AstraAlternative *a, void *unused) {
    (void)unused; char move[6]; move_to_uci(a->alternative_own, move);
    printf("{\"move\":\"%s\",\"own_history\":\"%016" PRIx64 "\",\"opponent_history\":\"%016" PRIx64 "\",\"reach_known\":%d,\"current\":",
           move,a->own_history,a->opponent_history,a->reach_known);
    position(&a->current); printf("},");
}
static void dump(const Belief *b, size_t n) {
    size_t valid=0, selected=0;
    for (size_t i=0; i<b->count; ++i) {
        AstraContext c; valid += astra_ancestry_context(b,i,&c);
    }
    n = n < b->count ? n : b->count;
    for (size_t k=0; k<n; ++k) {
        size_t i=n==1 ? 0 : k*(b->count-1)/(n-1);
        AstraContext c; if (!astra_ancestry_context(b,i,&c)) continue;
        char a[6],r[6];move_to_uci(c.own,a);move_to_uci(c.opponent,r);
        printf("{\"kind\":\"context\",\"index\":%zu,\"parent\":%u,\"own\":\"%s\",\"hypothesized_reply\":\"%s\","
               "\"opponent_before\":\"%016" PRIx64 "\",\"opponent_now\":\"%016" PRIx64 "\","
               "\"own_before\":\"%016" PRIx64 "\",\"own_now\":\"%016" PRIx64 "\",\"ancestor_logw\":%.9g,\"current_logw\":%.9g,\"ancestor\":",
               i,c.parent,a,r,c.opponent_before,c.opponent_now,c.own_before,c.own_now,c.ancestor_logw,c.current_logw);
        position(&c.ancestor);printf(",\"current\":");position(&c.current);
        printf(",\"alternatives\":[");
        size_t alternatives=astra_ancestry_alternatives(b,i,alternative,NULL,256);
        printf("null],\"alternatives_count\":%zu}\n",alternatives);
        ++selected;
    }
    printf("{\"kind\":\"coverage\",\"count\":%zu,\"valid\":%zu,\"selected\":%zu,\"payload_bytes\":%zu}\n",
           b->count,valid,selected,astra_ancestry_payload(b));
}
#endif
int main(void) {
    fow_init();zobrist_init();
    int side;size_t cap;uint64_t seed;
    if (scanf("%d%zu%" SCNu64,&side,&cap,&seed)!=3 || side<0 || side>1 || !cap)return 2;
    Belief b;belief_init_start(&b,side,cap);b.rng=seed;
#ifdef PAIR
    base_zobrist_init();Belief original;base_belief_init_start(&original,side,cap);original.rng=seed;
#endif
#ifdef TRACK
    if (!astra_ancestry_enable(&b))return 3;
#endif
    char op,view[65],move[6];size_t seq=0;double total=0;
    while(scanf(" %c",&op)==1) {
        double start=cpu();
        if (op=='o') {
            if(scanf("%5s%64s",move,view)!=2 || strlen(view)!=64)return 4;
            belief_after_own(&b,uci(move),view);
#ifdef PAIR
            base_belief_after_own(&original,uci(move),view);
#endif
        } else if (op=='p') {
            if(scanf("%64s",view)!=1 || strlen(view)!=64)return 5;
            belief_after_opponent(&b,view);
#ifdef PAIR
            base_belief_after_opponent(&original,view);
#endif
        } else if(op=='s') {
            size_t target;if(scanf("%zu",&target)!=1)return 6;belief_shrink(&b,target);
#ifdef PAIR
            base_belief_shrink(&original,target);
#endif
        } else if(op=='d') {
            size_t n;if(scanf("%zu",&n)!=1)return 7;
#ifdef TRACK
            uint64_t before=digest(&b), rng=b.rng;double generation_start=cpu();
            dump(&b,n);
            double generation_cpu=cpu()-generation_start;
            if(before!=digest(&b) || rng!=b.rng)return 11;
            printf("{\"kind\":\"generator_cost\",\"cpu_seconds\":%.9g}\n",generation_cpu);
#endif
            continue;
        } else return 8;
        total+=cpu()-start;
#ifdef PAIR
        if(!same(&b,&original))return 12;
        printf("{\"kind\":\"exact_parity\",\"seq\":%zu,\"worlds\":%zu}\n",seq,b.count);
#endif
        printf("{\"kind\":\"state\",\"seq\":%zu,\"op\":\"%c\",\"count\":%zu,\"capacity\":%zu,\"rng\":\"%016" PRIx64 "\",\"overflow\":%d,\"last_own\":%u,\"digest\":\"%016" PRIx64 "\"}\n",
               seq++,op,b.count,b.capacity,b.rng,b.overflowed,b.last_own,digest(&b));
        if(!b.count) {belief_free(&b);return 9;}
    }
    struct rusage usage;getrusage(RUSAGE_SELF,&usage);
    printf("{\"kind\":\"cost\",\"update_cpu\":%.9g,\"maxrss_kib\":%ld}\n",total,usage.ru_maxrss);
#ifdef PAIR
    base_belief_free(&original);
#endif
    belief_free(&b);return ferror(stdin)||fflush(stdout)||ferror(stdout)?10:0;
}
