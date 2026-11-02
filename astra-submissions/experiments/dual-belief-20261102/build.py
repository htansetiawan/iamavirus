from pathlib import Path
import difflib, hashlib, json, subprocess, zipfile

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
OUT=ROOT/'astra-submissions/analysis/dual-belief-20261102'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def change(s,a,b,n=1):
    assert s.count(a)==n,(a[:80],s.count(a),n)
    return s.replace(a,b)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    base=HERE/'build/base'; cand=HERE/'build/candidate'
    archive=ROOT/'fable-submissions/iamavirus-v37-mist-c-v14-allfit.zip'
    assert sha(archive)=='41e02e280b61e0e0c031a831d2ab4b2cc8f52c6c59bd8c11fc026f3cc817c76c'
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if name.endswith('/') or not(name.startswith('src/') or name in ('build.sh','data/history.bin')):continue
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            for directory in (base,cand):
                p=directory/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
    h=(base/'src/belief.h').read_text()
    h=change(h,'    float *logw;', '    float *logw1;       /* untempered likelihood on the same retained transition graph */\n    float *logw;')
    (cand/'src/belief.h').write_text(h)
    s=(base/'src/belief.c').read_text()
    s=change(s,'    b->logw[0] = 0;', '    b->logw[0] = 0;\n    b->logw1 = malloc(b->capacity * sizeof(float));\n    b->logw1[0] = 0;')
    s=change(s,'    free(b->logw);','    free(b->logw); free(b->logw1);')
    s=change(s,'float *logw; size_t count, capacity;', 'float *logw, *logw1; size_t count, capacity;')
    s=change(s,'uint64_t hist, float logw) {','uint64_t hist, float logw, float logw1) {')
    s=change(s,'        v->logw = realloc(v->logw, v->capacity * sizeof(float));','        v->logw = realloc(v->logw, v->capacity * sizeof(float));\n        v->logw1 = realloc(v->logw1, v->capacity * sizeof(float));')
    s=change(s,'v->logw[v->count] = logw; ++v->count;','v->logw[v->count] = logw; v->logw1[v->count] = logw1; ++v->count;')
    s=change(s,'free(b->items); free(b->hist); free(b->logw);','free(b->items); free(b->hist); free(b->logw); free(b->logw1);')
    s=change(s,'    b->logw = next->logw;', '''    b->logw = next->logw;
    float top1 = -INFINITY;
    for (size_t i = 0; i < next->count; ++i) if (next->logw1[i] > top1) top1 = next->logw1[i];
    for (size_t i = 0; i < next->count; ++i) next->logw1[i] -= top1;
    b->logw1 = next->logw1;''')
    s=change(s,'Move move; float logw; } Candidate;', 'Move move; float logw, logw1; } Candidate;')
    needle='                        : model_temp * (logit[j] - log_z));'
    s=change(s,needle,needle+'''
                    c->logw1 = (b->logw1 ? b->logw1[i] : 0.0f) + (!model_on ? 0.0f : N > 0
                        ? logf(((float)hc[j] + hist_n0 * expf(logit[j] - log_z)) / ((float)N + hist_n0))
                        : logit[j] - log_z);''')
    s=change(s,'        w->next->logw[k] = c->logw;', '        w->next->logw[k] = c->logw; w->next->logw1[k] = c->logw1;')
    s=change(s,'        float total = cand[i].logw;', '        float total = cand[i].logw; float total1 = cand[i].logw1;')
    s=change(s,'            total = log_add(total, cand[j].logw);', '            total = log_add(total, cand[j].logw);\n            total1 = log_add(total1, cand[j].logw1);')
    s=change(s,'        best.logw = total;', '        best.logw = total; best.logw1 = total1;')
    s=change(s,'    next.logw = malloc(next.capacity * sizeof(float));','    next.logw = malloc(next.capacity * sizeof(float));\n    next.logw1 = malloc(next.capacity * sizeof(float));')
    s=change(s,'b->logw ? b->logw[i] : 0.0f);   /* distinct', 'b->logw ? b->logw[i] : 0.0f, b->logw1 ? b->logw1[i] : 0.0f);   /* distinct')
    s=change(s,'            next.logw = realloc(next.logw, n * sizeof(float));','            next.logw = realloc(next.logw, n * sizeof(float));\n            next.logw1 = realloc(next.logw1, n * sizeof(float));')
    s=change(s,'                memcpy(next.logw + next.count, v->logw, v->count * sizeof(float));','                memcpy(next.logw + next.count, v->logw, v->count * sizeof(float));\n                memcpy(next.logw1 + next.count, v->logw1, v->count * sizeof(float));')
    s=change(s,'free(v->items); free(v->hist); free(v->logw);','free(v->items); free(v->hist); free(v->logw); free(v->logw1);')
    s=change(s,'        if (b->logw) b->logw[k] = b->logw[keep[k]];','        if (b->logw) b->logw[k] = b->logw[keep[k]];\n        if (b->logw1) b->logw1[k] = b->logw1[keep[k]];')
    s=change(s,'history_mix(0x7265, view_hash(theirs)), 0.0f);', 'history_mix(0x7265, view_hash(theirs)), 0.0f, 0.0f);')
    s=change(s,'free(next.items); free(next.hist); free(next.logw); return b->count;', 'free(next.items); free(next.hist); free(next.logw); free(next.logw1); return b->count;')
    (cand/'src/belief.c').write_text(s)
    s=(base/'src/main.c').read_text()
    s=change(s,'static int is_view(', '''static int dual_guard = 0;

static int is_view(''')
    s=change(s,'const double wt = exp(lw), w1 = exp(lw / temp);', 'const double wt = exp(lw), w1 = exp(dual_guard && b->logw1 ? b->logw1[i] : lw / temp);',2)
    # Set once before serving the protocol. Existing environment knobs unchanged.
    start=s.index('int main('); brace=s.index('{',start)
    s=s[:brace+1]+'\n    dual_guard = getenv("MIST_DUAL_GUARD") && atoi(getenv("MIST_DUAL_GUARD")) != 0;'+s[brace+1:]
    (cand/'src/main.c').write_text(s)
    patches=[]
    for name in ('belief.h','belief.c','main.c'):
        patches+=difflib.unified_diff((base/'src'/name).read_text().splitlines(True),(cand/'src'/name).read_text().splitlines(True),fromfile='v37/src/'+name,tofile='candidate/src/'+name)
    (OUT/'candidate.patch').write_text(''.join(patches))
    records=[]
    for d in (base,cand):
        r=subprocess.run(['bash','build.sh'],cwd=d,capture_output=True,text=True)
        records.append(dict(command=['bash','build.sh'],cwd=str(d),exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,r.stderr
    for name,extra in [('check',['-O2']),('check-san',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
        cmd=['gcc','-std=c11','-D_POSIX_C_SOURCE=200809L','-pthread',*extra,'-I',str(cand/'src'),str(HERE/'check.c'),str(cand/'src/board.c'),str(cand/'src/movemodel.c'),'-lm','-o',str(HERE/'build'/name)]
        r=subprocess.run(cmd,capture_output=True,text=True);records.append(dict(command=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,r.stderr
    for d in (base,cand):
        main=(d/'src/main.c').read_text()
        guards='static const int piece_pawns[6] = {1, 3, 3, 5, 9, 0};\nstatic int dual_guard = '+str(int(d==cand))+';\n'
        for fn in ('queen_risks','king_risks'):
            start=main.index('static void '+fn+'(');brace=main.index('{',start);level=1;end=brace+1
            while level:
                level+=(main[end]=='{')-(main[end]=='}');end+=1
            guards+=main[start:end]+'\n'
        (d/'src/guard_reference.h').write_text(guards)
        cmd=['gcc','-std=c11','-D_POSIX_C_SOURCE=200809L','-pthread','-O2','-shared','-fPIC','-I',str(d/'src'),'-DDUAL='+str(int(d==cand)),str(HERE/'bridge.c'),str(d/'src/board.c'),str(d/'src/movemodel.c'),'-lm','-o',str(d/'filter.so')]
        r=subprocess.run(cmd,capture_output=True,text=True);records.append(dict(command=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,r.stderr
    pins={str(p.relative_to(ROOT)):sha(p) for d in (base,cand) for p in [*sorted((d/'src').glob('*')),d/'mist',d/'filter.so',d/'data/history.bin'] if p.is_file()}
    (OUT/'build.json').write_text(json.dumps(dict(records=records,pins=pins),indent=2)+'\n')
    print(json.dumps(dict(built=True,base=sha(base/'mist'),candidate=sha(cand/'mist'))))
if __name__=='__main__':main()
