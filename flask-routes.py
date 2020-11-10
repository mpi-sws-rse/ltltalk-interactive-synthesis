import pdb
import sys

from flask import Flask, request
from flask import make_response

from flask_cors import CORS
import json
import os
from world import World
from candidatesCreation import create_candidates, update_candidates, create_disambiguation_example, \
    create_path_from_formula
from utils import convert_path_to_formatted_path, unwind_actions
import logging
import constants
from logger_initialization import stats_log, error_log
import pdb
import traceback

try:
    from utils.SimpleTree import Formula
    import encodingConstants
except:
    from encoding.utils.SimpleTree import Formula
    from encoding import encodingConstants

from flask import session
from pytictoc import TicToc

app = Flask(__name__)

# in order for using sessions, I had to set support_credentials to True.
# However, with this, default CORS policy of allowing every domain was not allowed.
# Therefore, I had to specify exact domains by setting "origins"
# https://flask-cors.readthedocs.io/en/latest/api.html#using-cors-with-cookies
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
if constants.TESTING:
    app.secret_key = "notsosecret"

# app.logger.setLevel(logging.INFO)
logging.getLogger().setLevel(constants.LOGGING_LEVEL)

flask_log = logging.getLogger('werkzeug')
flask_log.setLevel(logging.ERROR)

try:
    if int(os.environ['TESTING']) == 1:
        constants.TESTING = True
    else:
        constants.TESTING = False
except:
    pass


@app.route('/')
def hello_world():
    return "Hello world"


@app.route('/get-candidate-spec')
def candidate_spec():

    #try:
        stats_log.info("\n======\n")
        answer = {}
        answer["candidates"] = []
        disambiguation_stats = []
        num_disambiguations = 0
        nl_utterance = json.loads(request.args.get('query'))
        examples = json.loads(request.args.get("examples"))
        try:
            criterion = json.loads(request.args.get("optimizer-criterion"))
        except:
            criterion = encodingConstants.COMBINING_OBJECTIVES_MODE
        sessionId = request.args.get("sessionId")

        if "use-hints" in request.args:
            use_hints = request.args.get("use-hints")
            use_hints = True if use_hints == "True" else False
        else:
            use_hints = True
        print("use hints is set to {}".format(use_hints))


        if "no-excessive-trace-principle" in request.args:
            no_excessive_trace = request.args.get("no-excessive-trace-principle")
            no_excessive_trace = True if no_excessive_trace == "True" else False
        else:
            no_excessive_trace = True


        if "no-excessive-effort-principle" in request.args:
            no_excessive_effort = request.args.get("no-excessive-effort-principle")
            no_excessive_effort = True if no_excessive_effort == "True" else False
        else:
            no_excessive_effort = True

        world_1 = World(examples[0]["context"], json_type=2)
        wall_locations = world_1.get_wall_locations()

        stats_log.info("utterance: {}".format(nl_utterance))


        try:
            num_formulas = json.loads(request.args.get("num-formulas"))
            max_depth = json.loads(request.args.get("max-depth"))

        except:
            num_formulas = constants.NUM_CANDIDATE_FORMULAS
            max_depth = constants.CANDIDATE_MAX_DEPTH

        candidates, num_attempts, candidates_generation_time, solver_solving_times = create_candidates(nl_utterance,
                                                                                                       examples,
                                                                                                       testing=constants.TESTING,
                                                                                                       num_formulas=num_formulas,
                                                                                                       id=sessionId,
                                                                                                       max_depth=max_depth,
                                                                                                       criterion=criterion,
                                                                                                       use_hints=use_hints,
                                                                                                       no_excessive_effort=no_excessive_effort,
                                                                                                       no_excessive_trace=no_excessive_trace)

        answer["num_attempts"] = num_attempts
        answer["candidates_generation_time"] = candidates_generation_time
        stats_log.info("solving times are {}".format(solver_solving_times))

        try:
            answer["candidates_generation_solving_time"] = sum(solver_solving_times)
        except:
            answer["candidates_generation_solving_time"] = -1

        answer["sessionId"] = sessionId

        if len(candidates) == 0:
            answer["status"] = constants.FAILED_CANDIDATES_GENERATION_STATUS
        elif str(candidates[0]) == constants.UNKNOWN_SOLVER_RES:
            answer["status"] = constants.UNKNOWN_SOLVER_RES


        elif len(candidates) == 1:
            answer["status"] = "ok"
            answer["candidates"] = [str(candidates[0])]
            answer["num_disambiguations"] = num_disambiguations
            answer["disambiguation_stats"] = disambiguation_stats

        elif len(candidates) > 1:

            answer["status"] = "indoubt"
            t = TicToc()
            t.tic()
            status, disambiguation_world, disambiguation_path, candidate_1, candidate_2, considered_candidates, disambiguation_trace = create_disambiguation_example(
                candidates, wall_locations, testing=constants.TESTING)

            disambiguation_time = t.tocvalue()
            if constants.TESTING:
                num_disambiguations += 1
                disambiguation_stats.append(disambiguation_time)
            if not status == "indoubt":
                answer['status'] = status
                if status == "ok":
                    answer["candidates"].append(str(candidate_1))
                if constants.TESTING:
                    answer["num_disambiguations"] = num_disambiguations
                    answer["disambiguation_stats"] = disambiguation_stats

                return answer

            logging.debug(
                "disambiguation world is {}, disambiguation path is {} for candidate1 = {} and candidate2 = {}".format(
                    disambiguation_world, disambiguation_path, candidate_1, candidate_2))
            answer["world"] = disambiguation_world.export_as_json()
            formatted_path = convert_path_to_formatted_path(disambiguation_path, disambiguation_world)
            logging.debug("formatted path is {}".format(formatted_path))
            answer["path"] = formatted_path
            answer["actions"] = disambiguation_path
            answer["query"] = nl_utterance
            answer["trace"] = disambiguation_trace.traceVector

            answer["candidates"] = [str(c) for c in considered_candidates]
            answer["formatted_candidates"] = [str(c.reFormat()) for c in considered_candidates]
            answer["disambiguation-candidate-1"] = str(candidate_1)
            answer["disambiguation-candidate-2"] = str(candidate_2)

        logging.info("GET-CANDIDATE-SPEC: created the candidates:\n {}".format("\n".join(answer["candidates"])))

        if constants.TESTING:
            answer["num_disambiguations"] = num_disambiguations
            answer["disambiguation_stats"] = disambiguation_stats

        return answer

    # except Exception as e:
    #     error_log.error("exception {}".format(e))
    #     traceback.print_exc()
    #     return (str(e), 500)


