import random

from utils import create_json_spec, convert_json_actions_to_world_format, convert_path_to_formatted_path
from utils import unwind_actions, get_literals
import nlp_helpers
from encoding.run_solver_tests import disambiguate, get_path
from encoding.utils.SimpleTree import Formula
from encoding.utils.Traces import Trace, ExperimentTraces
from world import World
from encoding.smtEncoding.dagSATEncoding import DagSATEncoding
import pdb
import json
import os
import logging
from copy import deepcopy
import constants
from logger_initialization import stats_log
from pytictoc import TicToc
from z3 import *


def create_candidates(nl_utterance, examples, testing=False, num_formulas=None, id=None, max_depth=None, criterion=None,
                      use_hints=True):
    t = TicToc()
    emitted_events_seq = []
    collection_of_negative = []
    pickup_locations = []
    all_locations = []

    if max_depth is None:
        max_depth = constants.CANDIDATE_MAX_DEPTH

    for ex in examples:
        context = ex["context"]
        path = ex["init-path"]
        test_world = World(context, json_type=2)
        (emitted_events, pickup_locations_ex, collection_of_negative_ex,
         all_locations_ex) = test_world.execute_and_emit_events(
            path)
        emitted_events_seq.append(emitted_events)
        collection_of_negative += collection_of_negative_ex
        pickup_locations += pickup_locations_ex
        all_locations += all_locations_ex

    pickup_locations = list(set(pickup_locations))
    all_locations = list(set(all_locations))

    t.tic()


    hintsWithLocations = nlp_helpers.get_hints_from_utterance(nl_utterance, pickup_locations, all_locations, emitted_events_seq)


    literals = get_literals(pickup_locations, all_locations)
    emitted_traces = [Trace.create_trace_from_events_list(demonstration_events, literals_to_consider=literals) for
                      demonstration_events in emitted_events_seq]
    negative_traces = [Trace.create_trace_from_events_list(derived_events, literals_to_consider=literals)
                       for derived_events in collection_of_negative]

    traces = ExperimentTraces(tracesToAccept=emitted_traces, tracesToReject=negative_traces, hints=hintsWithLocations)

    hints_report = ["{} --> {}".format(k, hintsWithLocations[k]) for k in hintsWithLocations]
    stats_log.debug("hints: \n\t{}".format("\n\t".join(hints_report)))
    
    if constants.EXPORT_JSON_TASK:
        os.makedirs("data", exist_ok=True)
        json_name = "data/" + id + ".json"
        create_json_spec(file_name=json_name, emitted_events_sequences=emitted_events_seq, hints=hintsWithLocations,
                         pickup_locations=pickup_locations, all_locations=all_locations,
                         negative_sequences=collection_of_negative, num_formulas=num_formulas, max_depth=max_depth)

    formula_generation_times = []
    results = []

    generation_tic = TicToc()
    generation_tic.tic()

    ltl_formula_encoder = DagSATEncoding(max_depth, traces, literals=literals, testing=testing,
                 hintVariablesWithWeights=traces.hints_with_weights, criterion=criterion)
    ltl_formula_encoder.encodeFormula()
    formula_generation_times.append(generation_tic.tocvalue())

    num_attempts = 0
    solver_solving_times = []

    # give 3 attempts more than the number of formulas, to cover for the cases when equivalent formulas are found
    while len(results) < num_formulas and num_attempts < num_formulas + 3:

        num_attempts += 1

        solverTic = TicToc()
        solverTic.tic()
        solverRes = ltl_formula_encoder.solver.check()
        solver_solving_times.append(solverTic.tocvalue())

        if solverRes == unsat:
            logging.info("unsat!")
            if constants.LOGGING_LEVEL == logging.DEBUG:
                if not os.path.exists("debug_files/"):
                    os.makedirs("debug_files/")
                solver_filename = "debug_files/" + str(num_attempts) + ".solver"
                with open(solver_filename, "w") as solver_file:
                    solver_file.write(str(ltl_formula_encoder.solver))

            continue

        elif solverRes == unknown:
            results = [constants.UNKNOWN_SOLVER_RES]
            break


        else:

            solverModel = ltl_formula_encoder.solver.model()
            found_formula_depth = solverModel[ltl_formula_encoder.guessed_depth].as_long()

            formula = ltl_formula_encoder.reconstructWholeFormula(solverModel, depth=found_formula_depth)
            table = ltl_formula_encoder.reconstructTable(solverModel, depth=found_formula_depth)
            logging.info("found formula {} of depth {}".format(formula.prettyPrint(), found_formula_depth))
            formula = Formula.normalize(formula)
            if constants.LOGGING_LEVEL == logging.DEBUG:
                os.makedirs("debug_models/", exist_ok=True)
                model_filename = "debug_models/" + str(num_attempts) + ".model"
                table_filename = "debug_models/" + str(num_attempts) + ".table"
                with open(table_filename, "w") as table_file:
                    table_file.write(str(table))
                with open(model_filename, "w") as model_file:
                    model = solverModel
                    for idx in range(len(model)):
                        model_file.writelines("{}: {}\n".format(model[idx], model[model[idx]]))

            logging.debug("normalized formula {}\n=============\n".format(formula))
            if formula not in results:
                results.append(formula)
                logging.info(
                    "added formula {} to the set. Currently we have {} formulas and looking for total of {}".format(
                        formula, len(results), num_formulas))

            block = []

            informative_variables = ltl_formula_encoder.getInformativeVariables(depth=found_formula_depth, model=solverModel)

            logging.debug("informative variables of the model:")
            for v in informative_variables:
                logging.debug("{}: {}".format(v, solverModel[v]))
                block.append(Not(v))
            logging.debug("===========================\n")
            logging.debug("blocking {}".format(block))
            ltl_formula_encoder.solver.add(Or(block))
    stats_log.info("number of initial candidates: {}".format(len(results)))
    stats_log.debug("number of candidates per depth: {}".format(constants.NUM_CANDIDATE_FORMULAS_OF_SAME_DEPTH))
    stats_log.info("number of attempts to get initial candidates: {}".format(num_attempts))
    stats_log.info("propositional formula building times are {}".format(formula_generation_times))


    return results, num_attempts, formula_generation_times, solver_solving_times


