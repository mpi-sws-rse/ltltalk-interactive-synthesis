import constants
import json
import pdb
import logging


DEFAULT_NUM_FORMULAS = constants.NUM_CANDIDATE_FORMULAS
DEFAULT_MAX_DEPTH = constants.CANDIDATE_MAX_DEPTH

def get_literals(pickup_locations, all_locations):
    literals = []
    literals += constants.STATE_EVENTS
    for loc in pickup_locations:
        literals += constants.PICKUP_EVENTS_PER_LOCATION[loc]

    for loc in all_locations:
        literals.append(constants.AT_EVENTS_PER_LOCATION[loc])
        if loc in constants.SPECIAL_LOCATIONS:
            literals.append("at_{}".format(constants.SPECIAL_LOCATIONS[loc]))
    return literals


def create_json_spec(file_name, emitted_events_sequences, hints, pickup_locations, all_locations, negative_sequences, num_formulas = DEFAULT_NUM_FORMULAS,
                      max_depth = DEFAULT_MAX_DEPTH):


    if num_formulas is None:
        num_formulas = DEFAULT_NUM_FORMULAS

    logging.debug("hints when creating json file are {}".format(hints))
    with open(file_name, "w") as exampleJsonFile:
        example_info = {}
        literals = []
        literals += constants.STATE_EVENTS
        for loc in pickup_locations:
            literals += constants.PICKUP_EVENTS_PER_LOCATION[loc]

        for loc in all_locations:
            literals.append(constants.AT_EVENTS_PER_LOCATION[loc])
            if loc in constants.SPECIAL_LOCATIONS:                
                literals.append("at_{}".format(constants.SPECIAL_LOCATIONS[loc]))

        example_info["literals"] = literals
        example_info["number-of-formulas"] = num_formulas
        example_info["max-depth-of-formula"] = max_depth
        example_info["num-solutions-per-depth"] = constants.NUM_CANDIDATE_FORMULAS_OF_SAME_DEPTH
        example_info["operators"] = constants.OPERATORS
        example_info["hints"] = [[h, hints[h]] for h in hints]
        
        positive = [";".join([",".join([e for e in timestep_events])
                              for timestep_events in emitted_events])
                    for emitted_events in emitted_events_sequences]
        example_info["positive"] = positive
        negative = [";".join([",".join([e for e in timestep_events])
                              for timestep_events in neg_emitted_events])
                    for neg_emitted_events in negative_sequences]
        example_info["negative"] = negative


        json.dump(example_info, exampleJsonFile)

def convert_path_to_formatted_path(disambiguation_path, disambiguation_world):
    formatted_path = []
    # not sure if it is necessary, but probably does not hurt: setting the first step to be the move to the init
    # position
    formatted_path.append({"action": "path",
                           "x": disambiguation_world.robot_position[0],
                           "y": disambiguation_world.robot_position[1],
                           "color": "null",
                           "shape": "null",
                           "possible": "true"
                           })

    for step in disambiguation_path:


        if step[0] == "move":
            disambiguation_world.move(step[1])
            formatted_path.append({"action": "path",
                                   "x": disambiguation_world.robot_position[0],
                                   "y": disambiguation_world.robot_position[1],
                                   "color": "null",
                                   "shape": "null",
                                   "possible": "true"
                                   })
        elif step[0] == constants.PASS:

            formatted_path.append({"action": "path",
                                   "x": disambiguation_world.robot_position[0],
                                   "y": disambiguation_world.robot_position[1],
                                   "color": "null",
                                   "shape": "null",
                                   "possible": "true"
                                   })
        elif step[0] == "pick":
            for item_desc in step[1:]:
                for _ in range(item_desc[0]):
                    formatted_path.append({
                        "action": "pickitem",
                        "x": disambiguation_world.robot_position[0],
                        "y": disambiguation_world.robot_position[1],
                        "color": item_desc[1],
                        "shape": item_desc[2],
                        "possible": "true"
                    })
                    disambiguation_world.pick([(item_desc[1], item_desc[2])])
    return formatted_path


def convert_json_actions_to_world_format(world, actions):

    converted_actions = []
    pick_list = []
    for action in actions:
        current_pos = world.robot_position
        if action["action"] == "path":

            # adding pick list after a number of consecutive picks
            if len(pick_list) > 0:
                converted_actions.append((constants.PICK, pick_list))
                world.pick(pick_list)
                pick_list = []

            x_diff = int(action["x"]) - current_pos[0]
            y_diff = int(action["y"]) - current_pos[1]
            if x_diff == 1 and y_diff == 0:
                direction = constants.RIGHT

            elif x_diff == -1 and y_diff == 0:
                direction = constants.LEFT

            elif x_diff == 0 and y_diff == 1:
                direction = constants.UP

            elif x_diff == 0 and y_diff == -1:
                direction = constants.DOWN

            elif x_diff == 0 and y_diff == 0:
                continue
            else:
                raise ValueError("got unexpected x_diff = {} and y_diff = {} from current_pos = {} and action = {}".
                                 format(x_diff, y_diff, current_pos, action))
            converted_actions.append((constants.MOVE, direction))
            world.move(direction)

        elif action["action"] == "pickitem":
            pick_list.append((action["color"], action["shape"]))

    if len(pick_list) > 0:
        converted_actions.append((constants.PICK, pick_list))
        world.pick(pick_list)

    return converted_actions


def unwind_actions(actions):

    converted_list = []
    for action in actions:
        if action[0] == constants.PASS:
            converted_list.append(action)
        elif action[0] == constants.MOVE:
            converted_list.append(action)
        elif action[0] == constants.PICK:
            pick_list = []
            for item_desc in action[1:]:
                for _ in range(item_desc[0]):
                    pick_list.append((item_desc[1], item_desc[2]))
            converted_list.append((constants.PICK, pick_list))

    return converted_list

