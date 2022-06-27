/* Represent the B^[g] matrices using sparse matrix and vectors */
#ifndef _SPMAT_H
#define _SPMAT_H

#include "node.h"

typedef struct _spmat {
	/* Matrix size (n*n) */
	int n;

	/* Sum of all the degrees in the matrix */
	int M;

	/* The norm 1 of the matrix */
	double norm;

	/* The index i in the vector represents the degree of the vertex i */
	int *k;

	/* The original vertexes numbers from the input file */
	int *vertex_numbers;

	/* sum_of_rows[i] represent the sum of the row i, in the curr matrix */
	double *sum_of_rows;

	/* Adds row i to the matrix. Called before any other call,
	 * exactly n times in order (i = 0 to n-1) */
	void (*add_row)(struct _spmat *A, const int *row, int i);

	/* Frees all resources used by A */
	void (*free)(struct _spmat *A);

	/* Multiplies matrix A by vector v, into result (result is pre-allocated) */
	void (*mult)(const struct _spmat *A, const double *v, double *result, int for_eigen);

	/* Calculate the s-vector using a leading eigen vector of the matrix */
	void (*find_s_vector)(struct _spmat *A, double *result, double *eigen_value);

	/* Private field for inner implementation.
	 * Should not be read or modified externally */
	node **private;
} spmat;

/* Allocates a new linked-lists sparse matrix of size n */
spmat *spmat_allocate_list(int n, int sp_value);

/* Create a sub matrix according to a list of verteces */
void spmat_sub(const spmat *A, spmat *g1, node *g1_list);

#endif /* _SPMAT_H */
