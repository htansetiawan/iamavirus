#include <stdint.h>
#include <stddef.h>
typedef struct {double key;uint32_t index;} Ranked;
#include "observe.h"

int main(void) {
    Ranked r[3]={{1,0},{2,1},{3,2}};
    struct Row {uint64_t padding;float lw;uint32_t trailing;} w[3]={{123,-.22314355f,8},{456,-1.89711998f,9},{789,-2.99573227f,10}};
    Ranked before[3];memcpy(before,r,sizeof r);unsigned char original[sizeof w];memcpy(original,w,sizeof w);
    astra_cap_observe(0,3,2,r,w,sizeof(w[0]),offsetof(struct Row,lw));
    astra_cap_observe(1,3,2,r,NULL,sizeof(float),0);
    /* Repeated events are deliberately not exported; no duplicate path. */
    astra_cap_observe(0,3,2,r,w,sizeof(w[0]),offsetof(struct Row,lw));
    return memcmp(before,r,sizeof r) || memcmp(original,w,sizeof w);
}
