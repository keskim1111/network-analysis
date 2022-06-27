#include <math.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "eigen_vector.h"
#include "group.h"
#include "helpers.h"
#include "node.h"
#include "spmat.h"

/* Calculate the s-vector using a leading eigen vector of the matrix */
void find_s_vector(spmat *A, double *result, double *eigen_value) {
	int n = A->n;
	double *end_of_vector = result + n;
	double *eigen_vector = calculate_dominant_eigen_vector(A, n, eigen_value);
	double *curr_cell = eigen_vector;

	*eigen_value -= A->norm;
	for (; result < end_of_vector; result++, curr_cell++) {
		if (*curr_cell > 0) {
			*result = 1;
		} else {
			*result = -1;
		}
	}
	free(eigen_vector);
}

/* Compute norm 1 of matrix A */
void compute_norm(spmat *A) {
	int i, j, n = A->n, *k = A->k, M = A->M;
	double sum_rows = 0, fi = 0, max_row = 0, kij;
	node **private = A->private;
	node *row = NULL;
	for (i = 0; i < n; ++i, sum_rows = 0, fi = 0) {
		for (j = 0, row = private[i]; j < n; ++j) {
			kij = (k[i] * k[j] / (double)M);

			if (row == NULL || j < row->col_cur) {
				fi -= kij;
				if (i != j) {
					sum_rows += kij;
				}
			} else {
				fi += (1 - kij);
				if (i != j) {
					sum_rows += fabs(1 - kij);
				}
				row = row->next;
			}
		}
		sum_rows += fabs(-(k[i]*k[i]/(double)M) - fi);
		if (sum_rows > max_row) {
			max_row = sum_rows;
		}
	}
	A->norm = max_row;
}

/* Compute the fig values of matrix A */
void compute_fig(spmat *A) {
	int i, n = A->n, M = A->M, *k = A->k, *k_curr;
	double sum_row = 0;

	for (k_curr = k; k_curr < k + n ;k_curr++) {
		sum_row += *k_curr;
	}
	sum_row /= (double)M;

	for (i = 0; i < n; ++i) {
		/*F_ig*/
		(A->sum_of_rows)[i] -= k[i] * sum_row;
	}
}

/* Add row i the matrix. called before any other call excluding spmat_allocate_list, exactly n times in order (i = 0 to n-1) */
void add_row_linked_list(spmat *A, const int *row, int i) {
	int col = 0, flag = 0, sum = 0;
	int *endrow = (int*)row + A->n;
	node *prv, *curr;
	node **linked_list = A->private;

	curr = malloc(sizeof(node));
	if (curr == NULL) {
		print_and_exit(1, "Error: Failed to create new row.\n");
	}
	linked_list[i] = curr;
	A->vertex_numbers[i] = i;

	for (; row < endrow; row++, col++) {
		if (*row != 0) {
			flag = 1;
			curr->original_col = col;
			curr->col_cur = col;
			curr->next = malloc(sizeof(node));
			if (curr->next == NULL) {
				print_and_exit(1, "Error: Failed to create new cell.\n");
			}
			prv = curr;
			curr = curr->next;
			sum++;
		}
	}

	(A->k)[i] = sum;
	(A->sum_of_rows)[i] = sum;

	free(curr);
	if (!flag) {
		linked_list[i] = NULL;
	} else {
		prv->next = NULL;
	}

	if (i == A->n - 1) {
		compute_norm(A);
		compute_fig(A);
	}
}

/* Multiply matrix A by vector v, into result (result is pre-allocated) */
void mult(const spmat *A, const double *v, double *result, int for_eigen) {
	int i, n = A->n, M = A->M, *k = A->k, *k_curr, *k_end;
	double sum = 0, sum_mult = 0;
	double *v_curr, *result_curr, *result_end;
	node *curr;
	node **arr = A->private;
	node **endarr = arr + n;

	/* Mult A alone - i.e result = Av */
	for (result_curr = result; arr < endarr; arr++, sum = 0, result_curr++) {
		curr = *arr;
		while (curr != NULL) {
			sum += v[curr->col_cur];
			curr = curr->next;
		}
		*result_curr = sum;
	}

	/* Mult k_fg - i.e afterwards result = B^v */
	k_end = k + n;
	for (v_curr = (double*) v, k_curr = k; k_curr < k_end; v_curr++, k_curr++) {
		sum_mult += *v_curr * *k_curr;
	}
	sum_mult /= (double)M;

	result_end = result + n;
	for (i = 0 ,result_curr = result; result_curr < result_end; ++result_curr, ++i) {
		*result_curr -= ((k[i] * sum_mult) + (A->sum_of_rows)[i] * v[i]);

		if (for_eigen) {
			*result_curr += A->norm * v[i];
		}
	}
}