def update_candidates(old_candidates, path, decision, world, actions):
    collection_of_candidates = []
    collection_of_formulas = []

    if int(decision) == 1:
        formula_value = True
    elif int(decision) == 0:
        formula_value = False
    else:
        raise ValueError("got user decision different from 0 or 1, the value was {}".format(decision))

    # converted_path = convert_json_actions_to_world_format(deepcopy(world), path)
    converted_path = unwind_actions(actions)

    logging.debug(converted_path)

    (emitted_events, _, _, _) = world.execute_and_emit_events(converted_path)

    all_relevant_literals = []
    old_candidate_formulas = []
    for c in old_candidates:
        f = Formula.convertTextToFormula(c)
        old_candidate_formulas.append(f)
        all_relevant_literals += f.getAllVariables()
    all_relevant_literals = list(set(all_relevant_literals))
    # logging.debug("emitted events are {}".format(emitted_events))
    # logging.debug("+-+-------------- all relevant literals are {}".format(all_relevant_literals))

    trace = Trace.create_trace_from_events_list(emitted_events, literals_to_consider=all_relevant_literals)

    # logging.debug("+++++++++++++++++=======================\n elimination trace is {}".format(trace))
    # logging.debug("desired formula value is {}".format(formula_value))

    for f in old_candidate_formulas:

        if trace.evaluateFormulaOnTrace(f) == formula_value:
            collection_of_candidates.append(str(f))
            collection_of_formulas.append(f)
            stats_log.debug("candidate {} was retained".format(f))
        else:
            stats_log.debug("candidate {} was eliminated".format(f))

    return collection_of_candidates, collection_of_formulas


def create_path_from_formula(f, wall_locations, water_locations, robot_position, items_locations=None):
    return get_path(f, wall_locations, water_locations, robot_position, items_locations)


def create_disambiguation_example(candidates, wall_locations=[], testing=False):
    logging.debug("creating disambiguation examples for candidates {}".format(candidates))
    w = None
    path = None
    candidate_1 = None
    candidate_2 = None
    if len(candidates) == 0 or str(candidates[0]) == constants.UNKNOWN_SOLVER_RES:
        status = constants.FAILED_CANDIDATES_GENERATION_STATUS
        return (status, w, path, None, None, None, None)
    elif len(candidates) == 1:
        status = "ok"
        return (status, w, path, candidates[0], None, None, None)

    else:

        candidate_1 = candidates[0]
        candidate_2 = candidates[1]

        w, path, disambiguation_trace = disambiguate(candidate_1, candidate_2, wall_locations, testing=testing)
        if w == constants.UNKNOWN_SOLVER_RES:
            return (w, None, None, None, None, None, None)
        if w is None and path is None:

            if candidate_1 < candidate_2:
                longer_candidate = candidate_2

            else:
                longer_candidate = candidate_1

            candidates.remove(longer_candidate)
            stats_log.warning(
                "was not able to disambiguate between {} and {}. Removing {}".format(candidate_1, candidate_2,
                                                                                     longer_candidate))

            return create_disambiguation_example(candidates, wall_locations)
        else:
            status = "indoubt"

        return (status, w, path, candidate_1, candidate_2, candidates, disambiguation_trace)
