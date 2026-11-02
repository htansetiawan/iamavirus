"""Deterministic native adaptation of the pinned 237/238 inference kernels."""
import subprocess
from common import HERE, OLD, QUERY


COMBINE='''
static float bounded_residual(float a, float b, float z) {
    float s=fmaxf(-1.0f,fminf(1.0f,z/4.0f));
    return z+2.0f*tanhf((a+b*s)/2.0f);
}
'''


def replace_once(text, before, after):
    assert text.count(before)==1,before
    return text.replace(before,after)


def build():
    directory=HERE/'build';directory.mkdir(exist_ok=True)
    q=(QUERY/'query_infer.c').read_text().split('double fow_query_batch(')[0]
    q=replace_once(q,'#include <stdint.h>','#include <stdint.h>\n'+COMBINE)
    q=replace_once(q,'+F+F+1;','+F+2*F+2;')
    q=replace_once(q,'uint8_t half) {','uint8_t half, float base_z) {')
    q=replace_once(q,'hidden[F], result;','hidden[F], result[2];')
    q=replace_once(q,'linear(hidden,w,w+F,&result,F,1);return result;',
        'linear(hidden,w,w+2*F,result,F,2);return bounded_residual(result[0],result[1],base_z);')
    q=q.replace('fow_query','fow_residual_query')
    f=(OLD/'student_infer.c').read_text().split('double fow_student_batch(')[0]
    f=replace_once(f,'#include <stdint.h>','#include <stdint.h>\n#include <math.h>\n'+COMBINE)
    f=replace_once(f,'uint8_t half) {','uint8_t half, float base_z) {')
    f=replace_once(f,'const float out_bias=out[32];','const float *out_bias=out+64;')
    f=replace_once(f,'float z=out_bias;\n    for (int k=0;k<32;++k)z+=out[k]*mid[k];\n    return z;',
        'float v[2]={out_bias[0],out_bias[1]};\n    for(int j=0;j<2;j++)for(int k=0;k<32;k++)v[j]+=out[j*32+k]*mid[k];\n    return bounded_residual(v[0],v[1],base_z);')
    f=f.replace('fow_student','fow_residual_flat')
    for name,text in [('query',q),('flat',f)]:
        text+='''
double fow_residual_NAME_batch(const float *w,const uint8_t *x,const uint8_t *h,
                              const float *z,int n,int repeats) {
    double sum=0;
    for(int r=0;r<repeats;r++)for(int i=0;i<n;i++)
        sum+=fow_residual_NAME_logit(w,x+320*i,h[i],z[i]);
    return sum;
}
'''.replace('NAME',name)
        (directory/(name+'.c')).write_text(text)
    library=directory/'residual.so'
    cmd=['gcc','-std=c11','-O3','-Wall','-Wextra','-Werror','-shared','-fPIC',
         str(directory/'flat.c'),str(directory/'query.c'),'-lm','-o',str(library)]
    r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
    return library,cmd
