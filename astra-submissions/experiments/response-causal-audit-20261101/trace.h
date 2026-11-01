/* Post-decision export only: no truth input and no extra solver iterations.
 * audit_value is inherited byte-for-byte from the tested frozen-tree audit. */
#include "audit.h"

static double *trace_initial(const Game *g, int actions) {
    if (!getenv("ASTRA_RESPONSE_TRACE")) return NULL;
    const GameNode *root=&g->nodes[g->root];
    double *values=malloc((size_t)root->count*actions*sizeof(double));assert(values);
    for(int k=0;k<root->count;++k) {
        const GameNode *world=&g->nodes[g->child[root->first+k]];assert(world->count==actions);
        for(int a=0;a<actions;++a) values[k*actions+a]=g->nodes[g->child[world->first+a]].value;
    }
    return values;
}

static void trace_final(const Tree *t,const Belief *b,const int *indices,const double *shares,int count,
                        int root_I,const MoveList *moves,const SearchResult *result,const double *x,double *initial) {
    if(!initial)return;
    FILE *f=fopen(getenv("ASTRA_RESPONSE_TRACE"),"wx");assert(f);
    double *values=malloc((size_t)t->g.n_nodes*sizeof(double));unsigned char *marks=calloc(t->g.n_nodes,1);
    assert(values&&marks);double v=audit_value(&t->g,t->g.root,x,values,marks);
    assert(fabs(v-result->value)<1e-8 && fabs(v-game_value(&t->g,x))<1e-8);
    char move[6];move_to_uci(result->move,move);
    fprintf(f,"{\"chosen\":\"%s\",\"value\":%.17g,\"us\":%d,\"nodes\":%d,\"belief_capped\":%s,\"belief\":[",move,v,b->us,t->g.n_nodes,b->overflowed?"true":"false");
    double total=0;for(size_t i=0;i<b->count;++i)total+=b->logw?exp((double)b->logw[i]):1;
    assert(total>0);
    for(size_t i=0;i<b->count;++i) {
        char board[65];pos_to_board_string(&b->items[i],board);
        fprintf(f,"%s{\"board\":\"%s\",\"weight\":%.17g,\"castle\":%" PRIu64 ",\"ep\":%d}",
                i?",":"",board,(b->logw?exp((double)b->logw[i]):1)/total,b->items[i].castle_rooks,b->items[i].ep);
    }
    fprintf(f,"],\"root_actions\":[");const GameNode *root=&t->g.nodes[t->g.root];assert(root->count==count);
    for(int a=0;a<moves->count;++a) {
        double q=0,start=0;move_to_uci(moves->moves[a],move);
        for(int k=0;k<count;++k){const GameNode *world=&t->g.nodes[t->g.child[root->first+k]];q+=shares[k]*values[t->g.child[world->first+a]];start+=shares[k]*initial[k*moves->count+a];}
        fprintf(f,"%s{\"move\":\"%s\",\"probability\":%.17g,\"initial_q\":%.17g,\"q\":%.17g}",a?",":"",move,x[t->g.is_offset[root_I]+a],start,q);
    }
    fprintf(f,"],\"worlds\":[");
    for(int k=0;k<count;++k) {
        const Position *position=&b->items[indices[k]];char board[65];pos_to_board_string(position,board);
        const GameNode *world=&t->g.nodes[t->g.child[root->first+k]];
        assert(fabs(shares[k]-t->g.prob[root->first+k])<1e-12);
        fprintf(f,"%s{\"belief_index\":%d,\"board\":\"%s\",\"weight\":%.17g,\"actions\":[",k?",":"",indices[k],board,shares[k]);
        for(int a=0;a<moves->count;++a) {
            int id=t->g.child[world->first+a];const GameNode *node=&t->g.nodes[id];move_to_uci(moves->moves[a],move);
            fprintf(f,"%s{\"move\":\"%s\",\"initial_q\":%.17g,\"q\":%.17g,\"expanded\":%s,\"replies\":[",a?",":"",move,initial[k*moves->count+a],values[id],node->type==NODE_PLAYER?"true":"false");
            if(node->type==NODE_PLAYER) {
                Position p=*position;Undo undo;make_move(&p,moves->moves[a],&undo);MoveList replies;generate_moves(&p,&replies);
                assert(node->player==1 && replies.count==node->count);int offset=t->g.is_offset[node->infoset];
                double confidence=t->g.confidence[node->infoset],sum=0;
                for(int j=0;j<replies.count;++j) {
                    move_to_uci(replies.moves[j],move);int child=t->g.child[node->first+j];
                    double probability=x[offset+j],fixed=confidence>0?t->g.fixed_policy[offset+j]:0;
                    double free_probability=confidence<1?(probability-confidence*fixed)/(1-confidence):0;
                    assert(free_probability>=-1e-8);sum+=probability;
                    fprintf(f,"%s{\"move\":\"%s\",\"probability\":%.17g,\"fixed\":%.17g,\"confidence\":%.17g,\"free\":%.17g,\"q\":%.17g,\"expanded\":%s}",j?",":"",move,probability,fixed,confidence,free_probability,values[child],t->g.nodes[child].type==NODE_PLAYER?"true":"false");
                }
                assert(fabs(sum-1)<1e-8);
            }
            fprintf(f,"]}");
        }
        fprintf(f,"]}");
    }
    fprintf(f,"],\"diagnostic_only\":true,\"true_board_input\":false}\n");assert(!ferror(f));assert(fclose(f)==0);
    free(values);free(marks);free(initial);
}
