import pdb

import argparse

try:
    from solverRuns import run_solver, get_finite_witness
    from utils.SimpleTree import Formula
except:
    from encoding.solverRuns import run_solver, get_finite_witness
    from encoding.utils.SimpleTree import Formula

try:
    from utils.Traces import Trace, ExperimentTraces
except:
    from encoding.utils.Traces import Trace, ExperimentTraces

import logging



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", dest="loglevel", default="INFO")
    parser.add_argument("--candidate_formula_1", default="F(a)")
    parser.add_argument("--candidate_formula_2", default="F(&(a,b))")
    parser.add_argument("--trace_length", default = 5)

    args, unknown = parser.parse_known_args()

    """
    traces is 
     - list of different recorded values (traces)
     - each trace is a list of recordings at time units (time points)
     - each time point is a list of variable values (x1,..., xk) 
    """

    numeric_level = args.loglevel.upper()
    logging.basicConfig(level=numeric_level)

    trace_length = int(args.trace_length)

    f_1 = Formula.convertTextToFormula(args.candidate_formula_1)
    f_2 = Formula.convertTextToFormula(args.candidate_formula_2)
    difference_formula = Formula([encodingConstants.LOR,
                                 Formula([encodingConstants.LAND, f_1, Formula([encodingConstants.LNOT, f_2])]),
                                 Formula([encodingConstants.LAND, Formula([encodingConstants.LNOT, f_1]), f_2])
                                  ])

    #difference_formula = Formula(["&", f_1, Formula([encodingConstants.LNOT, f_2])])
    #difference_formula = Formula(["&", f_2, Formula([encodingConstants.LNOT, f_1])])

    # it is weird trace_length = trace_length +1 --> a mistake in the encoding that was reasons about number of states, rather than number of actions
    counterexample_witness = get_finite_witness(f=difference_formula, trace_length=trace_length)

    if counterexample_witness == "unsat":
        logging.error("Formulas {} and {} are equivalent (at least for all traces of length {}".format(f_1, f_2, trace_length))
    else:



        if counterexample_witness.evaluateFormulaOnTrace(difference_formula) == False:
            raise RuntimeError("looking for witness of satisfiability, but got a trace {} that is not a model for {}".format(cex, difference_formula))

        logging.info("the distinguishing trace is {}".format(counterexample_witness))



if __name__ == "__main__":
    main()

