#include <math.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

#include "group.h"
#include "helpers.h"
#include "spmat.h"

/* Push a group to a linked-list of groups */
void push(group **G, node *n, int group_size) {
	group *new_head = malloc(sizeof(group));
	if (new_head == NULL) {
		print_and_exit(1, "Error: Failed to create new group.\n");
	}
	new_head->head = n;
	new_head->size = group_size;
	new_head->next = (group*)(*G);
	*G = new_head;
}

/* Pop a group out of a linked-list of groups */
node* pop(group **G) {
	group *prv_head = *G;
	node *node_head = prv_head->head;
	*G = prv_head->next;
	free(prv_head);
	return node_head;
}

/* Push a matrix to a linked-list of matrices */
void mat_push(mat_group **G, spmat *m) {
	mat_group *new_head = malloc(sizeof(mat_group));
	if (new_head == NULL) {
		print_and_exit(1, "Error: Failed to create new mat_group.\n");
	}
	new_head->head = m;
	new_head ->next = (*G);
	*G = new_head;
}

/* Pop a matrix out of a linked-list of matrices */
spmat *mat_pop(mat_group **G) {
	mat_group *prv_head = *G;
	spmat *mat_head = prv_head->head;
	*G = prv_head->next;
	free(prv_head);
	return mat_head;
}

/* Print all the groups to path; number of groups and then size of group and group's elements for each group */
void print_groups(group **G, char *path) {
	int counter = 0;
	group *temp;
	FILE *out = fopen(path,"wb");
	int *vertex_curr, *vertex_names;

	if (out == NULL) {
		print_and_exit(1, "Error: Failed to open file for writing results.\n");
	}

	/* Count the number of groups and write it to the file */
	for (temp = *G; temp != NULL; temp = temp->next) {
		counter++;
	}
	fwrite(&counter, sizeof(int), 1, out);

	/* For each group count its element and then write their number and them to the file */
	for (temp = *G; temp != NULL; temp = temp->next) {
		node *temp_head;
		vertex_names = malloc(temp->size * sizeof(int));
		if (vertex_names == NULL) {
			print_and_exit(1, "Error: Failed to create name vector.\n");
		}

		vertex_curr = vertex_names;
		for (temp_head = temp->head; temp_head != NULL; temp_head = temp_head->next) {
			*vertex_curr = temp_head->original_col;
			vertex_curr++;
		}
		fwrite(&(temp->size), sizeof(int), 1, out);
		fwrite(vertex_names, sizeof(int), temp->size, out);
		free(vertex_names);
	}
	fclose(out);
}

/* Free all the groups inside G, including G itself */
void free_group(group **G) {
	group *curr_group = *G, *prv_group;
	while (curr_group != NULL) {
		node *curr_node = curr_group->head, *prv_node;
		while (curr_node != NULL) {
			prv_node = curr_node;
			curr_node = curr_node->next;
			free(prv_node);
		}
		prv_group = curr_group;
		curr_group = curr_group->next;
		free(prv_group);
	}
	free(G);
}
