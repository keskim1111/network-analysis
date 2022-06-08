from output_generator import *

if __name__ == '__main__':
    pass


"""
idea: there are some subgraphs that ilp takes long to finish. run orpaz-neuman partially, 
but also save the final result. Then - if there is a subgraph that ilp runs for longer
than X minutes - stop the run for this subgraph and put the neuman result instead
Another option is - if it runs too long - then just add that full subgraph as 1 community and dont continue to divide it
"""