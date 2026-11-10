/* Standalone mathematical primitive, not integrated with a playing filter.
 * Caller must supply exact observation-class IDs and mask only consistent
 * NONCAPTURING transitions eligible. We neither construct classes nor infer
 * legality. Copies old log-likelihoods by rank within each eligible class.
 * Two bounded mergesorts: worst-case O(n log n), O(n) scratch, n <= 256. */
#include <math.h>
#include <stdint.h>
#include <string.h>

#ifdef __cplusplus
extern "C" {
#endif

static int precedes(int i, int j, const uint32_t *group, const double *key) {
    if (group[i] != group[j]) return group[i] < group[j];
    if (key[i] != key[j]) return key[i] > key[j];
    return i < j;
}

static void sort_indices(int *index, int n, const uint32_t *group, const double *key) {
    int scratch[256];
    for (int width = 1; width < n; width *= 2) {
        for (int low = 0; low < n; low += 2 * width) {
            const int mid = low + width < n ? low + width : n;
            const int high = low + 2 * width < n ? low + 2 * width : n;
            int i = low, j = mid, at = low;
            while (i < mid && j < high)
                scratch[at++] = precedes(index[i], index[j], group, key) ? index[i++] : index[j++];
            while (i < mid) scratch[at++] = index[i++];
            while (j < high) scratch[at++] = index[j++];
        }
        memcpy(index, scratch, (size_t)n * sizeof(int));
    }
}

int astra_rank_reassign(int n, const uint32_t *group, const double *logp,
                       const double *ranking, const uint8_t *eligible, double *out) {
    if (n < 0 || n > 256) return -1;
    if (n == 0) return 0;
    if (!group || !logp || !ranking || !eligible || !out) return -1;
    int by_old[256], by_new[256], count = 0;
    double saved[256];
    for (int i = 0; i < n; ++i) {
        if (isnan(logp[i]) || logp[i] > 0 || eligible[i] > 1) return -1;
        if (eligible[i]) {
            if (isnan(ranking[i]) || ranking[i] == INFINITY) return -1;
            by_old[count] = by_new[count] = i;
            ++count;
        }
    }
    memcpy(saved, logp, (size_t)n * sizeof(double));
    sort_indices(by_old, count, group, saved);
    sort_indices(by_new, count, group, ranking);
    /* Snapshot before copying supports out == logp without a cycle hazard. */
    memcpy(out, saved, (size_t)n * sizeof(double));
    for (int k = 0; k < count; ++k) out[by_new[k]] = saved[by_old[k]];
    return 0;
}

#ifdef __cplusplus
}
#endif

#ifdef ASTRA_RANK_UNIT
#include <assert.h>
#include <stdio.h>
int main(void) {
    uint32_t group[256]; double old[256], score[256], out[256]; uint8_t eligible[256];
    assert(astra_rank_reassign(0, 0, 0, 0, 0, 0) == 0);
    assert(astra_rank_reassign(-1, 0, 0, 0, 0, 0) == -1);
    for (int n = 1; n <= 256; ++n) {
        for (int i = 0; i < n; ++i) {
            group[i] = (uint32_t)(i % 7); old[i] = -0.125 * i;
            score[i] = old[i]; eligible[i] = (uint8_t)(i % 3 != 0); out[i] = 123;
        }
        assert(astra_rank_reassign(n, group, old, score, eligible, out) == 0);
        assert(memcmp(old, out, (size_t)n * sizeof(double)) == 0);
        for (int i = 0; i < n; ++i) score[i] = -old[i];
        assert(astra_rank_reassign(n, group, old, score, eligible, out) == 0);
        for (int i = 0; i < n; ++i) {
            if (!eligible[i]) assert(memcmp(old + i, out + i, sizeof(double)) == 0);
            int before = 0, after = 0;
            if (eligible[i]) for (int j = 0; j < n; ++j) if (eligible[j] && group[j] == group[i]) {
                before += memcmp(old + i, old + j, sizeof(double)) == 0;
                after += memcmp(old + i, out + j, sizeof(double)) == 0;
            }
            assert(before == after);
        }
        assert(astra_rank_reassign(n, group, old, score, eligible, old) == 0);
        assert(memcmp(old, out, (size_t)n * sizeof(double)) == 0);
    }
    puts("256 lengths: identity, masked bits, per-class multiset and in-place checks pass");
    return 0;
}
#endif
