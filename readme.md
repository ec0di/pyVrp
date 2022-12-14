### VRP solved with OR-Tools using Column Generation
This project started out of this [article](https://medium.com/@sean-patrick-kelley/how-to-implement-column-generation-for-vehicle-routing-bdb8027c957f), 
and replaces Gurobi with OR-Tools (Free solver from Google) and makes it possible to throw any instance in the right format after the algorithm.

I want to highlight that I think the author (Sean Kelley) has done a really good job explaning Column Generation (CG) with a good example use-case on the Vehicle Route Problem (VRP).

### Installations
I recommend working in a virtual env, I use Conda myself, where you can specify python version (I use 3.9) and keep packages local.
To get started you only need python with a pip for installation purposes:

```
pip install -r requirements.txt
```

Note if you want to use SCIP, you need to install it, since it does not come precompiled with OrTools.
You can for instance install using https://github.com/scipopt/scip/blob/master/INSTALL.md

### Difference in implementation
The biggest difference in the implementation from that of [Sean Kelley](https://medium.com/@sean-patrick-kelley/how-to-implement-column-generation-for-vehicle-routing-bdb8027c957f) is that I currently only add 1 route for each run of the subproblem, whereas 
the Gurobi implementation potentially could add multiple. This seemed a bit harder to implement with OR-Tools, but I think
 it is definitely possible. There could be large improvements to the solutions by solving this.

I added route_costs specifically in a dict that I use for the objective function, since you cannot add variable contribution
to the objective in the definition of variables in OR-Tools as you can with Gurobi.

I created an initial solution that will work also for the instances where fleet_size < num_customers, which is most of the instances I guess.

Then I made an instance_reader class, so that I could easily transform Solomon instances to the same form used in input_dict.

Other than that there are smaller differences in the way you write up models / solvers for Gurobi and OR-Tools, which I implemented.


### My idea of Column Generation
Again, I recommend to read the article of Sean Patrick Kelley, but I will also try to give my view on how you can perceive column generation in a simple way.
* Write your original problem up as a Restricted Set Covering (RSC) problem, which is the master problem.
* Take advantage of LP relaxation of RSC + put all the constrains for a single route/plan onto the pricing problem.
* Solve LP of the master problem and use shadow values from the solution to find out if and how we can improve the solution by adding more routes/plans.
* While we can improve the solution to the master problem, solve the pricing problem and take the best routes/plans and add them to the master problem. Now resolve the master problem.
* When we cannot improve the master problem or time has run out, solve the RSC a final time, but without the LP relaxation. You now have your best column generated solution.

### Instances and testing
I found lots of problem instances from the Github Repo: https://github.com/laser-ufpb/VRPTWController/tree/master/src
These are added to this repo under instances. I chose to test the Solomon instances, which are also tested on this [webpage](http://www.bernabe.dorronsoro.es/vrp/index.html?/results/resultsSolom.htm)
. They have added solution values for 6 instances across multiple algorithms. I chose to compare with the original creater Solomon, which found quite effective solutions to the instances.

* LP solver: GLOP
* MIP solver: SCIP (but CBC yields almost identical results, SCIP slightly better)
* Time CG: 10 min
* Machine: Intel NUC11PHKi7 Phantom Canyon (2.8 GHz)

| Instance           | R1     | R2     | C1     | C2     | RC1    | RC2    | 
|--------------------|--------|--------|--------|--------|--------|--------| 
| Solomon (1987)     | 1436.7 | 1386.7 | 1343.7 | 797.6 | 1723.7 | 1651.1 | 
| Column Generation (2022) | 1676.8 | 1942.6 | 1302.2 | 1453.8 | 2416.7 | 1976.9 |
| Initial Solution Only | 2168.9 | 1942.6 | 1362.1 | 1453.8 | 2416.7 | 1976.9 |

Even though VRP probably is not the best suited case for a Column Generation approach, (since many effective meta 
heuristics exists that can be applied to this problem) we actually find okay solutions.
For at least half of the instances (R1, C1 and RC2) we are close to the performance of Solomon and for C1 instance, we actually outperform it.

We also see that in 4/6 cases our CG approach does not yield any improvement in the solution from the initial solution.

### Improvements to the model
* Find a way to retrieve N best routes for all subproblem optimizations.
* Look more into why new routes found are not improving obj even in LP space.
* Improve initial solution
* Tuning of parameter: pricing_problem_mip_gap
* Use OrTools Routing library
* Use a more effective programming language for OR tasks (for instance C# or C++)
