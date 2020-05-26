import pdb

import argparse
try:
    from solverRuns import run_solver
except:
    from encoding.solverRuns import run_solver

try:
    from utils.Traces import Trace, ExperimentTraces
except:
    from encoding.utils.Traces import Trace, ExperimentTraces

import logging
import json
from logger_initialization import stats_log

def helper(m, d, vars):
    tt = { k : m[vars[k]] for k in vars if k[0] == d }
    return tt


def start_experiment(experiment_specification, iteration_step=1, testing=False, trace_out=None, criterion=None):

    traces = ExperimentTraces()
    json_traces = json.load(open(experiment_specification))

    traces.readTracesFromFlieJson(json_traces)
    maxDepth = json_traces["max-depth-of-formula"]
    numFormulas = json_traces["number-of-formulas"]

    maxSolutionsPerDepth = json_traces["num-solutions-per-depth"]

    if testing:

        [formulas, timePassed, num_attempts, solver_solving_times] = run_solver(finalDepth=maxDepth, traces=traces,
                                                          maxNumOfFormulas=numFormulas,
                                                          step=iteration_step,
                                                          maxSolutionsPerDepth=maxSolutionsPerDepth, testing=testing,
                                                                                criterion=criterion)
    else:
        [formulas, timePassed] = run_solver(finalDepth=maxDepth, traces=traces,
                                                          maxNumOfFormulas=numFormulas,
                                                          step=iteration_step,
                                                          maxSolutionsPerDepth=maxSolutionsPerDepth, testing=testing)
    stats_log.info("initial candidates creation time: {}".format(timePassed))
    stats_log.debug("number of found formulas: {}".format(len(formulas)))
    stats_log.debug("found formulas: \n\t{}".format("\n\t".join([str(f) for f in formulas])))

    if not trace_out is None:
        traces.writeTracesToFile(trace_out)

    logging.debug("found formulas are {} and the time needed is {}".format(formulas, timePassed))
    if testing:
        return formulas, num_attempts, timePassed, solver_solving_times
    else:
        return formulas



 
def main():
    
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces", dest="tracesFileName", default="traces/dummy.trace")
    parser.add_argument("--max_depth", dest="maxDepth", default='8')
    parser.add_argument("--start_depth", dest="startDepth", default='1')
    parser.add_argument("--max_num_formulas", dest="numFormulas", default=3)
    parser.add_argument("--iteration_step", dest="iterationStep", default='1')
    parser.add_argument("--test_dt_method", dest="testDtMethod", default=False, action='store_true')
    parser.add_argument("--test_sat_method", dest="testSatMethod", default=False, action='store_true')
    parser.add_argument("--timeout", dest="timeout", default=600, help="timeout in seconds")
    parser.add_argument("--log", dest="loglevel", default="INFO")
    parser.add_argument("--positive_examples_only", dest="onlyPosExamples", default=False, action='store_true')
    parser.add_argument("--all_in_traces_file", dest="allInTraces", default=False, action='store_true')
    args,unknown = parser.parse_known_args()

    
    
    """
    traces is 
     - list of different recorded values (traces)
     - each trace is a list of recordings at time units (time points)
     - each time point is a list of variable values (x1,..., xk) 
    """
    
    numeric_level = args.loglevel.upper()
    logging.basicConfig(level=numeric_level)

    

    traces = ExperimentTraces()
    iterationStep = int(args.iterationStep)

    try:
        traces.readTracesFromFile(args.tracesFileName)
    except:
        jsonTraces = json.load(open(args.tracesFileName))
        traces.readTracesFromFlieJson(jsonTraces)

    if args.allInTraces == True:
        maxDepth = jsonTraces["max-depth-of-formula"]
        numFormulas = jsonTraces["number-of-formulas"]
        startDepth = jsonTraces["start-depth"]
    else:
        maxDepth = int(args.maxDepth)
        numFormulas = int(args.numFormulas)
        startDepth = int(args.startDepth)


    # solvingTimeout = int(args.timeout)
    # timeout = int(args.timeout)

    if args.onlyPosExamples == True:
        if len(traces.rejectedTraces) > 0:
            raise ValueError("option positive_examples_only was given, but there are negative traces as inputs")

        # add the biggest prefix as a negative trace
        for accTrace in traces.acceptedTraces:
            traces.rejectedTraces.append(Trace(traceVector=accTrace.traceVector[:-1]))


    if args.testSatMethod == True:
        [formulas, timePassed] = run_solver(finalDepth=maxDepth, traces=traces, maxNumOfFormulas = numFormulas, startValue=startDepth, step=iterationStep)
        logging.info("found formulas: "+str([f.prettyPrint(f) for f in formulas])+", timePassed: "+str(timePassed))
        
    
    # if args.testDtMethod == True:
    #
    #     [timePassed, numAtoms, numPrimitives] = run_dt_solver(traces=traces)
    #     logging.info("timePassed: {0}, numAtoms: {1}, numPrimitives: {2}".format(str(timePassed), str(numAtoms), str(numPrimitives)))
    #
    

            

if __name__ == "__main__":
    main()

