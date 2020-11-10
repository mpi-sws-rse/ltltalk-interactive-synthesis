import argparse
import copy
import os
import json
import pdb
import time
import sys


from world import World
from encoding.utils.SimpleTree import Formula
import requests
from pytictoc import TicToc
from utils import unwind_actions
from encoding.utils.Traces import Trace
import csv
import logging
import constants

FLIPPER_URL = "http://localhost:5000"
TEST_SESSION_ID = "test"

CANDIDATES_GENERATION_TIMEOUT = 60
WAITING_FOR_A_QUESTION_TIMEOUT = 60


TOP_DICT = {k:"TOP{}".format(k) for k in constants.TOP_VALUES}

WAITING_TIME_FOR_FIRST_CANDIDATES_HEADER = "initial_user_waiting"
INIT_CANDIDATES_GENERATION_TIME = "initial_candidates_generation_time"
INIT_CANDIDATES_ONLY_SOLVING_TIME = "candidates_generation_solving_time"
NUM_INIT_CANDIDATES_HEADER = "num_initial_candidates"
NL_UTTERANCE_HEADER = "nl_utterance"
FORMULA_HEADER = "target_formula"
IS_FORMULA_FOUND_HEADER = "formula_is_found"
RESULT_FORMULA_HEADER = "result_formula"
NUM_QUESTIONS_ASKED_HEADER = "num_questions_asked"
AVERAGE_WAITING_FOR_QUESTIONS_HEADER = "average_question_waiting"
AVERAGE_DISAMBIGUATION_DURATION_HEADER = "average_disambiguation_duration"
NUM_DISAMBIGUATIONS_HEADER = "num_disambiguations"
NUM_ATTEMPTS_FOR_CANDIDATES_GENERATION_HEADER = "num_attempts_candidates_generation"
TEST_FILENAME_HEADER = "filename"
TEST_ID_HEADER = "test_id"
MAX_NUM_CANDIDATES_HEADER = "max_num_candidates"
MAX_DEPTH_HEADER = "max depth"

HEADERS = [
    TEST_ID_HEADER,
    MAX_NUM_CANDIDATES_HEADER,
    MAX_DEPTH_HEADER,
    NL_UTTERANCE_HEADER,
    FORMULA_HEADER,
    WAITING_TIME_FOR_FIRST_CANDIDATES_HEADER,
    INIT_CANDIDATES_GENERATION_TIME,
    INIT_CANDIDATES_ONLY_SOLVING_TIME,
    NUM_INIT_CANDIDATES_HEADER,
    NUM_ATTEMPTS_FOR_CANDIDATES_GENERATION_HEADER,
    NUM_QUESTIONS_ASKED_HEADER,
    AVERAGE_WAITING_FOR_QUESTIONS_HEADER,
    AVERAGE_DISAMBIGUATION_DURATION_HEADER,
    NUM_DISAMBIGUATIONS_HEADER,
    IS_FORMULA_FOUND_HEADER,
    RESULT_FORMULA_HEADER
]

HEADERS = HEADERS + list(TOP_DICT.values())

main_log = logging.getLogger('main_logger')
logging.basicConfig(level=logging.INFO, format='%(message)s')

fh = logging.FileHandler('main.log')
fh.setLevel(logging.INFO)
main_log.addHandler(fh)


# ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)
# main_log.addHandler(ch)

def sanity_check(path, w, f, no_excessive_trace=True, no_excessive_effort=True):
    world = copy.deepcopy(w)
    try:
        (emitted_events, _, _, _) = world.execute_and_emit_events(path)

        all_relevant_literals = f.getAllVariables()
        trace = Trace.create_trace_from_events_list(emitted_events, literals_to_consider=all_relevant_literals)
        return Trace.evaluateFormulaOnTrace(trace, f)

    except Exception as e:
        print(e)
        print(w)
        print(path)
        pdb.set_trace()
        return False


