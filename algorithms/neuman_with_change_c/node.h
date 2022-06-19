/* A node of a linked list */
#ifndef _NODE_H
#define _NODE_H

typedef struct linked_list {
	/* Assumes all values are 1 so there is no need to save actual value */
	int original_col;
	int col_cur;
	struct linked_list *next;
} node;

#endif /* _NODE_H */
