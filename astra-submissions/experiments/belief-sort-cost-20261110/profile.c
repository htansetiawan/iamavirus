/* Delegate to the unchanged libc qsort; measure belief.c calls only. */
#include <inttypes.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

typedef struct {
    uint64_t calls, elements, max_elements, thread_ns, wall_ns;
} Bucket;
static Bucket buckets[3];
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

static uint64_t ns(clockid_t clock) {
    struct timespec t;
    clock_gettime(clock, &t);
    return (uint64_t)t.tv_sec * UINT64_C(1000000000) + (uint64_t)t.tv_nsec;
}

void astra_qsort(void *base, size_t n, size_t width,
                 int (*compare)(const void *, const void *)) {
    const uint64_t wall = ns(CLOCK_MONOTONIC);
    const uint64_t cpu = ns(CLOCK_THREAD_CPUTIME_ID);
    qsort(base, n, width, compare);
    const uint64_t cpu_elapsed = ns(CLOCK_THREAD_CPUTIME_ID) - cpu;
    const uint64_t wall_elapsed = ns(CLOCK_MONOTONIC) - wall;
    const int which = width == 24 ? 0 : width == 16 ? 1 : 2;
    pthread_mutex_lock(&lock);
    Bucket *b = &buckets[which];
    ++b->calls;
    b->elements += n;
    if (n > b->max_elements) b->max_elements = n;
    b->thread_ns += cpu_elapsed;
    b->wall_ns += wall_elapsed;
    pthread_mutex_unlock(&lock);
}

__attribute__((destructor)) static void report(void) {
    fprintf(stderr, "astra-sort-profile: {\"process_cpu_ns\":%" PRIu64 ",\"buckets\":[",
            ns(CLOCK_PROCESS_CPUTIME_ID));
    for (int i = 0; i < 3; ++i) {
        Bucket *b = &buckets[i];
        fprintf(stderr, "%s{\"width\":%d,\"calls\":%" PRIu64
                ",\"elements\":%" PRIu64 ",\"max_elements\":%" PRIu64
                ",\"thread_cpu_ns\":%" PRIu64 ",\"wall_ns\":%" PRIu64 "}",
                i ? "," : "", i == 0 ? 24 : i == 1 ? 16 : 4,
                b->calls, b->elements, b->max_elements, b->thread_ns, b->wall_ns);
    }
    fputs("]}\n", stderr);
}
