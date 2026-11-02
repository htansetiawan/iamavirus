/* Small FP32 leaf evaluator. Parameters follow the explicit export order in
 * native_check.py. No Python, ONNX, allocation or GPU on the inference path.
 * Inputs: 64 x (piece, own visible, other visible, castle rook, raw EP).
 */
#include <stdint.h>
#include <math.h>

static float bounded_residual(float a, float b, float z) {
    float s=fmaxf(-1.0f,fminf(1.0f,z/4.0f));
    return z+2.0f*tanhf((a+b*s)/2.0f);
}


float fow_residual_flat_logit(const float *w, const uint8_t *x, uint8_t half, float base_z) {
    const float *piece=w;
    const float *vision=piece+64*13*128;
    const float *castle=vision+64*4*128;
    const float *ep=castle+64*128;
    const float *bias=ep+64*128;
    const float *half_weight=bias+128;
    const float *hidden=half_weight+128;
    const float *hidden_bias=hidden+32*128;
    const float *out=hidden_bias+32;
    const float *out_bias=out+64;
    float acc[128]={0}, mid[32];
    for (int sq=0;sq<64;++sq) {
        const uint8_t *f=x+5*sq;
        const float *p=piece+(13*sq+f[0])*128;
        const float *v=vision+(4*sq+f[1]+2*f[2])*128;
        const float *c=castle+sq*128,*e=ep+sq*128;
        for (int j=0;j<128;++j)
            acc[j]+=p[j]+v[j]+(float)f[3]*c[j]+(float)f[4]*e[j];
    }
    const float h=(half>100?100:half)/100.0f;
    for (int j=0;j<128;++j) {
        float a=acc[j]+bias[j]+h*half_weight[j];
        acc[j]=a<0?0:a>1?1:a;
    }
    for (int k=0;k<32;++k) {
        float a=hidden_bias[k];
        for (int j=0;j<128;++j)a+=hidden[128*k+j]*acc[j];
        mid[k]=a<0?0:a>1?1:a;
    }
    float v[2]={out_bias[0],out_bias[1]};
    for(int j=0;j<2;j++)for(int k=0;k<32;k++)v[j]+=out[j*32+k]*mid[k];
    return bounded_residual(v[0],v[1],base_z);
}


double fow_residual_flat_batch(const float *w,const uint8_t *x,const uint8_t *h,
                              const float *z,int n,int repeats) {
    double sum=0;
    for(int r=0;r<repeats;r++)for(int i=0;i<n;i++)
        sum+=fow_residual_flat_logit(w,x+320*i,h[i],z[i]);
    return sum;
}
