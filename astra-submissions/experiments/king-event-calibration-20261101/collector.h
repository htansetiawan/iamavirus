/* Diagnostic only. Included in a copy of immutable v35 main.c.
 * No truth input, sampling, decision overrides, or learned parameters here. */
typedef struct { double flat,sharp,uniform,invalid; size_t scanned; } AstraKingRisk;

static void astra_king_risks(const Belief *b, const MoveList *actions,
                            double temp, AstraKingRisk *out) {
    const size_t cap=20000;
    const size_t stride=b->count>cap ? (b->count+cap-1)/cap : 1;
    double total[3]={0,0,0}, lost[256][3]={{0}}, invalid[256]={0};
    /* Moves occupy 15 bits (six from, six to, three promotion).
     * Reverse lookup makes legality O(legal_moves + candidate_moves) per world,
     * rather than a quadratic comparison of the two lists. */
    int16_t slot[1<<15];memset(slot,-1,sizeof(slot));
    for(int a=0;a<actions->count;++a)slot[actions->moves[a]]=(int16_t)a;
    size_t scanned=0;
    /* One move-list construction per board, reused across actions. */
    for(size_t i=0;i<b->count;i+=stride){
        const Position *p=&b->items[i]; MoveList legal;generate_moves(p,&legal);
        unsigned char valid[256]={0};
        for(int j=0;j<legal.count;++j){int a=slot[legal.moves[j]];if(a>=0)valid[a]=1;}
        const double lw=b->logw ? (double)b->logw[i] : 0;
        const double weight[3]={exp(lw/temp),exp(lw),1};
        for(int w=0;w<3;++w)total[w]+=weight[w];
        ++scanned;
        for(int a=0;a<actions->count;++a){
            if(!valid[a]){invalid[a]+=weight[1];continue;}
            Position q=*p;Undo u;make_move(&q,actions->moves[a],&u);
            /* Exact root terminal event: capturing their king wins first. */
            if(king_square(&q,p->side^1)>=0 && mover_left_king_capturable(&q))
                for(int w=0;w<3;++w)lost[a][w]+=weight[w];
        }
    }
    for(int a=0;a<actions->count;++a){
        out[a]=(AstraKingRisk){total[0]>0?lost[a][0]/total[0]:0,
                              total[1]>0?lost[a][1]/total[1]:0,
                              total[2]>0?lost[a][2]/total[2]:0,
                              total[1]>0?invalid[a]/total[1]:0,scanned};
    }
}

static void astra_king_events(const Belief *b, const MoveList *actions,
                              int decision, double temp) {
    AstraKingRisk risk[256];astra_king_risks(b,actions,temp,risk);
    for(int a=0;a<actions->count;++a){
        char move[6];move_to_uci(actions->moves[a],move);
        fprintf(stderr,"astra_king %d %s %.12g %.12g %.12g %.12g %zu %zu %d\n",
                decision,move,risk[a].flat,risk[a].sharp,risk[a].uniform,
                risk[a].invalid,b->count,risk[a].scanned,b->overflowed);
    }
}
