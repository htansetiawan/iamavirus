/* Offline oracle, building on the immutable first miner's rules helpers. */
#define main same_current_action_miner
#include "../past-alias-20261110/mine.c"
#undef main

typedef struct {
    Position pos;
    Move move;
    char view[65];
    MoveList replies;
    uint64_t safe[4], signature, join;
    int danger;
} Child;

static uint64_t bytes_hash(uint64_t h,const void *ptr,size_t n) {
    const unsigned char *p=ptr;
    for(size_t i=0;i<n;++i)h=(h^p[i])*UINT64_C(1099511628211);
    return h;
}
static int same_row(const Child *a,const Child *b) {
    return !memcmp(a->view,b->view,64) && a->replies.count==b->replies.count
        && !memcmp(a->replies.moves,b->replies.moves,(size_t)a->replies.count*sizeof(Move));
}
static int earlier(Move a,Move b) {
    char x[6],y[6];move_to_uci(a,x);move_to_uci(b,y);return strcmp(x,y)<0;
}

/* Task-specific compression for the one-reply diagnostic only. Equal views,
 * legal rows, royal danger and reply-safety signatures get ONE representative.
 * This does not merge nodes or information histories in a playing search. */
static int children(const Position *root,int us,Child *out,int *raw) {
    int table[1024];for(int i=0;i<1024;++i)table[i]=-1;
    MoveList moves;generate_moves(root,&moves);int count=0;*raw=0;
    for(int a=0;a<moves.count;++a) {
        Child c;memset(&c,0,sizeof c);c.pos=*root;c.move=moves.moves[a];Undo u;
        make_move(&c.pos,c.move,&u);if(!continued(&c.pos))continue;
        observation(&c.pos,us^1,c.view);generate_moves(&c.pos,&c.replies);if(!c.replies.count)continue;
        c.danger=is_attacked(&c.pos,king_square(&c.pos,us^1),us);
        for(int r=0;r<c.replies.count;++r)if(reply_safe(&c.pos,c.replies.moves[r]))c.safe[r/64]|=UINT64_C(1)<<(r%64);
        c.join=bytes_hash(UINT64_C(1469598103934665603),c.view,64);
        c.join=bytes_hash(c.join,c.replies.moves,(size_t)c.replies.count*sizeof(Move));
        c.signature=bytes_hash(c.join,c.safe,sizeof c.safe)^((uint64_t)c.danger*UINT64_C(0x9e3779b97f4a7c15));
        size_t slot=c.signature&1023;
        while(table[slot]>=0) {
            Child *old=&out[table[slot]];
            if(old->signature==c.signature && old->danger==c.danger && same_row(old,&c) && !memcmp(old->safe,c.safe,sizeof c.safe))break;
            slot=(slot+1)&1023;
        }
        if(table[slot]<0){table[slot]=count;out[count++]=c;}
        else if(earlier(c.move,out[table[slot]].move))out[table[slot]]=c;
        ++*raw;
    }
    return count;
}

