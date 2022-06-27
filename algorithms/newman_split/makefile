FLAGS = -ansi -Wall -Wextra -Werror -pedantic-errors
LIBS = -lm

all: cluster
clean:
	rm -rf *.o cluster

cluster: divide_group.o eigen.o group.o main.o spmat.o
	gcc divide_group.o eigen_vector.o group.o main.o spmat.o -o cluster $(LIBS)

main.o: main.c divide_group.h eigen_vector.h group.h helpers.h node.h spmat.h
	gcc $(FLAGS) -c main.c

spmat.o: spmat.c eigen_vector.h group.h helpers.h node.h spmat.h
	gcc $(FLAGS) -c spmat.c

eigen.o: eigen_vector.c eigen_vector.h helpers.h node.h spmat.h
	gcc $(FLAGS) -c eigen_vector.c

group.o: group.c eigen_vector.h group.h helpers.h node.h spmat.h
	gcc $(FLAGS) -c group.c

divide_group.o: divide_group.c divide_group.h eigen_vector.h helpers.h spmat.h
	gcc $(FLAGS) -c divide_group.c
