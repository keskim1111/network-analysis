/* Calculate the dominant eigen vector and its eigen value */
#ifndef _EIGEN_VECTOR_H
#define _EIGEN_VECTOR_H

#include "spmat.h"

/* Create new vector of a given size with random values */
double *initialize_random_vector(int size_of_vector);

/* Check if a given vector is an eigen vector */
int is_eigen_vector(double *vector, double *new_vector, int size_of_vector);

/* Swap the pointers of two given vectors */
void swap(double **vector, double **new_vector);

/* Calculate eigen vector using power iteration method */
double *calculate_dominant_eigen_vector(spmat *matrix, int size_of_vector, double *eigen_value);

/* Calculate vector multiplication */
double vector_mult(double *vector_a, double *vector_b, int size_of_vector);

#endif /* _EIGEN_VECTOR_H */
