#define _POSIX_C_SOURCE 200809L
#include "strata.h"
#include "gtcfr.h"
#include "sfeval.h"
#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static void fail(const char *message) { fprintf(stderr, "%s\n", message); exit(2); }
static double now(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)t.tv_sec+1e-9*t.tv_nsec;
}
static Move parse_move(const char *s) {
    if (strlen(s) < 4 || strlen(s) > 5 || s[0] < 'a' || s[0] > 'h' ||
        s[2] < 'a' || s[2] > 'h' || s[1] < '1' || s[1] > '8' || s[3] < '1' || s[3] > '8') fail("bad move");
    int promo = NO_PIECE;
    if (s[4]) {
        switch (s[4]) { case 'n': promo=KNIGHT; break; case 'b': promo=BISHOP; break;
            case 'r': promo=ROOK; break; case 'q': promo=QUEEN; break; default: fail("bad promotion"); }
    }
    return MAKE_MOVE(s[0]-'a'+8*(s[1]-'1'), s[2]-'a'+8*(s[3]-'1'), promo);
}
static void read_input(const char *path, Belief *b, MoveList *moves, Move *old_avoid, int *old_count, int *budget) {
    FILE *f = fopen(path, "r"); if (!f) fail("input open failed");
    memset(b, 0, sizeof(*b)); *old_count=0;
    if (fscanf(f, "%zu%d%d%d", &b->count, &b->us, budget, &moves->count) != 4 ||
        !b->count || b->count > 200000 || (b->us != 0 && b->us != 1) ||
        *budget < 1 || *budget > ASTRA_MAX_DRAWS || moves->count < 1 || moves->count > 256) fail("bad dimensions");
    for (int a = 0; a < moves->count; ++a) {
        char uci[6]; int kept;
        if (fscanf(f, "%5s%d", uci, &kept) != 2 || (kept != 0 && kept != 1)) fail("bad action");
        moves->moves[a] = parse_move(uci);
        for (int j = 0; j < a; ++j) if (moves->moves[j] == moves->moves[a]) fail("duplicate action");
        if (!kept) old_avoid[(*old_count)++] = moves->moves[a];
    }
    if (*old_count == moves->count) fail("old mask has no action");
    b->items=calloc(b->count, sizeof(*b->items)); b->hist=malloc(b->count*sizeof(*b->hist));
    b->logw=malloc(b->count*sizeof(*b->logw));
    if (!b->items || !b->hist || !b->logw) fail("input allocation failed");
    for (size_t i = 0; i < b->count; ++i) {
        char board[65]; int side, ep, halfmove; uint64_t castle, hist; double logw;
        if (fscanf(f, "%64s%d%" SCNx64 "%d%d%" SCNx64 "%lf", board, &side, &castle, &ep, &halfmove, &hist, &logw) != 7 ||
            strlen(board) != 64 || (side != 0 && side != 1) || ep < -1 || ep > 63 || halfmove < 0 || !isfinite(logw)) fail("bad world");
        if (pos_from_board_string(&b->items[i], board, side, castle, ep)) fail("bad board");
        b->items[i].halfmove=halfmove; b->hist[i]=hist; b->logw[i]=(float)logw;
    }
    char extra[2]; if (fscanf(f, "%1s", extra) == 1) fail("extra input");
    if (fclose(f)) fail("input close failed");
}

static uint64_t fingerprint(const Belief *b) {
    uint64_t h = UINT64_C(1469598103934665603);
    const void *parts[] = {b->items,b->hist,b->logw};
    const size_t sizes[] = {b->count*sizeof(*b->items),b->count*sizeof(*b->hist),b->count*sizeof(*b->logw)};
    for (int j = 0; j < 3; ++j) {
        const unsigned char *p=parts[j];
        for (size_t i=0; i<sizes[j]; ++i) h=(h^p[i])*UINT64_C(1099511628211);
    }
    return h;
}
static void print_moves(const Move *moves, int count) {
    putchar('[');
    for (int a=0; a<count; ++a) { char s[6];move_to_uci(moves[a],s);printf("%s\"%s\"",a?",":"",s); }
    putchar(']');
}
static void print_samples(const Belief *b, const RootCensus *c, int budget, uint64_t seed, int stratified) {
    int idx[ASTRA_MAX_DRAWS];double weight[ASTRA_MAX_DRAWS];
    uint64_t rng=seed^UINT64_C(0x5eed);
    const int n=stratified?root_strata_sample(c,budget,&rng,idx,weight):belief_sample(b,budget,&rng,idx,weight);
    putchar('[');
    for (int j=0;j<n;++j) printf("%s{\"index\":%d,\"weight\":%.17g}",j?",":"",idx[j],weight[j]);
    putchar(']');
}

