/* Actor-visible response student. Tokens: own PNBRQK=0..5, enemy=6..11,
 * unknown=12, visible empty=13. Black is rank-reflected before this call.
 * Moves: from | to<<6 | promotion<<12, promotion=0 none,1 N,2 B,3 R,4 Q. */
#ifndef ASTRA_VISIBLE_RESPONSE_H
#define ASTRA_VISIBLE_RESPONSE_H
#include <stdint.h>
#define ASTRA_RESPONSE_FLOATS 68417
float *astra_response_load(const char *path);
int astra_response_logits(const float *weights, const uint8_t tokens[64],
                          const uint16_t *moves, int count, float *out);
int astra_response_probs(const float *weights, const uint8_t tokens[64],
                         const uint16_t *moves, int count, double *out);
#endif