def flipper_session(test_def, max_num_init_candidates, criterion, questions_timeout, candidates_timeout,
                    max_depth, test_id=TEST_SESSION_ID, use_hints=True, num_examples=None,
                    noExcessiveTrace=True, noExcessiveEffort=True):
    stats = {}
    server_num_disambiguations = 0
    server_disambiguations_stats = []

    nl_utterance = test_def["description"]
    target_formula = Formula.convertTextToFormula(test_def["target-formula"])

    examples = test_def["examples"]

    if not num_examples is None:
        if num_examples <= len(examples):
            examples = examples[0:num_examples]

    print("number of examples traces is {}".format(len(examples)))



    candidate_spec_payload = {}
    #candidate_spec_payload["context"] = json.dumps(world_context)
    candidate_spec_payload["query"] = json.dumps(nl_utterance)
    #candidate_spec_payload["path"] = json.dumps(init_path)
    candidate_spec_payload["examples"] = json.dumps(examples)
    candidate_spec_payload["sessionId"] = test_id
    candidate_spec_payload["num-formulas"] = max_num_init_candidates
    candidate_spec_payload["max-depth"] = max_depth

    candidate_spec_payload["use-hints"] = use_hints
    candidate_spec_payload["no-excessive-trace-principle"] = noExcessiveTrace
    candidate_spec_payload["no-excessive-effort-principle"] = noExcessiveEffort
    candidate_spec_payload["optimizer-criterion"] = json.dumps(criterion)


    # try:
    #     r = requests.get(FLIPPER_URL + "/get-candidate-spec", params=candidate_spec_payload, timeout=candidates_timeout)
    # except requests.exceptions.Timeout:
    #     stats[INIT_CANDIDATES_HEADER] = "timeout"
    #     for h in HEADERS:
    #         if h not in stats:
    #             stats[h] = "/"
    #     return stats

    for ex in examples:
        world_s = World(ex["context"], json_type=2)
        f_s = target_formula
        path_s = ex["init-path"]
        if not sanity_check(path_s, world_s, target_formula, no_excessive_effort=noExcessiveEffort,no_excessive_trace=noExcessiveTrace):
            pdb.set_trace()
            raise ValueError("test is not correct")



    stats[MAX_NUM_CANDIDATES_HEADER] = max_num_init_candidates
    stats[NL_UTTERANCE_HEADER] = nl_utterance
    stats[MAX_DEPTH_HEADER] = max_depth

    r = requests.get(FLIPPER_URL + "/get-candidate-spec", params=candidate_spec_payload)
    init_candidates_time = r.elapsed.total_seconds()
    response_status = r.status_code

    if response_status == 500:
        stats[WAITING_TIME_FOR_FIRST_CANDIDATES_HEADER] = "error"
        for h in HEADERS:
            if h not in stats:
                stats[h] = "/"
        return stats


    json_response = r.json()
    if json_response["status"] == constants.UNKNOWN_SOLVER_RES:
        stats[WAITING_TIME_FOR_FIRST_CANDIDATES_HEADER] = "timeout"
        for h in HEADERS:
            if h not in stats:
                stats[h] = "/"
        return stats

    candidates = json_response["candidates"]
    main_log.info("init candidates are {}\n\n".format(candidates))

    for top_x in TOP_DICT:
        if str(target_formula) in candidates[0:top_x]:
            stats[TOP_DICT[top_x]] = True
        else:
            stats[TOP_DICT[top_x]] = False

    num_initial_candidates = len(candidates)

    server_num_disambiguations += json_response["num_disambiguations"]
    server_disambiguations_stats += json_response["disambiguation_stats"]

    stats[WAITING_TIME_FOR_FIRST_CANDIDATES_HEADER] = init_candidates_time
    stats[INIT_CANDIDATES_GENERATION_TIME] = json_response["candidates_generation_time"]
    stats[INIT_CANDIDATES_ONLY_SOLVING_TIME] = json_response["candidates_generation_solving_time"]
    stats[NUM_INIT_CANDIDATES_HEADER] = num_initial_candidates

    stats[NUM_ATTEMPTS_FOR_CANDIDATES_GENERATION_HEADER] = json_response["num_attempts"]
    stats[FORMULA_HEADER] = test_def["target-formula"]


    interaction_status = json_response["status"]
    if interaction_status == "ok":
        foundFormula = Formula.convertTextToFormula(candidates[0])
        stats[RESULT_FORMULA_HEADER] = str(foundFormula)
        if foundFormula == target_formula:
            stats[IS_FORMULA_FOUND_HEADER] = True
        else:
            stats[IS_FORMULA_FOUND_HEADER] = False
        return stats




    if num_initial_candidates == 0:
        stats[IS_FORMULA_FOUND_HEADER] = False
        for h in HEADERS:
            if h not in stats:
                stats[h] = "/"
        return stats
    world_context = json_response["world"]

    world = World(world_context, json_type=2)

    actions = json_response["actions"]

    num_questions_asked = 0
    decision_update_durations = []
    while num_questions_asked < num_initial_candidates:
        time.sleep(5)

        converted_path = unwind_actions(actions)

        (emitted_events, _, _, _) = world.execute_and_emit_events(converted_path)

        all_relevant_literals = target_formula.getAllVariables()
        trace = Trace.create_trace_from_events_list(emitted_events, literals_to_consider=all_relevant_literals)
        user_decision = Trace.evaluateFormulaOnTrace(trace, target_formula)

        decision_update_payload = {"session-id": json.dumps(TEST_SESSION_ID), "sessionId": json.dumps(TEST_SESSION_ID),
                                   "decision": json.dumps(int(user_decision)), "context": json.dumps(world_context),
                                   "path": json.dumps(converted_path), "candidates": json.dumps(candidates),
                                   "actions": json.dumps(actions)}

        # try:
        #     decision_update_request = requests.get(FLIPPER_URL + "/user-decision-update",
        #                                            params=decision_update_payload, timeout=questions_timeout)
        # except requests.exceptions.Timeout:
        #     stats[AVERAGE_WAITING_FOR_QUESTIONS_HEADER] = "timeout"
        #     for h in HEADERS:
        #         if not h in stats:
        #             stats[h] = "/"
        #     return stats
        decision_update_request = requests.get(FLIPPER_URL + "/user-decision-update", params=decision_update_payload)
        decision_time = decision_update_request.elapsed.total_seconds()
        decision_update_durations.append(decision_time)

        if decision_update_request.status_code == 500:
                stats[AVERAGE_WAITING_FOR_QUESTIONS_HEADER] = "error"
                for h in HEADERS:
                    if not h in stats:
                        stats[h] = "/"
                return stats


        result_decision_update = decision_update_request.json()

        num_questions_asked += 1
        status = result_decision_update["status"]

        if status == constants.UNKNOWN_SOLVER_RES:
            stats[AVERAGE_WAITING_FOR_QUESTIONS_HEADER] = "timeout"
            for h in HEADERS:
                if not h in stats:
                    stats[h] = "/"
            return stats

        candidates = result_decision_update["candidates"]
        server_num_disambiguations += result_decision_update["num_disambiguations"]
        server_disambiguations_stats += result_decision_update["disambiguation_stats"]
        main_log.info("decision update. remaining candidates are {}".format(candidates))

        if status == "ok":

            foundFormula = Formula.convertTextToFormula(candidates[0])
            stats[RESULT_FORMULA_HEADER] = str(foundFormula)
            if foundFormula == target_formula:
                stats[IS_FORMULA_FOUND_HEADER] = True
            else:
                stats[IS_FORMULA_FOUND_HEADER] = False

            stats[NUM_QUESTIONS_ASKED_HEADER] = num_questions_asked
            stats[NUM_DISAMBIGUATIONS_HEADER] = server_num_disambiguations

            try:
                stats[AVERAGE_DISAMBIGUATION_DURATION_HEADER] = sum(server_disambiguations_stats) / len(
                    server_disambiguations_stats)
            except ZeroDivisionError:
                stats[AVERAGE_DISAMBIGUATION_DURATION_HEADER] = "/"

            try:
                stats[AVERAGE_WAITING_FOR_QUESTIONS_HEADER] = sum(decision_update_durations) / len(
                    decision_update_durations)
            except ZeroDivisionError:
                stats[AVERAGE_WAITING_FOR_QUESTIONS_HEADER] = "/"
            break
        if status == constants.FAILED_CANDIDATES_GENERATION_STATUS:
            stats[AVERAGE_WAITING_FOR_QUESTIONS_HEADER] = "candidates generation failure"
            for h in HEADERS:
                if not h in stats:
                    stats[h] = "/"
            return stats

        world_context = result_decision_update["world"]
        world = World(world_context, json_type=2)

        actions = result_decision_update["actions"]

    return stats


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--tests_definition_folder", dest="testsFolder")
    parser.add_argument("--output", dest="statsOutput", default="stats.csv")
    parser.add_argument("--condensed_output", dest="statsCondensedOutput", default="condensedStats.csv")
    parser.add_argument("--num_repetitions", dest="numRepetitions", type=int, default=1)
    parser.add_argument("--num_examples", dest="numExamples", type=int, default=None)
    parser.add_argument("--num_init_candidates", dest="numInitCandidates", nargs='+', type=int, default=[3, 6, 10])
    parser.add_argument("--max_depth", dest="maxDepth", type=int, nargs='+', default=[2, 3, 4])
    parser.add_argument("--continue_test", dest="continueTest", action='store_true', default=False)
    parser.add_argument("--no_hints", dest="notUseHints", action='store_true', default=False)
    parser.add_argument("--exclude_no_excessive_trace_principle", dest="excludeNoExcessiveTracePrinciple", action='store_true', default=False)
    parser.add_argument("--exclude_no_excessive_effort_principle", dest="excludeNoExcessiveEffortPrinciple", action='store_true',
                        default=False)
    parser.add_argument("--candidates_timeout", dest="candidatesTimeout", type=int,
                        default=CANDIDATES_GENERATION_TIMEOUT)
    parser.add_argument("--questions_timeout", dest="questionsTimeout", type=int,
                        default=WAITING_FOR_A_QUESTION_TIMEOUT)
    parser.add_argument("--optimizer_criterion", dest="optimizerCriterion", default="lexicographic")

    args, unknown = parser.parse_known_args()
    directory = args.testsFolder

    if args.continueTest:
        statsOpeningMode = "a"
    else:
        statsOpeningMode = "w"

    if args.notUseHints is True:
        use_hints = False
    else:
        use_hints = True

    condensed_headers = ["task id", "depth", "num initial candidates", "formula found", "overall waiting time", "number of interactions",
                         "candidates generation waiting time"]

    with open(args.statsOutput, statsOpeningMode) as csv_stats:
        with open(args.statsCondensedOutput, statsOpeningMode) as condensed_stats_file:
            condensed_writer = csv.DictWriter(condensed_stats_file, fieldnames=condensed_headers)
            condensed_writer.writeheader()
            headers = HEADERS
            writer = csv.DictWriter(csv_stats, fieldnames=headers)
            tests_already_covered = []

            if args.continueTest:
                with open(args.statsOutput) as csv_read_stats:
                    reader = csv.DictReader(csv_read_stats)

                    tests_already_covered = [row[TEST_ID_HEADER] for row in reader]
            else:

                writer.writeheader()
            all_files = sorted(os.scandir(directory), key= lambda dir_entry: dir_entry.name)

            for test_filename in all_files:

                with open(test_filename.path) as test_file:
                    test_def = json.load(test_file)
                    number_of_times_formula_is_found = 0
                    individual_overall_durations = []
                    individual_number_of_interactions = []
                    individual_formula_generation_waiting_times = []
                    for num_init_candidates in args.numInitCandidates:

                        for max_depth in args.maxDepth:
                            for rep in range(args.numRepetitions):

                                main_log.info(
                                    "testing {}, for max {} candidates, max depth {}, repetition {}".format(
                                        test_filename.name, num_init_candidates, max_depth, rep))
                                test_id = test_filename.name + str(num_init_candidates) + str(max_depth) + str(rep)
                                test_name = test_filename.name.split(".")[0]
                                if args.excludeNoExcessiveTracePrinciple is True:
                                    noExcessiveTrace = False
                                else:
                                    noExcessiveTrace = True

                                if args.excludeNoExcessiveEffortPrinciple is True:
                                    noExcessiveEffort = False
                                else:
                                    noExcessiveEffort = True

                                if not test_id in tests_already_covered:
                                    try:
                                        stats = flipper_session(test_def, max_num_init_candidates=num_init_candidates,
                                                                questions_timeout=args.questionsTimeout,
                                                                candidates_timeout=args.candidatesTimeout, test_id=test_id,
                                                                max_depth=max_depth, criterion=args.optimizerCriterion,
                                                                num_examples=args.numExamples, use_hints=use_hints,
                                                                noExcessiveTrace=noExcessiveTrace,
                                                                noExcessiveEffort=noExcessiveEffort)
                                    except Exception as e:
                                        stats = {}
                                        for h in HEADERS:
                                                stats[h] = "unknown error"
                                        main_log.error("Failed with the exception {}".format(e))


                                    if stats['formula_is_found'] is True:
                                        number_of_times_formula_is_found += 1
                                    formulas_generation_time = stats['initial_candidates_generation_time'][0]
                                    individual_formula_generation_waiting_times.append(formulas_generation_time)
                                    if stats["num_questions_asked"] == "/":
                                        question_waiting_time = 0
                                    else:
                                        question_waiting_time = stats['num_questions_asked'] * stats['average_disambiguation_duration']

                                    overall_time = formulas_generation_time  + question_waiting_time
                                    individual_overall_durations.append(overall_time)
                                    if stats['num_questions_asked'] == "/":
                                        num_questions_asked = 0
                                    else:
                                        num_questions_asked = stats['num_questions_asked']
                                    individual_number_of_interactions.append(num_questions_asked)


                                    stats[TEST_ID_HEADER] = test_id
                                    writer.writerow(stats)
                                    main_log.info("\n")
                                    time.sleep(10)
                            condensed_stats = {"task id": test_name, "formula found":number_of_times_formula_is_found,
                                               "overall waiting time":avg(individual_overall_durations),
                                               "number of interactions":avg(individual_number_of_interactions),
                                               "candidates generation waiting time": avg(individual_formula_generation_waiting_times),
                                               "depth": max_depth,
                                               "num initial candidates": num_init_candidates}

                            condensed_writer.writerow(condensed_stats)



            main_log.info("\n\n===\n\n")

def avg(l):
    return sum(l) / len(l)

if __name__ == '__main__':
    main()
