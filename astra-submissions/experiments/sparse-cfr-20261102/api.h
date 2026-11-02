#ifndef ASTRA_SOLVER_API_H
#define ASTRA_SOLVER_API_H
#include <stddef.h>
typedef struct {
 void *(*create)(void);
 void (*destroy)(void *);
 int (*info)(void *,int,int);
 int (*node)(void *,int,int,int,double);
 void (*children)(void *,int,const int *,const double *,int);
 void (*finalize)(void *);
 void (*grow)(void *);
 void (*start)(void *,int,int);
 void (*expand)(void *,int,int,int,const int *,int);
 void (*step)(void *,int);
 size_t (*state)(void *,double *);
 void (*value)(void *,int,double);
 size_t (*storage)(void *);
 void *(*load)(const char *);
 void (*wrap)(void *);
 unsigned long long (*clears)(void *);
 void (*evaluate)(void *,double *);
} SolverAPI;
extern const SolverAPI base_api,fast_api;
#endif
