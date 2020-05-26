import pdb

import argparse
import itertools

try:
    from solverRuns import get_finite_witness
    from utils.SimpleTree import Formula
    import encodingConstants
    from . import constants
except:
    from encoding.solverRuns import get_finite_witness
    from encoding.utils.SimpleTree import Formula
    from encoding import encodingConstants
    import constants


try:
    from utils.Traces import Trace, ExperimentTraces
except:
    from encoding.utils.Traces import Trace, ExperimentTraces

from logger_initialization import stats_log

from world import World

import logging


def get_path(f, wall_locations, water_locations, robot_location, items_locations=None):
    f = Formula.convertTextToFormula(f)

    for tr in itertools.chain(range(constants.MIN_FINE_RANGE, constants.MAX_FINE_RANGE, constants.STEP_FINE_RANGE),
                              range(constants.MIN_COARSE_RANGE, constants.MAX_COARSE_RANGE, constants.STEP_COARSE_RANGE)):

        disambiguation = get_finite_witness(f=f, wall_locations=wall_locations, trace_length=tr, water_locations=water_locations, robot_position=robot_location, items_locations=items_locations)

        if disambiguation == "unsat":
            continue
        else:
            (disambiguation_example, init_world, path) = disambiguation
            return path
    return False

def disambiguate(f_1, f_2, wall_locations=[], min_trace_length = None, max_trace_legnth = None, step = None, all_vars_to_consider = [], testing=False):

    stats_log.debug("disambiguation between {} and {}".format(f_1, f_2))
    if min_trace_length is None:
        min_trace_length = constants.MIN_RANGE_DISAMBIGUATION
    if max_trace_legnth is None:
        max_trace_legnth = constants.MAX_RANGE_DISAMBIGUATION
    if step is None:
        step = constants.STEP_DISAMBIGUATION


    for tr_length in range(min_trace_length, max_trace_legnth, step):
        difference_formula = Formula([encodingConstants.LOR,
                                      Formula([encodingConstants.LAND, f_1, Formula([encodingConstants.LNOT, f_2])]),
                                      Formula([encodingConstants.LAND, Formula([encodingConstants.LNOT, f_1]), f_2])
                                      ])

        #difference_formula = Formula(["&", f_1, Formula([encodingConstants.LNOT, f_2])])
        #difference_formula = Formula(["&", f_2, Formula([encodingConstants.LNOT, f_1])])


        # if tr_length > 8:
        #     pdb.set_trace()

        disambiguation = get_finite_witness(f = difference_formula, trace_length=tr_length, wall_locations = wall_locations, testing=testing)

        if disambiguation == "unsat":
            continue
        elif disambiguation == constants.UNKNOWN_SOLVER_RES:
            return disambiguation, disambiguation, disambiguation
        else:
            (disambiguation_example, init_world, path) = disambiguation
            logging.debug("+=+=+=++++ disambiguation example is {}".format(disambiguation_example))
            if disambiguation_example.evaluateFormulaOnTrace(difference_formula) == False:
                raise RuntimeError(
                    "looking for witness of satisfiability, but got a trace {} that is not a model for {}".format(
                        disambiguation_example, difference_formula))


            w = World(worldDescriptionJson = init_world, json_type=1)
            logging.debug("the distinguishing sequence of actions is {}".format(path))
            # emitted_path = w.execute_and_emit_events(path)
            # logging.debug("+=+=+=++++ emitted path is is {}".format(emitted_path))

            logging.debug("distinguishing between {} and {}".format(f_1, f_2))
            logging.debug("the initial world is {}".format(w))


            logging.debug("the distinguishing traces are {}".format(disambiguation_example))
            logging.debug("\n\n====\n\n")
            return w, path, disambiguation_example
    logging.error("Could not find a path disambiguating between {} and {}".format(f_1, f_2))
    return None, None, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", dest="loglevel", default="INFO")
    parser.add_argument("--test_file", default="experiments/data/test1.txt")
    parser.add_argument("--max_trace_length", default = 5)
    parser.add_argument("--min_trace_length", default=3)


    args, unknown = parser.parse_known_args()

    """
    traces is 
     - list of different recorded values (traces)
     - each trace is a list of recordings at time units (time points)
     - each time point is a list of variable values (x1,..., xk) 
    """

    numeric_level = args.loglevel.upper()
    logging.basicConfig(level=numeric_level)

    max_trace_length = int(args.max_trace_length)
    min_trace_length = int(args.min_trace_length)

    with open(args.test_file) as test_file:
        for line in test_file:
            [f_1_string, f_2_string] = line.split(";")

            f_1 = Formula.convertTextToFormula(f_1_string)
            f_2 = Formula.convertTextToFormula(f_2_string)



            disambiguate(f_1, f_2, min_trace_length, max_trace_length, 1)





if __name__ == "__main__":
    main()

