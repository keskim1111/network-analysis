#include <math.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "eigen_vector.h"
#include "helpers.h"
#include "spmat.h"

#define epsilon 0.00001

/* Create a vector of size size_of_vector, with random elements between 0 to 1 */
double *initialize_random_vector(int size_of_vector) {
	double *vector, *current_cell, *end_of_vector;

	vector = (double*) malloc(sizeof(double) * size_of_vector);
	if (vector == NULL) {
		print_and_exit(1, "Error: Failed to create random vector.\n");
	}

	end_of_vector = vector + size_of_vector;

	srand(time(NULL));
	for (current_cell = vector; current_cell < end_of_vector; current_cell++) {
		*current_cell = (double)rand() / RAND_MAX;
	}

	return vector;
}

/* Check if a certain vector is an eigen vector by compare it to the last vector and check if the diffrences are small enough */
int is_eigen_vector(double *vector, double *new_vector, int size_of_vector) {
	double *end_of_vector = vector + size_of_vector;

	for (; vector < end_of_vector; vector++, new_vector++) {
		if (fabs(*vector - *new_vector) > epsilon) {
			return 0;
		}
	}

	return 1;
}

/* Divide the vector by its norm */
void normalize_vector(double *vec, int size_of_vector) {
	double norm = 0;
	double *temp_vector = vec, *end_vector = vec + size_of_vector;

	for (; temp_vector < end_vector; temp_vector++) {
		norm += *temp_vector * *temp_vector;
	}

	if (norm != 0) {
		norm = sqrt(norm);
		for (temp_vector = vec; temp_vector < end_vector; temp_vector++) {
			*temp_vector /= norm;
		}
	}
}

/* Switch between two pointers to arrays */
void swap(double **vector, double **new_vector) {
	double *temp;
	temp = *vector;
	*vector = *new_vector;
	*new_vector = temp;
}

/* Multiply two vectors and return the result */
double vector_mult(double *vector_a, double *vector_b, int size_of_vector) {
	double sum = 0, *end_of_vector = vector_a + size_of_vector;

	for (;vector_a < end_of_vector; vector_a++, vector_b++) {
		sum += *vector_a * *vector_b;
	}

	return sum;
}

/* Compute and return the dominant eigen vector, using power-iteration. update the eigen value accordingly */
double *calculate_dominant_eigen_vector(spmat *matrix, int size_of_vector, double *eigen_value) {
	int is_eigen = 0, number_of_iterations = 0, max_number_of_iterations = 0.5 * size_of_vector * size_of_vector + 20000 * size_of_vector + 200000;
	double *vector, *new_vector, double_bk;

	vector = initialize_random_vector(size_of_vector);
	new_vector = (double*) malloc(sizeof(double) * size_of_vector);
	if (new_vector == NULL) {
		print_and_exit(1, "Error: Failed to create temp vector.\n");
	}

	/* Power iteration */
	while (is_eigen == 0) {
		matrix->mult(matrix, vector, new_vector, 1);
		normalize_vector(new_vector, size_of_vector);
		is_eigen = is_eigen_vector(vector, new_vector, size_of_vector);
		swap(&vector, &new_vector);
		number_of_iterations++;
		if (number_of_iterations > max_number_of_iterations) {
			print_and_exit(1, "Error: Infinite loop.\n");
		}
	}

	/* Compute the eigen value */
	double_bk = vector_mult(vector, vector, size_of_vector);
	if (double_bk == 0) {
		*eigen_value = 0;
	} else {
		matrix->mult(matrix, vector, new_vector, 1);
		*eigen_value = vector_mult(vector, new_vector, size_of_vector) / double_bk;
	}
	free(new_vector);
	return vector;
}
