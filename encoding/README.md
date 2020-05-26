# traces2LTL

This branch implements learning LTL formulas from the set of positive examples (P) and a set of hints H.
Every hint is a variable with a weight, saying that a variable should be use in a specification.
The hints are encoded as soft constraints.

## Conclusions (so far)
 - for a given positive example (or a set of positive examples), one can think of the prefixes of that
 example as being negative. It holds only in the context of showing "what needs to be accomplished": is 
 something was accomplished by a prefix, the user would not bother showing the full trace
 
 - LTL is not suitable for describing what needs to be accomplished (more detailed discussion [here](discussions/DSLTL.md)) 
 so it needs to be restricted to be usable

 
## Setup
- setup a virtualenvironment for python 3.6 ([link](http://virtualenvwrapper.readthedocs.io/en/latest/)) and activate it (`workon ...`)
- run `pip install -r requirements.txt` to qinstall all necessary python packages available from pip
- install Z3 with python bindings ([link](https://github.com/Z3Prover/z3#python))

## Running
- to test on a single example, run e.g. `python experiment.py --traces=traces/dummy.json --test_sat_method --max_num_formulas=20`.
That will learn on the examples defined in the file `traces/dummy.json`. If you want to test it on a different file,
add it to the argument list, e.g. ` python experiment.py --traces=traces/anotherFile.json --test_sat_method`

### Experiment Trace File Format
 Options are specified in the JSON format. (Don't forget commas between every two properties!)

The properties to specify are:

   - literals: propositional variables that will be part of positive or negative traces (not obligatory. If omitted, will be filled by everything occurring in traces)
   - positive: traces (paths) that the formula should model. They are formatted as the initial and the lasso part, separated by a vertical bar (|). Both parts consist of timesteps separated by a semi-colon (;). Each timestep contains the literals (propositional variables) that hold true in it, separated by a comma (,). If none of the literals is true in a timestep, it should be either empty, or a reserved word "null".
   - hints: a list of propositional variables that should be a part of the formula together with the weight (how confident
   we are that is the case)
   - number-of-formulas: how many formulas to find (counts when to stop searching, even if none is found that implies negations of all safety restrictions)
   - max-depth-of-formula: maximum depth of any formula found by flie (default: 5)
   - operators: a list of LTL operators allowed in a formula (default: ["F", "->", "&", "|", "U", "G", "X"])
   
An example file is [here](traces/dummy.json) 


 
