/* An independently grouped exhaustive transition oracle for the modified
 * belief. Including the implementation exposes settings for all three arms
 * in one test; the oracle never uses its sorting/merge/context-key routine. */
#include "native/belief.c"
#include <assert.h>

typedef struct { uint64_t key; uint32_t recent; double mass; } Expected;
static Move get_move(const Position *p,const char *uci) {
    MoveList l;generate_moves(p,&l);
    for(int i=0;i<l.count;++i){char s[6];move_to_uci(l.moves[i],s);if(!strcmp(s,uci))return l.moves[i];}
    assert(0);return 0;
}
static void check_distribution(int mode,int split,float temp) {
    astra_model=mode;astra_context_merge=split;model_temp=temp;
    Belief b;belief_init_start(&b,WHITE,100000);Position p;pos_clear(&p);p.side=BLACK;
    pos_put(&p,0,WHITE,KING);pos_put(&p,7,WHITE,ROOK);pos_put(&p,60,BLACK,KING);pos_put(&p,42,BLACK,KNIGHT);
    b.count=2;b.items[0]=p;b.items[1]=p;b.logw[0]=0;b.logw[1]=-.7f;
    RecentOwn a={MAKE_MOVE(57,42,NO_PIECE),1,KNIGHT,0,0};
    RecentOwn c={MAKE_MOVE(62,60,NO_PIECE),1,KING,0,0};
    b.recent[0]=recent_pack(a);b.recent[1]=recent_pack(c);b.hist[0]=17;b.hist[1]=29;
    Position actual=p;Undo u;make_move(&actual,get_move(&p,"c6b4"),&u);char view[65];observation(&actual,WHITE,view);
    Expected expected[1024];int n=0;double total=0;
    for(size_t i=0;i<b.count;++i){
        MoveList l;generate_moves(&b.items[i],&l);float z[256];recent_logits(b.recent[i],&b.items[i],&l,b.last_own,mode,z);
        double top=-INFINITY;for(int j=0;j<l.count;++j)if(z[j]>top)top=z[j];
        double sum=0;for(int j=0;j<l.count;++j)sum+=exp(z[j]-top);double logz=top+log(sum);
        for(int j=0;j<l.count;++j){
            Position q=b.items[i];make_move(&q,l.moves[j],&u);char v[65];observation(&q,WHITE,v);
            if(strcmp(v,view)||mover_left_king_capturable(&q))continue;
            uint64_t key=position_key(&q);uint32_t context=recent_advance(b.recent[i],&b.items[i],l.moves[j]);
            double mass=exp((double)b.logw[i]+temp*(z[j]-logz));int at=0;
            while(at<n && !(expected[at].key==key && (!split||expected[at].recent==context)))++at;
            if(at==n){assert(n<1024);expected[n++]=(Expected){key,context,0};}
            expected[at].mass+=mass;total+=mass;
        }
    }
    belief_after_opponent(&b,view);assert(b.count==(size_t)n && !b.overflowed);
    double kept=0;for(size_t i=0;i<b.count;++i)kept+=exp(b.logw[i]);
    for(size_t i=0;i<b.count;++i){int at=0;
        while(at<n && !(position_key(&b.items[i])==expected[at].key && (!split||b.recent[i]==expected[at].recent)))++at;
        assert(at<n);assert(fabs(exp(b.logw[i])/kept-expected[at].mass/total)<2e-7);
    }
    belief_shrink(&b,3);assert(b.count==3);
    for(size_t i=0;i<b.count;++i){int found=0;
        for(int j=0;j<n;++j) {
            if(position_key(&b.items[i])==expected[j].key && (!split||b.recent[i]==expected[j].recent))found=1;
        }
        assert(found);
    }
    char board[65];pos_to_board_string(&b.items[1],board);uint32_t retained=b.recent[1];
    belief_keep_board(&b,board,NULL);assert(b.count>=1);
    int present=0;for(size_t i=0;i<b.count;++i)if(b.recent[i]==retained)present=1;assert(present);
    Position fallback=b.items[0];pos_put(&fallback,32,BLACK,PAWN);pos_to_board_string(&fallback,board);
    double natural;belief_force_board_share(&b,board,&fallback,.2,&natural);assert(b.recent[b.count-1]==0 && natural==0);
    pos_put(&fallback,33,BLACK,PAWN);pos_to_board_string(&fallback,board);
    assert(belief_keep_board(&b,board,&fallback)==0 && b.count==1 && b.recent[0]==0);
    /* Parallel own update must carry its matching context, not a shared one. */
    b.items=realloc(b.items,4096*sizeof(Position));b.hist=realloc(b.hist,4096*sizeof(uint64_t));
    b.logw=realloc(b.logw,4096*sizeof(float));b.recent=realloc(b.recent,4096*sizeof(uint32_t));
    b.count=b.capacity=4096;p.side=WHITE;
    for(size_t i=0;i<b.count;++i){b.items[i]=p;b.hist[i]=i;b.logw[i]=0;b.recent[i]=recent_pack(i%2?a:c);}
    actual=p;Move own=get_move(&p,"a1b1");make_move(&actual,own,&u);observation(&actual,WHITE,view);
    belief_after_own(&b,own,view);assert(b.count==4096);
    for(size_t i=0;i<b.count;++i)assert(b.recent[i]==recent_pack(i%2?a:c));
    /* Rebuilt worlds have no invented action history. */
    pos_clear(&p);p.side=WHITE;pos_put(&p,0,WHITE,KING);pos_put(&p,45,WHITE,QUEEN);pos_put(&p,63,BLACK,KING);
    observation(&p,WHITE,view);int their[6]={0,0,0,0,0,1};
    size_t rebuilt=belief_resample(&b,view,their,0,8,100);assert(rebuilt>0);
    for(size_t i=0;i<b.count;++i)assert(b.recent[i]==0);
    belief_free(&b);
}
int main(void) {
    fow_init();zobrist_init();settings_read=1;model_on=1;prune_capturable=1;hist_table=NULL;threads_setting=2;
    for(int i=0;i<10000;++i){RecentOwn r={(Move)(i*37),1,i%6,i%10,i%2};RecentOwn q=recent_unpack(recent_pack(r));
        assert(q.move==r.move && q.known==r.known && q.type==r.type && q.captured_value==r.captured_value && q.continued==r.continued);}
    Position p;pos_start(&p);astra_context_merge=1;
    for(int bit=0;bit<25;++bit)assert(context_key(&p,0)!=context_key(&p,1U<<bit));
    for(int t=1;t<=2;++t){check_distribution(0,0,(float)t);check_distribution(0,1,(float)t);check_distribution(1,1,(float)t);}
    printf("PASS: exhaustive posterior oracle, temp1/2, static/temporal, merge/split, packed25bits, shrink, keep, forced fallback, parallel own update, rebuild unknown; Candidate=%zu\n",sizeof(Candidate));
    return 0;
}
