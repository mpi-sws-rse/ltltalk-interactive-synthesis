import pdb
import constants
from collections import defaultdict
import logging

class World:
    def __init__(self, worldDescriptionJson, json_type = 0):

        # it is a complete mess with different formats used by different servers. That will have to be unified :/

        # items' positions are given in a list, robot's position as well
        if json_type == 0:
            self.width = int(worldDescriptionJson["width"])
            self.height = int(worldDescriptionJson["height"])
            self.wall = []
            self.water = []
            self.items_on_the_floor = defaultdict(lambda : defaultdict(int))
            self.robot_position = (int(worldDescriptionJson["robot"][0]), int(worldDescriptionJson["robot"][1]))
            self.items_on_robot = defaultdict(int)
    
    
            for item in worldDescriptionJson["robot"][2]:
                item_description = (item[0], item[1])
                self.items_on_robot[item_description] += 1
    
    
    
            for world_place in worldDescriptionJson["world"]:
                pos = (world_place[0], world_place[1])
                if world_place[2] == "wall":
                    self.wall.append(pos)
                elif world_place[2] == "water":
                    self.water.append(pos)
                elif world_place[2] == "item":
                    found_item = (world_place[3], world_place[4])
                    self.items_on_the_floor[pos][found_item] += 1

        # items' position and robots' position are given as (x,y) coordinates
        elif json_type == 1:
            self.width = int(worldDescriptionJson["width"])
            self.height = int(worldDescriptionJson["height"])
            self.wall = []
            self.water = []
            self.items_on_the_floor = defaultdict(lambda: defaultdict(int))
            self.robot_position = (int(worldDescriptionJson["robot"]["x"]), int(worldDescriptionJson["robot"]["y"]))
            self.items_on_robot = defaultdict(int)

            for field in worldDescriptionJson["items"]:
                pos = (field["x"], field["y"])
                if field["type"] == "wall":
                    self.wall.append(pos)
                elif field["type"] == "water":
                    self.water.append(pos)
                elif field["type"] == "item":
                    found_item = (field["color"], field["shape"])
                    self.items_on_the_floor[pos][found_item] = int(field["quantity"])

        # robot's position is given as a list, items' position with (x,y) coordinates
        elif json_type == 2:
            self.width = int(worldDescriptionJson["width"])
            self.height = int(worldDescriptionJson["height"])
            self.wall = []
            self.water = []
            self.items_on_the_floor = defaultdict(lambda: defaultdict(int))
            self.robot_position = (int(worldDescriptionJson["robot"][0]), int(worldDescriptionJson["robot"][1]))
            self.items_on_robot = defaultdict(int)

            for field in worldDescriptionJson["world"]:
                pos = (field["x"], field["y"])
                if field["type"] == "wall":
                    self.wall.append(pos)
                elif field["type"] == "water":
                    self.water.append(pos)
                elif field["type"] == "item":
                    found_item = (field["color"], field["shape"])
                    self.items_on_the_floor[pos][found_item] += 1

                    

    def export_as_json(self):
        w_json = {}
        w_json["height"] = self.height
        w_json["width"] = self.width
        w_json["robot"] = [self.robot_position[0], self.robot_position[1],[]]

        for robo_item in self.items_on_robot:
            for _ in range(self.items_on_robot[robo_item]):
                w_json["robot"][2].append({"color": robo_item[0], "shape":robo_item[1]})



        wall_fields = []
        for field in self.wall:
            wall_fields.append({"x": field[0], "y": field[1], "type":"wall", "shape":"null", "color":"null"})

        water_fields = []
        for field in self.water:
            water_fields.append({"x": field[0], "y": field[1], "type":"water", "shape":"null", "color":"null"})

        item_fields = []
        for field in self.items_on_the_floor:
            for item_desc in self.items_on_the_floor[field]:
                for _ in range(self.items_on_the_floor[field][item_desc]):
                    item_fields.append({"x": field[0], "y": field[1], "type":"item", "shape":item_desc[1], "color":item_desc[0]})

        w_json["world"] = wall_fields + water_fields + item_fields

        return w_json

    def get_wall_locations(self):
        return self.wall

    def get_water_locations(self):
        return self.water

    def get_robot_position(self):
        return self.robot_position

    def get_items_locations(self):
        items_locations = defaultdict(int)
        for (x,y) in self.items_on_the_floor:
            for (c, s) in self.items_on_the_floor[(x,y)]:
                items_locations[(x,y,c,s)] = self.items_on_the_floor[(x,y)][(c,s)]
        return items_locations

    def __repr__(self):
        s = ""

        items_on_floor_counter = 0
        dict_of_items_on_floor = {}
        for j in range(self.height,-1,-1):
            for i in range(self.width):
                pos = (i,j)

                if pos in self.items_on_the_floor:
                    if pos == self.robot_position:
                        s += "X"
                        dict_of_items_on_floor["X"] = pos
                    else:
                        s += str(items_on_floor_counter)
                        dict_of_items_on_floor[items_on_floor_counter] = pos
                        items_on_floor_counter += 1
                elif pos == self.robot_position:
                    s += "X"
                elif pos in self.water:
                    s += "w"
                elif pos in self.wall:
                    s += "b"


                else:
                    s += " "
            s +="\n"
        s += "\n"

        s += "items:\n"
        if len(dict_of_items_on_floor) == 0:
            s +="None\n"
        for item_label in dict_of_items_on_floor:
            pos = dict_of_items_on_floor[item_label]
            s += "{} === {}: {}\n".format(item_label, pos, dict(self.items_on_the_floor[pos]))

        s +="\nrobot_position: {}\n".format(self.robot_position)
        s +="items at robot:\n"
        if len(self.items_on_robot) == 0:
            s += "None\n"
        else:
            for item_description in self.items_on_robot:
                s += "{}: {}\n".format(item_description, self.items_on_robot[item_description])

        return s

    def move(self, direction):
        roboX = self.robot_position[0]
        roboY = self.robot_position[1]
        if direction == constants.LEFT:
            if roboX == 0:
                raise ValueError("Can't move {} when robot is at the position {}".format(direction, self.robot_position))
            else:
                newPosition = (roboX-1, roboY)

        elif direction == constants.RIGHT:
            if roboX == self.width - 1:
                raise ValueError("Can't move {} when robot is at the position {}".format(direction, self.robot_position))
            else:
                newPosition = (roboX+1, roboY)

        elif direction == constants.UP:
            if roboY == self.height - 1:
                raise ValueError("Can't move {} when robot is at the position {}".format(direction, self.robot_position))
            else:
                newPosition = (roboX, roboY+1)

        elif direction == constants.DOWN:
            if roboY == 0:
                raise ValueError("Can't move {} when robot is at the position {}".format(direction, self.robot_position))
            else:
                newPosition = (roboX, roboY-1)

        if newPosition in self.wall:
            pdb.set_trace()
            raise RuntimeError("Can't move into the wall")

        self.robot_position = newPosition


        return self.robot_position

    def pick(self, color_shape_pairs, speculative = False, items_on_robot = None, items_at_pos=None):
        if speculative == False:
            new_items_on_robot = self.items_on_robot.copy()
            new_items_at_pos = self.items_on_the_floor[self.robot_position].copy()
        else:
            new_items_on_robot = items_on_robot.copy()
            new_items_at_pos = items_at_pos.copy()

        for item_description in color_shape_pairs:
            if new_items_at_pos[item_description] == 0:
                raise RuntimeError("Can not pick {} from {}".format(color_shape_pairs, self.robot_position))
            else:
                new_items_at_pos[item_description] -= 1
                new_items_on_robot[item_description] += 1

        if speculative == False:
            self.items_on_robot = new_items_on_robot
            self.items_on_the_floor[self.robot_position] = new_items_at_pos

        return new_items_on_robot, new_items_at_pos

    def _get_num_items(self, items_from_a_position, color = None, shape = None):
        num_items = 0
        for item_description in items_from_a_position:
            item_color = item_description[0]
            item_shape = item_description[1]
            if (color is None or item_color == color) and (shape is None or item_shape == shape):
                num_items += items_from_a_position[item_description]

        return num_items

    def execute_and_emit_events(self, sequence_of_actions, no_excessive_trace=True, no_excessive_effort=True):

        new_sequence_of_actions = []
        for event, next_event in zip(sequence_of_actions, sequence_of_actions[1:]):
            if event[0] == constants.PICK and next_event[0] == constants.PICK:
                raise ValueError("No two consecutive {} events allowed".format(constants.PICK))

        #     if event[0] == constants.MOVE and next_event[0] == constants.PICK:
        #         continue
        #     else:
        #         new_sequence_of_actions.append(event)
        # new_sequence_of_actions.append(sequence_of_actions[-1])
        #
        # sequence_of_actions = new_sequence_of_actions
        events = []
        collection_of_negative_events = []
        pickup_locations = []
        all_locations = []
        init_events = []

        # add initial dry event
        if not self.robot_position in self.water:
            init_events.append(constants.DRY)


        # add initial location event
        if self.robot_position in constants.SPECIAL_LOCATIONS:
            init_events.append("at_{}".format(constants.SPECIAL_LOCATIONS[self.robot_position]))
        else:
            init_events.append("at_{}_{}".format(self.robot_position[0], self.robot_position[1]))

        all_locations.append(self.robot_position)
        events.append(init_events)



        logging.warning("for sequence of actions: {}".format(sequence_of_actions))
        list_of_forked_events = []
        for idx, action in enumerate(sequence_of_actions):

            action_events = []

            if action[0] == constants.MOVE:



                self.move(action[1])
                if not self.robot_position in self.water:
                    action_events.append(constants.DRY)

                if self.robot_position in constants.SPECIAL_LOCATIONS:
                    action_events.append("at_{}".format(constants.SPECIAL_LOCATIONS[self.robot_position]))
                else:
                    action_events.append("at_{}_{}".format(self.robot_position[0], self.robot_position[1]))
                all_locations.append(self.robot_position)

            elif action[0] == constants.PASS:
                if not self.robot_position in self.water:
                    action_events.append(constants.DRY)

                if self.robot_position in constants.SPECIAL_LOCATIONS:
                    action_events.append("at_{}".format(constants.SPECIAL_LOCATIONS[self.robot_position]))
                else:
                    action_events.append("at_{}_{}".format(self.robot_position[0], self.robot_position[1]))
                if not self.robot_position in all_locations:
                    all_locations.append(self.robot_position)

            elif action[0] == constants.PICK:
                pickup_locations.append(self.robot_position)
                old_field_items = self.items_on_the_floor[self.robot_position].copy()

                old_robot_items = self.items_on_robot.copy()
                list_of_items = [tuple(it) for it in action[1]]
                self.pick(list_of_items)
                new_field_items = self.items_on_the_floor[self.robot_position]
                action_events = self._get_action_events(events, old_field_items, new_field_items, self.robot_position)

                """
                here I'd like to exclude one item from the set of picked items and emit those events as negative events.
                The assumption is that if any picking was unnecessary, the user would not do it at all
                In the paper, this is the N0_EXCESSIVE_EFFORT principle
            
                """


                for item_desc in list_of_items:
                    modified_collection = list_of_items.copy()
                    modified_collection.remove(item_desc)
                    (speculative_new_robot_items, speculative_new_field_items) = self.pick(modified_collection, speculative=True,
                                                                                           items_on_robot=old_robot_items , items_at_pos=old_field_items)
                    speculative_action_events = self._get_action_events(events, old_field_items, speculative_new_field_items, self.robot_position)
                    forked_events = events.copy()
                    forked_events.append(speculative_action_events)
                    if no_excessive_effort is True:
                        collection_of_negative_events.append(forked_events)
                    else:
                        logging.warning("not adding {} to negative due to no excessive effort".format(forked_events))

            # merge position events to the next pick action (they will be mentioned there)
            # I am not sure why this was necessary. At the moment it doesn't seem to be, commenting out
            # if idx < len(sequence_of_actions) - 1:
            #         if sequence_of_actions[idx+1][0] == constants.PICK and sequence_of_actions[idx][0] == constants.MOVE:
            #             continue

            events.append(action_events)
        """
        here we are adding a prefix (all but the last) 
        to the set events. in the paper, this is called
        NO_EXCESSIVE_TRACE
        """
        if no_excessive_trace is True:
            collection_of_negative_events.append(events[:-1])
        else:
            logging.warning("not adding {} to negative due to no excessive trace principle".format(events[:-1]))

        return (events, pickup_locations, collection_of_negative_events, all_locations)

    def _get_action_events(self, events, old_field_items, new_field_items, robot_position):

        action_events = []
        # when the robot is picking the state is not changing (if it was dry, it will remain dry)

        if not self.robot_position in self.water:
            action_events.append(constants.DRY)

        #adding robot's position
        action_events.append("at_{}_{}".format(robot_position[0], robot_position[1]))

        numbersToWords = {num: constants.numbersToWords[num] for num in constants.numbersToWords if
                          constants.numbersToWords[num] in constants.QUANTIFIERS}


        # adding what happened to items without any restrictions (on the color or the shape)
        if self._get_num_items(old_field_items) > 0 and self._get_num_items(new_field_items) == 0:
            action_events.append("{}_every_x_x_item_at_{}_{}".format(constants.PICK, robot_position[0], robot_position[1]))

        for number in numbersToWords:
            if self._get_num_items(old_field_items) - self._get_num_items(new_field_items) == number:
                action_events.append(
                    "{}_{}_x_x_item_at_{}_{}".format(constants.PICK, numbersToWords[number], robot_position[0],
                                                      robot_position[1]))




        for color in constants.COLORS:
            if self._get_num_items(old_field_items, color=color) > 0 and self._get_num_items(new_field_items,
                                                                                             color=color) == 0:
                action_events.append("{}_every_{}_x_item_at_{}_{}".format(constants.PICK, color, robot_position[0], robot_position[1]))
            for number in numbersToWords:
                if self._get_num_items(old_field_items, color=color) - self._get_num_items(new_field_items,
                                                                                           color=color) == number:
                    action_events.append(
                        "{}_{}_{}_x_item_at_{}_{}".format(constants.PICK, numbersToWords[number], color, robot_position[0], robot_position[1]))

        for shape in constants.SHAPES:
            if self._get_num_items(old_field_items, shape=shape) > 0 and self._get_num_items(new_field_items,
                                                                                             shape=shape) == 0:
                action_events.append("{}_every_x_{}_item_at_{}_{}".format(constants.PICK, shape, robot_position[0], robot_position[1]))
            for number in numbersToWords:
                if self._get_num_items(old_field_items, shape=shape) - self._get_num_items(new_field_items,
                                                                                           shape=shape) == number:
                    action_events.append(
                        "{}_{}_x_{}_item_at_{}_{}".format(constants.PICK, numbersToWords[number], shape, robot_position[0], robot_position[1]))

        for color in constants.COLORS:
            for shape in constants.SHAPES:
                if self._get_num_items(old_field_items, color=color, shape=shape) > 0 and self._get_num_items(
                        new_field_items, color=color, shape=shape) == 0:
                    action_events.append(
                        "{}_every_{}_{}_item_at_{}_{}".format(constants.PICK, color, shape, robot_position[0], robot_position[1]))
                for number in numbersToWords:
                    if self._get_num_items(old_field_items, color=color, shape=shape) - self._get_num_items(
                            new_field_items, color=color, shape=shape) == number:
                        action_events.append(
                            "{}_{}_{}_{}_item_at_{}_{}".format(constants.PICK, numbersToWords[number], color, shape,
                                                         robot_position[0], robot_position[1]))

        return action_events