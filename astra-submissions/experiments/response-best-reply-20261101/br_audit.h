#include "br.h"

static uint64_t br_state_hash(const Game *g) {
    uint64_t h=audit_tree_hash(g),bits;
    const double *slots[]={g->regret,g->last,g->strategy,g->strategy_sum,g->fixed_policy};
    for(int j=0;j<5;++j)for(int i=0;i<g->n_slots;++i){memcpy(&bits,&slots[j][i],sizeof(bits));h=audit_hash_word(h,bits);}
    for(int i=0;i<g->n_infosets;++i){memcpy(&bits,&g->confidence[i],sizeof(bits));h=audit_hash_word(h,bits);}
    return h;
}

static void br_audit(const Tree *t,const Belief *b,const int *indices,const double *shares,int count,
                     int root_I,const MoveList *moves,const SearchResult *result,const double *x) {
    const char *path=getenv("ASTRA_BEST_REPLY_TRACE");if(!path)return;
    struct timespec began;clock_gettime(CLOCK_MONOTONIC,&began);
    const Game *g=&t->g;uint64_t before=br_state_hash(g);BrIndex index=br_index(g,1);
    double *policy=malloc((size_t)g->n_slots*sizeof(double)),*reply=malloc((size_t)g->n_slots*sizeof(double));
    double *v[4];for(int j=0;j<4;++j)v[j]=malloc((size_t)g->n_nodes*sizeof(double));
    unsigned char *marks=calloc(g->n_nodes,1);assert(policy&&reply&&marks);for(int j=0;j<4;++j)assert(v[j]);
    /* Focus moves affect only this post-decision audit; they do not enter search. */
    int actions[5]={-1},used=1;char chosen[6];move_to_uci(result->move,chosen);
    for(int a=0;a<moves->count;++a)if(moves->moves[a]==result->move)actions[used++]=a;
    assert(used==2);const char *focus=getenv("ASTRA_BEST_REPLY_FOCUS");
    if(focus)for(int a=0;a<moves->count;++a){char uci[6];move_to_uci(moves->moves[a],uci);if(strstr(focus,uci)){int exists=0;for(int j=1;j<used;++j)exists|=actions[j]==a;if(!exists){assert(used<5);actions[used++]=a;}}}
    FILE *f=fopen(path,"wx");assert(f);
    int first=0,later=0;
    for(int I=0;I<g->n_infosets;++I)if(g->is_player[I]==1&&g->confidence[I]>0){if(index.iprev[I]<0)++first;else ++later;}
    fprintf(f,"{\"chosen\":\"%s\",\"tree_hash\":\"%016" PRIx64 "\",\"nodes\":%d,\"infosets\":%d,\"layers\":%d,\"restricted_first_sets\":%d,\"restricted_later_sets\":%d,\"values_order\":[\"current\",\"restricted_best\",\"first_only_best\",\"unrestricted_best\"],\"profiles\":[",chosen,audit_tree_hash(g),g->n_nodes,g->n_infosets,index.layers,first,later);
    const GameNode *root=&g->nodes[g->root];assert(root->count==count);
    for(int h=0;h<used;++h) {
        int action=actions[h];memcpy(policy,x,(size_t)g->n_slots*sizeof(double));char name[6]="mixed";
        if(action>=0){move_to_uci(moves->moves[action],name);for(int a=0;a<moves->count;++a)policy[g->is_offset[root_I]+a]=a==action?1:0;}
        memset(marks,0,g->n_nodes);double values[4];values[0]=audit_value(g,g->root,policy,v[0],marks);
        const int modes[]={1,2,0};
        for(int j=1;j<4;++j) {
            values[j]=br_solve(g,&index,policy,modes[j-1],reply,v[j]);
            for(int I=0;I<g->n_infosets;++I)if(g->is_player[I]==0)for(int a=0;a<g->is_actions[I];++a)assert(reply[g->is_offset[I]+a]==policy[g->is_offset[I]+a]);
            assert(values[j]<=values[j-1]+1e-8);
        }
        fprintf(f,"%s{\"profile\":\"%s\",\"values\":[%.17g,%.17g,%.17g,%.17g],\"solver_slack\":%.17g,\"future_restriction_gap\":%.17g,\"first_restriction_gap\":%.17g,\"worlds\":[",h?",":"",name,values[0],values[1],values[2],values[3],values[0]-values[1],values[1]-values[2],values[2]-values[3]);
        if(action>=0)for(int k=0;k<count;++k) {
            const Position *position=&b->items[indices[k]];char board[65];pos_to_board_string(position,board);
            const GameNode *world=&g->nodes[g->child[root->first+k]];int id=g->child[world->first+action];const GameNode *node=&g->nodes[id];
            fprintf(f,"%s{\"index\":%d,\"board\":\"%s\",\"weight\":%.17g,\"values\":[%.17g,%.17g,%.17g,%.17g],\"replies\":[",k?",":"",indices[k],board,shares[k],v[0][id],v[1][id],v[2][id],v[3][id]);
            if(node->type==NODE_PLAYER) {
                Position p=*position;Undo undo;make_move(&p,moves->moves[action],&undo);MoveList replies;generate_moves(&p,&replies);assert(node->player==1&&replies.count==node->count);
                for(int a=0;a<replies.count;++a){char uci[6];move_to_uci(replies.moves[a],uci);int child=g->child[node->first+a];fprintf(f,"%s{\"move\":\"%s\",\"values\":[%.17g,%.17g,%.17g,%.17g]}",a?",":"",uci,v[0][child],v[1][child],v[2][child],v[3][child]);}
            }
            fprintf(f,"]}");
        }
        fprintf(f,"]}");
    }
    assert(before==br_state_hash(g));
    fprintf(f,"],\"state_unchanged\":true,\"seconds\":%.9g,\"scope\":\"Fixed finite tree and fixed own continuation, conditional on root profile. Values are not full-game exploitability or Elo.\"}\n",seconds_since(&began));
    assert(!ferror(f)&&fclose(f)==0);br_index_free(&index);free(policy);free(reply);free(marks);for(int j=0;j<4;++j)free(v[j]);
}
