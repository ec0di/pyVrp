# VRPTWController
> VRPTWController is used to run and calculate score for the 12th DIMACS Implementation Challenge: VRPTW track. Specified in [Competition Rules](http://dimacs.rutgers.edu/files/8516/3848/0275/VRPTW_Competition_Rules.pdf).

## Installation

Linux, MacOS & OpenBSD:

```sh
git clone https://github.com/laser-ufpb/VRPTWController
cd VRPTWController
mkdir build
cd build
cmake ..
make
```

Testing the Controller with a dummy solver:

```sh
make test
```

The output will be at `build/` as `DIMACS-VRPTW-Dummy-R108.out`.

## Usage example

### How to run:
```sh
./VRPTWController <Competitor ID> <Instance path> <CPU mark> <Time limit> <Instance BKS> <If BKS is optimal [0/1]> <Path to solver>
```

### Example:
```sh
./VRPTWController Wolverine R108.txt 2064 1800 932.1 1 Solver1
```

### How to run the instances:
Generating the script:
```sh
sh genScript1.sh <Competitor ID> <CPU mark> <Solver path> > VRPTW-Script1.sh
```
Running the instances:
```sh
sh VRPTW-Script1.sh
```

to run all the instances, you also have to run the scripts genScript2.sh and genScript3.sh.

### Example:
```sh
sh genScript1.sh Wolverine 2064 Solver1 > VRPTW-Script1.sh
sh VRPTW-Script1.sh
```
_For more examples and usage, please refer to the [Competition Rules](http://dimacs.rutgers.edu/files/8516/3848/0275/VRPTW_Competition_Rules.pdf)._

### How to call the solver indirectly via shell script
Suppose a file named <i>solver</i> has the following content:
```sh
#!/usr/bin/env bash
./real-solver $1 $2 
```
Therefore, you can use <i>solver</i> (after calling <i>chmod +x solver</i>) instead of the original executable file <i>real-solver</i> (which could have other command-line arguments in addition to the two defined in the challenge rules). 

## Meta

Bruno Passeti – bruno@bravadus.com.br (UFPB)

Rodrigo Ramalho – rodrigo@bravadus.com.br (UFPB)

Distributed under the MIT license. See ``LICENSE`` for more information.
