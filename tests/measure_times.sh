#!/bin/sh


NValues=(200 250 300 350)
kValues=(5 6 8 10)

touch times_log.txt
for i in ${!NValues[@]}; do
	printf "\n#####Curr N is ${NValues[$i]}#####\n" >> times_log.txt
	for j in ${!kValues[@]}; do
		printf "the params running are k = ${kValues[$j]} and n = ${NValues[$i]} and Random = --no-Random\n...\n"
		start=`date +%s`

		python3.8.5 -m invoke run ${kValues[$j]} ${NValues[$i]} --no-Random

		end=`date +%s`
		echo input k = ${kValues[$j]} and n = ${NValues[$i]} and Random = --Random.Execution time was $((end-start)) seconds.>> times_log.txt
		printf "\n the  k = ${kValues[$j]} and n = ${NValues[$i]} and Random = --no-Random run ended with $((end-start)) seconds"
		rm *mykmeanssp.cpython*


done
done
mv times_log.txt times_log_$( date '+%Y-%m-%d_%H-%M-%S' ).txt

