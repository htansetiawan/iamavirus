/* Small FP32 leaf evaluator. Parameters follow the explicit export order in
 * native_check.py. No Python, ONNX, allocation or GPU on the inference path.
 * Inputs: 64 x (piece, own visible, other visible, castle rook, raw EP).
 */
#include <stdint.h>

float fow_student_logit(const float *w, const uint8_t *x, uint8_t half) {
    const float *piece=w;
    const float *vision=piece+64*13*128;
    const float *castle=vision+64*4*128;
    const float *ep=castle+64*128;
    const float *bias=ep+64*128;
    const float *half_weight=bias+128;
    const float *hidden=half_weight+128;
    const float *hidden_bias=hidden+32*128;
    const float *out=hidden_bias+32;
    const float out_bias=out[32];
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
    float z=out_bias;
    for (int k=0;k<32;++k)z+=out[k]*mid[k];
    return z;
}

double fow_student_batch(const float *w,const uint8_t *x,const uint8_t *h,int n,int repeats) {
    double checksum=0;
    for (int r=0;r<repeats;++r)
        for (int i=0;i<n;++i)checksum+=fow_student_logit(w,x+320*i,h[i]);
    return checksum;
}