int main(void) {
    fow_init();char board[65],a_text[6],b_text[6];int side,ep,halfmove;uint64_t castle;long context=0;
    while(scanf("%64s%d%" SCNx64 "%d%d%5s%5s",board,&side,&castle,&ep,&halfmove,a_text,b_text)==7) {
        Position before;if((side!=0&&side!=1)||strlen(board)!=64||pos_from_board_string(&before,board,side,castle,ep))return 2;
        before.halfmove=halfmove;Move a,b;Undo u;
        if(!parse_move(&before,a_text,&a))return 3;
        Position after_a=before;make_move(&after_a,a,&u);if(!continued(&after_a))return 4;
        if(!parse_move(&after_a,b_text,&b))return 5;
        Position actual=after_a;make_move(&actual,b,&u);if(!continued(&actual))return 6;
        Child pchildren[256],qchildren[256];int praw=0;
        const int pn=children(&actual,side,pchildren,&praw);
        /* Index opposite-danger rows by observation/legal-row hash. Once
         * signatures are deduplicated, non-output equal-safety comparisons
         * are at most linear. Remaining cross products are output size. */
        int heads[1024],next[256];for(int k=0;k<1024;++k)heads[k]=-1;
        for(int k=0;k<pn;++k){uint64_t h=pchildren[k].join^((uint64_t)pchildren[k].danger*UINT64_C(0x9e3779b97f4a7c15));
            int slot=(int)(h&1023);next[k]=heads[slot];heads[slot]=k;}
        MoveList alternatives;generate_moves(&before,&alternatives);
        int aliases=0,witnesses=0,qrawsum=0,qsigsum=0,comparisons=0;
        for(int i=0;i<alternatives.count;++i) {
            const Move alt=alternatives.moves[i];if(alt==a)continue;
            Position q=before;make_move(&q,alt,&u);if(!continued(&q)||!same_view(&q,&after_a,side^1))continue;
            Move checked;if(!parse_move(&q,b_text,&checked)||checked!=b)continue;
            make_move(&q,b,&u);if(!continued(&q)||!same_view(&q,&actual,side^1))continue;
            char qb[65],pb[65];pos_to_board_string(&q,qb);pos_to_board_string(&actual,pb);if(!memcmp(qb,pb,64))continue;
            ++aliases;int qraw=0,qn=children(&q,side,qchildren,&qraw);qrawsum+=qraw;qsigsum+=qn;
            for(int j=0;j<qn;++j) {
                const Child *cq=&qchildren[j];uint64_t h=cq->join^((uint64_t)(cq->danger^1)*UINT64_C(0x9e3779b97f4a7c15));
                for(int k=heads[h&1023];k>=0;k=next[k]) {
                    const Child *cp=&pchildren[k];++comparisons;
                    if(cp->join!=cq->join || cp->danger==cq->danger || !same_row(cp,cq) || !memcmp(cp->safe,cq->safe,sizeof cp->safe))continue;
                    int np=0,nq=0,intersection=0;
                    for(int r=0;r<cp->replies.count;++r){int sp=(cp->safe[r/64]>>(r%64))&1,sq=(cq->safe[r/64]>>(r%64))&1;np+=sp;nq+=sq;intersection+=sp&&sq;}
                    ++witnesses;char alt_text[6],c_text[6],d_text[6];move_to_uci(alt,alt_text);move_to_uci(cp->move,c_text);move_to_uci(cq->move,d_text);
                    printf("{\"kind\":\"witness\",\"context\":%ld,\"actual_previous\":\"%s\",\"alternative_previous\":\"%s\","
                           "\"same_opponent_move\":\"%s\",\"actual_current_move\":\"%s\",\"alternative_current_move\":\"%s\","
                           "\"shared_opponent_view\":\"%s\",\"actual_danger\":%d,\"alternative_danger\":%d,"
                           "\"safe_counts\":[%d,%d],\"safe_intersection\":%d,\"reach_weights\":null,\"ancestor\":",
                           context,a_text,alt_text,b_text,c_text,d_text,cp->view,cp->danger,cq->danger,np,nq,intersection);
                    print_position(&before);printf(",\"actual_root\":");print_position(&actual);printf(",\"alternative_root\":");print_position(&q);
                    printf(",\"replies\":[");
                    for(int r=0;r<cp->replies.count;++r){char s[6];move_to_uci(cp->replies.moves[r],s);
                        printf("%s{\"uci\":\"%s\",\"actual_safe\":%d,\"alternative_safe\":%d}",r?",":"",s,
                              (int)((cp->safe[r/64]>>(r%64))&1),(int)((cq->safe[r/64]>>(r%64))&1));}
                    printf("]}\n");
                }
            }
        }
        printf("{\"kind\":\"summary\",\"context\":%ld,\"past_aliases\":%d,\"actual_children\":%d,\"actual_signatures\":%d,"
               "\"alternative_children\":%d,\"alternative_signatures\":%d,\"join_comparisons\":%d,\"witnesses\":%d}\n",
               context,aliases,praw,pn,qrawsum,qsigsum,comparisons,witnesses);
        ++context;
    }
    return (ferror(stdin)||fflush(stdout)||ferror(stdout))?7:0;
}
