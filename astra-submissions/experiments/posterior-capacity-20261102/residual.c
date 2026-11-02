/* Portable sparse deployment form; coefficient order matches the training mask. */
void residual_logits(const float *x, const float *base, int n,
                     const float *linear, const float *quadratic, float *out) {
    for (int r=0; r<n; ++r) {
        const float *v=x+26*r;
        int active[26], count=0;
        float delta=0;
        for (int i=0; i<26; ++i) if (v[i]!=0) {
            active[count++]=i; delta+=linear[i]*v[i];
        }
        for (int a=0; a<count; ++a) for (int b=a; b<count; ++b) {
            int i=active[a],j=active[b];
            delta+=quadratic[26*i+j]*v[i]*v[j];
        }
        out[r]=base[r]+delta;
    }
}
