#ifndef ASTRA_RESPONSE_ADAPTER_H
#define ASTRA_RESPONSE_ADAPTER_H
#include "fow.h"
/* No full Position is accepted by the model adapter. */
int visible_pack(const char view[65], int side, const Move *moves, int n,
                 uint8_t tokens[64], uint16_t encoded[256]);
#endif
