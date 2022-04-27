/* Represent group of nodes and group of matrices */
#ifndef _GROUP_H
#define _GROUP_H

#include "spmat.h"

typedef struct group {
	node *head;
	int size;
	struct group *next;
} group;

typedef struct mat_group {
	spmat *head;
	struct mat_group *next;
} mat_group;

/* Push a group to a linked-list of groups */
void push(group **G, node *n, int size);

/* Pop a group out of a linked-list of groups */
node *pop(group **G);

/* Print all the groups to path; number of groups and then size of group and group's elements for each group */
void print_groups(group **G, char *path);

/* Free all the groups inside G, including G itself */
void free_group(group **G);

/* Push a matrix to a linked-list of matrices */
void mat_push(mat_group **G, spmat *m);

/* Pop a matrix out of a linked-list of matrices */
spmat *mat_pop(mat_group **G);

#endif /* _GROUP_H */
