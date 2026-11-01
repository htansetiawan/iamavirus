#!/usr/bin/env python3
"""Isolated persistent-mode successor; original experiments remain immutable."""
import difflib,hashlib,json,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PARENT=HERE.parent/'observable-response-search-20261101'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def main():
    pin=json.loads((PARENT/'provenance.json').read_text())
    for p,h in pin['source_sha256'].items():assert sha(ROOT/p)==h,p
    build=HERE/'build';build.mkdir(exist_ok=False);shutil.copytree(PARENT/'build/src',build/'src')
    original={p.name:p.read_text() for p in (build/'src').glob('*')}
    shutil.copyfile(HERE/'mode.h',build/'src/mode.h')
    p=build/'src/gtcfr.c';s=p.read_text()
    s=replace(s,'#include "sfeval.h"','#include "sfeval.h"\n#include "mode.h"')
    s=replace(s,'    int node;                    /* the Game node, currently an evaluated leaf */','    int node;                    /* the Game node, currently an evaluated leaf */\n    int opponent_mode;          /* persistent0=free,1=fixed; never in our history */')
    s=replace(s,'    Game g;','    Game g;\n    int persistent;\n    double model_prior;\n    unsigned long mode_expansions[2];')
    marker='static void remember_leaf(Tree *t, int node, const Position *p, const uint64_t hist[2]) {'
    s=replace(s,marker,'''static int mode_infoset(Tree *t,int player,uint64_t hist,int actions,int mode) {
    assert(mode==0||mode==1);
    /* history_mix forces the value low bit on; tags must differ above it. */
    if(t->persistent&&player==1)hist=history_mix(hist,0x5045525349535400ULL+2*(uint64_t)mode);
    return infoset_for(t,player,hist,actions);
}

static void remember_leaf(Tree *t, int node, const Position *p, const uint64_t hist[2], int mode) {''')
    s=replace(s,'    l->node = node; l->pos = *p;','    l->node = node; l->opponent_mode = mode; l->pos = *p;')
    s=replace(s,'                                 int sf, const int *sf_cp, const int *sf_found) {','                                 int sf, const int *sf_cp, const int *sf_found, int mode) {')
    s=replace(s,'        remember_leaf(t, kids[a], &q, h);','        remember_leaf(t, kids[a], &q, h, mode);')
    s=replace(s,'static int build_children(Tree *t, const Position *p, const uint64_t hist[2], int *kids, const MoveList *only) {','static int build_children(Tree *t, const Position *p, const uint64_t hist[2], int *kids, const MoveList *only, int mode) {')
    s=replace(s,'    return build_children_scored(t, p, hist, kids, only, sf, sf_cp, sf_found);','    return build_children_scored(t, p, hist, kids, only, sf, sf_cp, sf_found, mode);')
    s=replace(s,'    const int count = build_children_scored(t, &leaf.pos, leaf.hist, kids, NULL, sf, sf_cp, sf_found);','    const int count = build_children_scored(t, &leaf.pos, leaf.hist, kids, NULL, sf, sf_cp, sf_found, leaf.opponent_mode);')
    s=replace(s,'    const int I = infoset_for(t, player, leaf.hist[player], count);','    const int I = mode_infoset(t, player, leaf.hist[player], count, leaf.opponent_mode);')
    s=replace(s,'    t->leaf_of[leaf.node] = -1;','    t->leaf_of[leaf.node] = -1;\n    ++t->mode_expansions[leaf.opponent_mode];')
    marker='    t.best_init = !(getenv("MIST_BEST_INIT") && atoi(getenv("MIST_BEST_INIT")) == 0);'
    s=replace(s,marker,marker+'''
    if(getenv("ASTRA_PERSISTENT")&&atoi(getenv("ASTRA_PERSISTENT"))==1) {
        visible_config();
        if(visible_weights&&visible_confidence>0){t.persistent=1;t.model_prior=visible_confidence;}
    }''')
    start='    int *chance_kids = malloc(K * sizeof(int)); double *chance_p = malloc(K * sizeof(double));'
    end='    game_children(&t.g, root, chance_kids, chance_p, K);'
    assert s.count(start)==1 and s.count(end)==1
    a=s.index(start);z=s.index(end,a)+len(end)
    s=s[:a]+'''    const int modes=t.persistent?persistent_count(t.model_prior):1;
    int *chance_kids = malloc(K*modes*sizeof(int)); double *chance_p = malloc(K*modes*sizeof(double));
    int kids[256],branches=0;
    for(int k=0;k<K;++k) {
        const Position *p=&b->items[idx[k]];
        const uint64_t hist[2]={our_root_hist,b->hist?b->hist[idx[k]]:0};
        int sf_cp[256],sf_found[256],sf=0;
        /* Root leaf evaluation is identical in both modes; ask Stockfish once. */
        if(t.persistent&&sf_ready())sf=sf_children(p,&ours,sf_cp,sf_found);
        for(int branch=0;branch<modes;++branch) {
            int mode=t.persistent?persistent_mode(t.model_prior,branch):0;
            int node=game_node(&t.g,NODE_TERMINAL,0,-1,0);
            int count=t.persistent?build_children_scored(&t,p,hist,kids,&ours,sf,sf_cp,sf_found,mode):build_children(&t,p,hist,kids,&ours,0);
            game_expand_leaf(&t.g,node,0,root_I,kids,count);
            chance_kids[branches]=node;
            chance_p[branches++]=share[k]*(t.persistent?persistent_weight(t.model_prior,mode):1);
        }
    }
    assert(branches==K*modes);
    game_children(&t.g,root,chance_kids,chance_p,branches);'''+s[z:]
    marker='    dbr_report(&t, x);'
    s=replace(s,marker,marker+'''
    if(t.persistent)fprintf(stderr,"astra_persistent: prior %.9g physical_worlds %d branches %d free_expansions %lu fixed_expansions %lu\\n",t.model_prior,K,branches,t.mode_expansions[0],t.mode_expansions[1]);''')
    p.write_text(s)
    p=build/'src/dbr.h';s=p.read_text()
    s=replace(s,'    if (t->g.is_player[I] != 1 || !visible_weights) return;','    if (t->g.is_player[I] != 1 || !visible_weights || (t->persistent&&leaf->opponent_mode==0)) return;')
    s=replace(s,'    game_restrict(&t->g, I, visible_confidence, q);','    game_restrict(&t->g, I, t->persistent?1:visible_confidence, q);');p.write_text(s)
    # No solver, belief, guard, board, neural, clock or root-purification changes.
    for name in ['cfr.c','cfr.h','belief.c','main.c','board.c','movemodel.c','response.c','adapter.c']:
        assert sha(build/'src'/name)==sha(PARENT/'build/src'/name),name
    patch=[]
    for name,before in original.items():
        after=(build/'src'/name).read_text()
        if before!=after:patch.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/'+name,tofile='b/src/'+name))
    (HERE/'patch.diff').write_text(''.join(patch))
    cmd=['gcc','-O2','-pthread','-D_POSIX_C_SOURCE=199309L','-std=c11',*[str(p.relative_to(build)) for p in sorted((build/'src').glob('*.c'))],'-lm','-o','mist']
    r=subprocess.run(cmd,cwd=build,text=True,capture_output=True);(HERE/'build.log').write_text(r.stdout+r.stderr);r.check_returncode()
    result=dict(parent_provenance_sha256=sha(PARENT/'provenance.json'),parent_binary_sha256=sha(PARENT/'build/mist'),binary_sha256=sha(build/'mist'),model_sha256=pin['model_sha256'],compiler=cmd,
                source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'mode.h',HERE/'patch.diff',*sorted((build/'src').glob('*'))]},
                invariants='Mode carried through all leaves; our history keys and action choice unchanged; opponent keys include mode; free mode unrestricted, model mode fixed. Root scoring reused across modes.')
    (HERE/'provenance.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'binary':result['binary_sha256']}))
if __name__=='__main__':main()
