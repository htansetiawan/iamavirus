#include "sfeval.h"
#include <stdio.h>
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    const int ready = sf_start(argv[1]);
    printf("start=%d workers=%d\n", ready, sf_workers());
    sf_stop();
    return ready ? 0 : 1;
}
