/* Separate a group into two groups if possible by modularity */
#ifndef _DIVIDE_GROUP_H
#define _DIVIDE_GROUP_H

#include "group.h"

/* Do one iteration of the dividing algorithm */
void divide_group(mat_group **mat_list, group **P, group **O);

#endif /* _DIVIDE_GROUP_H */
