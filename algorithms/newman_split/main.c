#include <math.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "divide_group.h"
#include "eigen_vector.h"
#include "group.h"
#include "helpers.h"
#include "spmat.h"

#define SEEK_CUR 1

/* Count the number of edges on the adjacency matrix */
int count_nonzeros(FILE *in) {
	int n, dim, nnz = 0, i, deg;
	rewind(in);
	n = fread(&dim, sizeof(int), 1, in);
	if (n != 1) {
		print_and_exit(1, "Error: Failed to read matrix dimension.\n");
	}

	for (i = 0; i < dim; i++) {
		n = fread(&deg, sizeof(int), 1, in);
		if (n != 1) {
			print_and_exit(1, "Error: Failed to read line degree.\n");
		}
		nnz += deg;
		n = fseek(in, deg * sizeof(int), SEEK_CUR);
		if (n != 0) {
			print_and_exit(1, "Error: Failed to go to next line.\n");
		}
	}
	return nnz;
}

/* Put the value 0 in each element of the vector */
void empty(int *vector, int size_of_vector) {
	int *end_of_vector = vector + size_of_vector;
	for (; vector < end_of_vector; vector++) {
		*vector = 0;
	}
}

/* Create the matrix by adding it row after row according to the input file */
void add_rows_to_matrix(spmat *matrix, FILE *in) {
	int dim, n, i, deg;
	int *row, *sp_row, *curr;
	rewind(in);

	n = fread(&dim, sizeof(int), 1, in);
	if (n != 1) {
		print_and_exit(1, "Error: Failed to read matrix dimension.\n");
	}
	row = malloc(dim * sizeof(double));
	if (row == NULL) {
		print_and_exit(1, "Error: Failed to create row buffer.\n");
	}
	sp_row = malloc(dim * sizeof(double));
	if (sp_row == NULL) {
		print_and_exit(1, "Error: Failed to create sparse row buffer.\n");
	}

	for (i = 0; i < dim; i++) {
		n = fread(&deg, sizeof(int), 1, in);
		if (n != 1) {
			print_and_exit(1, "Error: Failed to read line degree.\n");
		}
		empty(row, dim);
		if (deg != 0) {
			n = fread(sp_row, sizeof(int), deg, in);
			if (n != deg) {
				print_and_exit(1, "Error: Failed to read line.\n");
			}
			for (curr = sp_row; curr < sp_row + deg; curr++) {
				row[*curr] = 1;
			}
		}
		matrix->add_row(matrix, row, i);
	}

	free(row);
	free(sp_row);
}

/* Initialize the matrix */
spmat *create_matrix(FILE *in) {
	int n, nnz, dim;
	spmat *matrix;
	if (in == NULL) {
		print_and_exit(1, "Error: Failed to open matrix.\n");
	}
	n = fread(&dim, sizeof(int), 1, in);
	if (n != 1) {
		print_and_exit(1, "Error: Failed to read matrix dimension.\n");
	}
	if (dim == 0) {
		print_and_exit(1, "Error: Invalid graph - no vertices.\n");
	}
	nnz = count_nonzeros(in);
	if (nnz == 0) {
		print_and_exit(1, "Error: Invalid graph - no edges.\n");
	}
	matrix = spmat_allocate_list(dim, nnz);
	add_rows_to_matrix(matrix, in);
	return matrix;
}

void print_k(int* k, int n) {
    int i;
    for (i=0; i<n; i++) {
        printf("(i=%d, k=%d) ", i, k[i]);
    }
    printf("\n");
}

void initialize_P_and_mats(FILE *in, FILE *in_communities, group **P, mat_group **mats) {
    int n, i, j;
    int num_of_groups, current_group_size, current_node;
    spmat *A = create_matrix(in);
    spmat *sub1 = NULL;

    n = fread(&num_of_groups, sizeof(int), 1, in_communities);
    if (n != 1) {
		print_and_exit(1, "Error: Failed to read num_of_groups in communities.in file.\n");
	}

    for (i=0; i<num_of_groups; i++) {
        node *all_nodes = NULL;

        n = fread(&current_group_size, sizeof(int), 1, in_communities);

        if (n != 1) {
		    print_and_exit(1, "Error: Failed to read num_of_groups in communities.in file.\n");
	    }

        sub1 = spmat_allocate_list(current_group_size, A->M);
	    for (j=0; j<current_group_size; j++) {
	        node* new_node = NULL;
	        n = fread(&current_node, sizeof(int), 1, in_communities);

            if (n != 1) {
		        print_and_exit(1, "Error: Failed to read num_of_groups in communities.in file.\n");
	        }

            new_node = malloc(sizeof(node));
            if (new_node == NULL) {
                print_and_exit(1, "Error: Failed to create node list.\n");
            }
            new_node->original_col = current_node;
            new_node->next = all_nodes;
            all_nodes = new_node;
	    }

	    spmat_sub(A, sub1, all_nodes);

	    push(P, all_nodes, current_group_size);
	    mat_push(mats, sub1);
    }
    A->free(A);
}

int main(int argc, char *argv[]) {
	FILE *in = fopen(argv[1], "rb");
	FILE *in_communities = fopen(argv[2], "rb");
	mat_group **mats = malloc(sizeof(mat_group*));
	group **O = malloc(sizeof(group*));
	group **P = malloc(sizeof(group*));

	if (mats == NULL || O == NULL || P == NULL) {
		print_and_exit(1, "Error: malloc had failed\n");
	}
	if (argc != 4) {
		print_and_exit(1, "Error: Wrong number of arguments\n");
	}

	*P = NULL;
	*O = NULL;

	initialize_P_and_mats(in, in_communities, P, mats);

	while (*P != NULL) {
		divide_group(mats, P, O);
	}

	print_groups(O, argv[3]);
	free_group(O);
	free_group(P);
	fclose(in);
	free(mats);
	return 0;
}