int main(int argc, char **argv) {
    if (argc < 4 || argc > 6) fail("usage: driver describe|search INPUT SEED [SECONDS ORDER]");
    const int search=!strcmp(argv[1],"search");
    if (!search && strcmp(argv[1],"describe")) fail("bad mode");
    const uint64_t seed=strtoull(argv[3],NULL,10);
    const double seconds=argc>4?strtod(argv[4],NULL):0.1;
    const int order=argc>5?atoi(argv[5]):0;
    if (search && (!(seconds>0) || seconds>10 || order<0 || order>3)) fail("bad search budget/order");
    fow_init();zobrist_init();
    Belief b;MoveList moves;Move old_avoid[256],bounded_avoid[256];int old_count,budget;
    read_input(argv[2],&b,&moves,old_avoid,&old_count,&budget);
    const uint64_t before=fingerprint(&b);
    RootCensus c;root_census_build(&c,&b,&moves,budget);
    int bounded_count=root_interval_avoid(&c,2,bounded_avoid);
    if (bounded_count<0) { bounded_count=old_count;memcpy(bounded_avoid,old_avoid,(size_t)old_count*sizeof(Move)); }
    printf("{\"eligible\":%s,\"reason\":\"%s\",\"count\":%zu,\"groups\":%d,\"budget\":%d,\"seed\":%" PRIu64 ",\"census_seconds\":%.9g,\"old_avoid\":",
        c.eligible?"true":"false",c.reason,b.count,c.groups,budget,seed,c.seconds);
    print_moves(old_avoid,old_count);printf(",\"bounded_avoid\":");print_moves(bounded_avoid,bounded_count);
    printf(",\"actions\":[");
    for (int a=0;a<moves.count;++a) {
        char uci[6];move_to_uci(moves.moves[a],uci);
        printf("%s{\"uci\":\"%s\",\"loss\":%.17g,\"win\":%.17g,\"fitted_loss\":%.17g}",a?",":"",uci,c.loss[a],c.win[a],c.fitted_loss[a]);
    }
    printf("],\"ordinary_samples\":");print_samples(&b,&c,budget,seed,0);
    printf(",\"stratified_samples\":");print_samples(&b,&c,budget,seed,1);
    if (!search) {
        printf(",\"group_of\":[");
        for (size_t i=0;i<b.count;++i) printf("%s%d",i?",":"",c.eligible?c.group_of[i]:-1);
        printf("],\"group_mass\":[");
        for (int g=0;c.eligible && g<c.groups;++g) printf("%s%.17g",g?",":"",c.group[g].mass);
        putchar(']');
    }
    printf(",\"searches\":[");
    if (search) {
        const char *sf=getenv("MIST_STOCKFISH");
        if (!sf) fail("explicit Stockfish path required");
        const char *names[]={"ordinary-old","stratified-old","ordinary-bounded","stratified-bounded"};
        for (int step=0;step<4;++step) {
            const int arm=(step+order)%4;
            GtcfrParams p={budget,seconds,1500000,32,10,seed,arm&2?bounded_avoid:old_avoid,arm&2?bounded_count:old_count,2};
            root_strata_activate(&c,arm&1);
            sf_stop();if (!sf_start(sf)) fail("fresh scorer startup failed");
            const double started=now();SearchResult result;
            if (!gtcfr_decide(&b,&p,&result)) fail("search failed");
            const double elapsed=now()-started;
            sf_stop();if (fingerprint(&b)!=before) fail("belief changed during search");
            char uci[6];move_to_uci(result.move,uci);
            printf("%s{\"arm\":\"%s\",\"move\":\"%s\",\"value\":%.17g,\"probability\":%.17g,\"nodes\":%d,\"iterations\":%d,\"samples\":%d,\"seconds\":%.9g}",
                step?",":"",names[arm],uci,result.value,result.probability,result.nodes,result.iterations,result.samples,elapsed);
            fflush(stdout);
        }
    }
    printf("],\"belief_unchanged\":%s}\n",fingerprint(&b)==before?"true":"false");
    root_strata_activate(NULL,0);root_census_free(&c);
    free(b.items);free(b.logw);free(b.hist);
    return 0;
}