@app.route('/get-path')
def get_path_from_formula():
    answer = {}
    context = json.loads(request.args.get("context"))
    world = World(context, json_type=2)
    wall_locations = world.get_wall_locations()
    water_locations = world.get_water_locations()
    robot_position = world.get_robot_position()
    items_locations = world.get_items_locations()

    formulas = json.loads(request.args.get("formulas"))

    paths = []
    answer["status"] = "ok"
    for f in formulas:

        path = create_path_from_formula(f, wall_locations, water_locations, robot_position, items_locations)
        if path is False:
            paths.append("false")
            answer["status"] = "error"

        else:

            formatted_path = convert_path_to_formatted_path(path, World(context, json_type=2))
            paths.append(formatted_path)

    answer["paths"] = paths
    answer["world"] = context

    return answer


@app.route('/debug-disambiguation')
def debug_disambiguation():
    candidates = json.loads(request.args.get("candidates"))
    context = json.loads(request.args.get("context"))
    world = World(context, json_type=2)
    wall_locations = world.get_wall_locations()
    converted_candidates = [Formula.convertTextToFormula(c) for c in candidates]
    status, disambiguation_world, disambiguation_path, candidate_1, candidate_2, considered_candidates, disambiguation_trace = create_disambiguation_example(
        converted_candidates, wall_locations=wall_locations)
    logging.debug("status is {}, disambiguation path is {}".format(status, disambiguation_path))
    logging.debug("disambiguation world is {}".format(disambiguation_world))
    answer = {}
    answer["status"] = status
    answer["path"] = disambiguation_path
    return answer


@app.route('/user-decision-update')
def user_decision_update():
    try:

        t = TicToc()
        if constants.TESTING:
            num_disambiguations = 0
            disambiguation_stats = []

        decision = request.args.get("decision")
        sessionId = request.args.get("sessionId")

        candidates = json.loads(request.args.get("candidates"))

        path = json.loads(request.args.get("path"))

        context = json.loads(request.args.get("context"))
        world = World(context, json_type=2)
        wall_locations = world.get_wall_locations()
        actions = json.loads(request.args.get("actions"))
        updated_candidates, updated_formulas = update_candidates(candidates, path, decision, world, actions)

        answer = {}
        answer["sessionId"] = sessionId
        answer["candidates"] = updated_candidates
        answer["formatted_candidates"] = [str(f.reFormat()) for f in updated_formulas]
        if len(updated_candidates) == 0:
            answer["status"] = constants.FAILED_CANDIDATES_GENERATION_STATUS
            return answer
        elif len(updated_candidates) == 1:

            answer["status"] = "ok"
            if constants.TESTING:
                answer["num_disambiguations"] = num_disambiguations
                answer["disambiguation_stats"] = disambiguation_stats
            return answer
        elif len(updated_candidates) > 1:
            answer["status"] = "indoubt"

            converted_candidates = [Formula.convertTextToFormula(c) for c in updated_candidates]

            t = TicToc()
            t.tic()
            status, disambiguation_world, disambiguation_path, candidate_1, candidate_2, considered_candidates, disambiguation_trace = create_disambiguation_example(
                converted_candidates, wall_locations=wall_locations)
            disambiguation_time = t.tocvalue()
            if constants.TESTING:
                num_disambiguations += 1
                disambiguation_stats.append(disambiguation_time)
            if not status == "indoubt":
                answer["status"] = status
                if status == "ok":

                    answer["candidates"] = [str(candidate_1)]
                    answer["formatted_candidates"] = [str(candidate_1.reFormat())]
                else:
                    answer["candidates"] = []
                    answer["formatted_candidates"] = []
                if constants.TESTING:
                    answer["num_disambiguations"] = num_disambiguations
                    answer["disambiguation_stats"] = disambiguation_stats
                return answer
            else:

                answer["world"] = disambiguation_world.export_as_json()
                formatted_path = convert_path_to_formatted_path(disambiguation_path, disambiguation_world)
                answer["path"] = formatted_path
                answer["disambiguation-candidate-1"] = str(candidate_1)
                answer["disambiguation-candidate-2"] = str(candidate_2)
                answer["candidates"] = [str(f) for f in considered_candidates]
                answer["formatted_candidates"] = [str(f.reFormat()) for f in considered_candidates]
                answer["actions"] = disambiguation_path

                if constants.TESTING:
                    answer["num_disambiguations"] = num_disambiguations
                    answer["disambiguation_stats"] = disambiguation_stats

                return answer
    except Exception as e:
        error_log.error("exception {}".format(e))
        return (str(e), 500)

# if __name__=='__main__':
#     app.run(request_handler=TimeoutRequestHandler)
