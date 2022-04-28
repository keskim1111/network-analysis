#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <math.h>

#include "divide_group.h"
#include "eigen_vector.h"
#include "helpers.h"
#include "spmat.h"

#define IS_POSITIVE(X) ((X) > 0.00001)

/* Put the value num in each element of the vector s */
void make_vector_to_num(double *s, int size, double num) {
	double *end = s + size;
	for (;s < end; s++) {
		*s = num;
	}
}

/* Check if a certain group can be divide to two groups according to algorithm 2. update vector s so it represents the best division */
void find_initial_division(spmat *A, double *s) {
	double eigen_value, vec_res;
	double *result = malloc(A->n * sizeof(double));
	if (result == NULL) {
		print_and_exit(1, "Error: Failed to allocate space for result vector.\n");
	}

	A->find_s_vector(A, s, &eigen_value);
	A->mult(A, s, result, 0);
	vec_res = vector_mult(s, result, A->n);

	free(result);

	if (eigen_value == 0 || vec_res < 0) {
		make_vector_to_num(s, A->n, 1);
	}
}

/* Split a linked-list to two linked-lists according to vector s */
void split_list(node *curr, double *s, node **g1, node **g2, int *n1, int *n2) {
	node *g1_curr = NULL, *g2_curr = NULL;

	for (; curr != NULL; curr = curr->next, s++) {
		if (*s == 1) {
			(*n1)++;
			if (g1_curr == NULL) {
				*g1 = g1_curr = curr;
			} else {
				g1_curr->next = curr;
				g1_curr = g1_curr->next;
			}
		} else {
			(*n2)++;
			if (g2_curr == NULL) {
				*g2 = g2_curr = curr;
			} else {
				g2_curr->next = curr;
				g2_curr = g2_curr->next;
			}
		}
	}

	if (g1_curr != NULL) {
		g1_curr->next = NULL;
	}
	if (g2_curr != NULL) {
		g2_curr->next = NULL;
	}
}

/* Copy the array from to the array to */
void copy_array(double *from, double *to, int size) {
	double *end = from + size;
	for (; from < end; from++, to++) {
		*to = *from;
	}
}

/* Calculate the new result of A*s using the fact that there's only one change */
void change_mult_by_one(spmat *A, double *result, double *v, int index) {
	node *row = (A->private)[index];
	int *k = A->k, i, sign = v[index], k_index = k[index], m = A->M;

	for (i = 0; i < A->n; i++, result++, k++) {
		if (row != NULL && row->col_cur == i) {
			*result += 2 * sign * (1 - ((*k * k_index)/((double)m)));
			row = row->next;
		} else {
			*result -= 2 * sign * ((*k * k_index)/((double)m));
		}
		if (i == index) {
			*result -= 2 * sign * ((A->sum_of_rows)[i]);
		}
	}
}

/* Find a better division according to algorithm 4 */
void find_optimal_division(spmat *A, double *s) {
	int i = 0, j = 0, index_max_state = 0, counter = 0, kj = 0;
	double *unmoved = malloc(sizeof(double) * A->n);
	double score = 0, max_score = 0, delta_Q = 0;
	double *max_s = malloc(sizeof(double) * A->n), *result = malloc(sizeof(double) * A->n);
	if (unmoved == NULL || max_s == NULL || result == NULL) {
		print_and_exit(1, "Error: malloc had failed\n");
	}
	do {
		int max_j = 0;
		double total_delta_Q = 0, max_total_delta_Q = 0;

		make_vector_to_num(unmoved, A->n, 0);
		copy_array(s, max_s, A->n);
		A->mult(A, s, result, 0);

		for (i = 0; i < A->n; i++) {
			for (counter = 0, j = 0, max_score = 0; j < A->n; j++) {
				if (!unmoved[j]) {
					kj = (A->k)[j];
					score = 4 * (-s[j] * result[j] - (((kj * kj)/(double)A->M) + (A->sum_of_rows)[j]));
					if (IS_POSITIVE(score - max_score) || counter == 0) {
						max_score = score;
						max_j = j;
					}
				counter++;
				}
			}
			s[max_j] *= -1;
			unmoved[max_j] = 1;
			change_mult_by_one(A, result, s, max_j);

			total_delta_Q += max_score;
			if (total_delta_Q > max_total_delta_Q) {
				max_total_delta_Q = total_delta_Q;
				index_max_state = i;
				copy_array(s, max_s, A->n);
			}
		}
		copy_array(max_s, s, A->n);

		if (index_max_state == (A->n)-1) {
			delta_Q = 0;
		} else {
			delta_Q = max_total_delta_Q;
		}
	}
	while (IS_POSITIVE(delta_Q));
	free(result);
	free(max_s);
	free(unmoved);
}

/* Divide a group of verteces, regarding to the division that maximize the modularity */
void divide_group(mat_group **mat_list, group **P, group **O, int lp_critical) {
	spmat *A = mat_pop(mat_list);
	node *orig_group = pop(P);
	double *s = malloc(A->n * sizeof(double));
	node *g1 = NULL, *g2 = NULL;
	int n1 = 0, n2 = 0;
	if (s == NULL) {
		print_and_exit(1, "Error: malloc had failed\n");
	}
	find_initial_division(A, s);

	find_optimal_division(A, s);
	split_list(orig_group, s, &g1, &g2, &n1 ,&n2);

	/* adding to O when other group is empty or size is <= lp_critical*/
	if (n1 == 0 || (n2 <= lp_critical && n2 >= 1) ) {
		printf("pushing to O group g2 of size %d\n", n2);
		push(O, g2, n2);
	}
	if (n2 == 0 || (n1 <= lp_critical && n1 >= 1)) {
		printf("pushing to O group g1 of size %d\n", n1);
		push(O, g1, n1);
	}
	
	/* adding to P when size is > lp_critical*/
	if (n1 > lp_critical && n2 > 0) {
		spmat *sub1  = spmat_allocate_list(n1, A->M);
		spmat_sub(A, sub1, g1);
		push(P, g1, n1);
		mat_push(mat_list, sub1);
	}
	if (n2 > lp_critical && n1 > 0) {
		spmat *sub2  = spmat_allocate_list(n2, A->M);
		spmat_sub(A, sub2, g2);
		push(P,g2, n2);
		mat_push(mat_list, sub2);
	}
	A->free(A);
	free(s);
}
