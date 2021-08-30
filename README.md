# Interactive Synthesis
This is a server that accepts a single example from a LTLTalk user
together with the corresponding natural language definitions, 
and tries to generalize it to a definition.


## Setting up the environment
 - create a virtual environment for python3 (for example, using [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/))
 - run `pip install -r requirements.txt`
 - run `export FLASK_APP=flask-routes.py` (or add it to the `.bashrc` file)

## Running
-  `flask run`. 
(The server will run on the port 5000 by default)

## Running experiments
This section covers running the experiments as presented in the paper [Interactive Synhtesis of Temporal Specifications from Examples and Natural Language](https://dl.acm.org/doi/10.1145/3428269).

### Tasks
Tasks (Table 1 in the paper) are listed in 
[interactive-synthesis/experiments/multiple_examples_experiments_worlds](/interactive-synthesis/experiments/multiple_examples_experiments_worlds) folder.

### RQ1
Run the script `/run.sh`.
Inside this script, there is a command
`python experiments/interaction_experiment.py --tests_definition_folder=experiments/multiple_examples_experiments_world 
--num_repetitions=5 --max_depth 4 --num_init_candidates 5 –-output=results.csv 
–ondensed_output=condensed_results.csv --optimizer_criterion=pareto --num_examples=1`

The command first specifies where to take the input data from (tests_definition_folder), 
how many times to repeat the experiment for each task (num_repetitions), 
what depth of the formula to use (max_depth), how many initial candidates to use (num_init_candidates) and
how many examples to take from the input for each tasks (num_examples. Here we take 1, but there are max 2 available in the input).
Note a slightly different way of specifying max_depth and num_init_candidates: these can be a list of numbers so the 
equality sign is not used (as will be used in following sections).
The results corresponding to Table2 are written in condensed_results.csv (the detailed version is in results.csv). 
 
### RQ2
- run the script `run_no_hints.sh`. It contains the same command as run.sh with additional option --no_hints
- the results will be in the files `condensedResultsNoHints.csv` and `resultsNoHints.csv` (or, specify a different file 
when running the command)


## Interacting with the whole system (frontent+backend)

### Setup
Install [frontend](https://github.com/mpi-sws-rse/ltltalk-frontend), 
[semantic parser](https://github.com/mpi-sws-rse/ltltalk-backend), 
and [interactive synthesis engine](https://github.com/mpi-sws-rse/ltltalk-interactive-synthesis) locally. To install each part, please follow the instructions in the corresponding repositories.


### RQ3
- run the script `run_vary_parameters.sh`. 
The script contains the command 
`python experiments/interaction_experiment.py --tests_definition_folder=experiments/multiple_examples_experiments_world 
--num_repetitions=5 --max_depth 1 3 5 7 --num_init_candidates 2 3 4 5 6 
--condensed_output=condensedResultsVaryingParameters.csv --output=resultsVaryingParameters.csv 
--optimizer_criterion=pareto --num_examples=1`
(the values for max_depth and num_init_candidates are changed with respect to run.sh) and run it. 
This will take a pretty long time as there are 10x4x5x5 experiments inside 
(number of tasks x values of depths x values of number of candidates x number of repetitions).




### Basic system functionality


In order to have a view of the overall system (as shown in Fig. 2 of the paper), do the following:
Terminal 1: 
 - navigate to the ltltalk-backend directory and run `./interactive/run @mode=ltltalk`

Terminal 2: 
 - navigate to interactive-synthesis directory 
 - run `workon ltlTalk' (to use the correct python virtual environment)
 - run `flask run'

Terminal 3:
 - navigate to the frontend directory
 - enter folder `voxelurn`
 - run `yarn start`

Terminal 1 runs the naturalization server (described in Section 5 of the paper). Terminal 2 runs the interactive synthesis server (described in Section 4 of the paper). Finally, Terminal 3 runs the frontend. Upon running `yarn start`, a firefox window should open. If this does not happen, visit `localhost:3000` in a browser.

Navigate to the Play tab of the frontend. (For the moment, disregard other tabs as they are not completely up to date.) To test the system, try the example from the paper:
 - write `take one red item from 7,4`
 - the robot will not know what is meant by that and will ask for clarification: do it using arrows and pressing P for picking (these instructions will be provided in the frontend as well)
 - the system will show a couple of demonstrations for which you have to judge whether or not they fit to the intended command. (This process is not deterministic so the number of questions can vary.)
 - once the process is finished, try `take every triangle item from 10, 8` . Now, the system should be able to parse it and execute the action.


