#ifndef ASTRA_OBSERVABLE_PROOF_H
#define ASTRA_OBSERVABLE_PROOF_H
#include <stdint.h>
/* Same actor-canonical tokens/actions as the frozen student. Inputs are
 * assumed to be permitted legal candidates. A 1 is a sufficient proof of
 * immediate king loss, not a complete risk assessment. Unknowns block proofs
 * of slider attacks. No hidden board or opponent view can enter this API. */
int observable_fatal(const uint8_t tokens[64], const uint16_t *moves, int n,
                     uint8_t *fatal, uint8_t *witness);
#endif