/* Free all resources used by A */
void free_linked_list(spmat *A) {
	int n = A->n;
	node *prev, *curr;
	node **arr = A->private;
	node **endrow = arr + n;

	for (; arr < endrow; arr++) {
		for (curr = prev = *arr; curr != NULL;) {
			prev = curr;
			curr = curr->next;
			free(prev);
		}
	}
	free(A->private);
	free(A->sum_of_rows);
	free(A->vertex_numbers);
	free(A->k);
	free(A);
}

/* Allocates a new linked-lists sparse matrix of size n */
spmat *spmat_allocate_list(int n, int M){
	spmat *mat = malloc(sizeof(spmat));
	if (mat == NULL) {
		print_and_exit(1, "Error: Failed to create new matrix.\n");
	}

	mat->n = n;
	mat->M = M;
	mat->norm = 0;

	mat->k = calloc(sizeof(int), n);
	if (mat->k == NULL) {
		print_and_exit(1, "Error: Failed to create new matrix.\n");
	}

	mat->vertex_numbers = malloc(n * sizeof(int));
	if (mat->vertex_numbers == NULL) {
		print_and_exit(1, "Error: Failed to create new matrix.\n");
	}

	mat->sum_of_rows = calloc(n, sizeof(double));
	if (mat->sum_of_rows == NULL) {
		print_and_exit(1, "Error: Failed to create new matrix.\n");
	}

	mat->add_row = add_row_linked_list;
	mat->free = free_linked_list;
	mat->mult = mult;
	mat->find_s_vector = find_s_vector;

	mat->private = malloc(sizeof(node*) * n);
	if (mat->private == NULL) {
		print_and_exit(1, "Error: Failed to create new matrix.\n");
	}

	return mat;
}

void print_k2(int* k, int n) {
    int i;
    for (i=0; i<n; i++) {
        printf("(i=%d, k=%d) ", i, k[i]);
    }
    printf("\n");
}

/* Create a sub matrix according to a list of verteces */
void spmat_sub(const spmat *A, spmat *sub, node *sub_vertexes) {
	int i = 0, index, col_index = 0 ,counter = 0;
	node *vertexes_head = sub_vertexes, *vertexes_curr = sub_vertexes;

	for (index = 0; index < A->n; index++, vertexes_curr = sub_vertexes, col_index = 0, counter = 0) {
		node *new_row = malloc(sizeof(node));
		node *new_head = new_row;
		node *mat_row = (A->private)[index];
		node *prv = NULL;
		if (new_row == NULL) {
			print_and_exit(1, "Error: Failed to create new row.\n");
		}
		if (vertexes_head != NULL && (A->vertex_numbers)[index] == vertexes_head->original_col) {
			while (vertexes_curr != NULL && mat_row != NULL) {
				if (vertexes_curr->original_col == mat_row->original_col) {
					new_row->original_col = mat_row->original_col;
					new_row->col_cur = col_index;
					new_row->next = malloc(sizeof(node));
					if (new_row->next == NULL) {
						print_and_exit(1, "Error: Failed to create new cell.\n");
					}

					prv = new_row;
					new_row = new_row->next;
					vertexes_curr = vertexes_curr->next;
					mat_row = mat_row->next;
					col_index++;
					counter++;
				} else {
					if (vertexes_curr->original_col > mat_row->original_col) {
						mat_row = mat_row->next;
					}
					else {
						vertexes_curr = vertexes_curr->next;
						col_index++;
					}
				}
			}
			(sub->sum_of_rows)[i] = counter;
			if (prv != NULL) {
				(sub->private)[i] = new_head;
				prv->next = NULL;
			} else {
				(sub->private)[i] = NULL;
			}
			(sub->k)[i] = (A->k)[index];
			(sub->vertex_numbers)[i] = (A->vertex_numbers)[index];
			vertexes_head = vertexes_head ->next;
			i++;

		}
		free(new_row);
	}
	compute_norm(sub);
	compute_fig(sub);
}
