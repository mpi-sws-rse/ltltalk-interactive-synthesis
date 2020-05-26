from z3 import *
import pdb
try:
    from utils.SimpleTree import SimpleTree, Formula
    from utils.TwoWayDict import TwoWayDict
    import encodingConstants
except:
    from encoding.utils.SimpleTree import SimpleTree, Formula
    from encoding.utils.TwoWayDict import TwoWayDict
    from encoding import encodingConstants

import random
try:
    from utils.Traces import Trace
except:
    from encoding.utils.Traces import Trace


import logging



INFINITY = 10

try:
    import constants
    COLORS = constants.COLORS
    COLOR_CODES = TwoWayDict(constants.COLOR_CODES)

    SHAPES = constants.SHAPES
    SHAPE_CODES = TwoWayDict(constants.SHAPE_CODES)
    ACTION_CODES= TwoWayDict(constants.ACTION_CODES)
    DIRECTION_CODES= TwoWayDict(constants.DIRECTION_CODES)
    NUMBERS_CODES = TwoWayDict(constants.numbersToWords)
except:
    COLORS = ["red", "green", "blue", "yellow"]
    COLOR_CODES = TwoWayDict({"red": 1, "green": 2, "blue": 3, "yellow": 4, "x": 0})
    SHAPES = ["square", "circle", "triangle"]
    SHAPE_CODES = TwoWayDict({"square": 1, "circle": 2, "triangle": 3, "x": 0})

    ACTION_CODES = TwoWayDict({"move": 0, "pick": 1, "pass":2})
    DIRECTION_CODES = TwoWayDict({"left": 0, "right": 1, "up": 2, "down": 3})
    NUMBERS_CODES = TwoWayDict({1: "one", 2: "two", 3: "three", -1: "every"})


DEBUG_UNSAT_CORE = constants.DEBUG_UNSAT_CORE
#DEBUG_UNSAT_CORE = True


class SATOfLTLEncoding:
    """
    - D is the depth of the tree
    - lassoStartPosition denotes the position when the trace values start looping
    - traces is 
      - list of different recorded values (trace)
      - each trace is a list of recordings at time units (time point)
      - each time point is a list of variable values (x1,..., xk)
    """
    def __init__(self, f, init_part_length, lasso_part_length, operators, literals,
                 world_width=12, world_height=9, wall_positions = [], water_locations = None, robot_position = None,
                 items_locations = None, testing=True):

        defaultOperators = [encodingConstants.G, encodingConstants.F, encodingConstants.LNOT, encodingConstants.UNTIL, encodingConstants.LAND,encodingConstants.LOR, encodingConstants.IMPLIES, encodingConstants.X]
        unary = [encodingConstants.G, encodingConstants.F, encodingConstants.LNOT, encodingConstants.X, encodingConstants.ENDS]
        binary = [encodingConstants.LAND, encodingConstants.LOR, encodingConstants.UNTIL, encodingConstants.IMPLIES, encodingConstants.STRICTLY_BEFORE]
        #except for the operators, the nodes of the "syntax table" are additionally the propositional variables 

        if operators == None:
            self.listOfOperators = list(set(f.getAllOperators()))
        else:
            self.listOfOperators = list(operators)

        if encodingConstants.LOR not in self.listOfOperators:
            self.listOfOperators.append(encodingConstants.LOR)
        if encodingConstants.LAND not in self.listOfOperators:
            self.listOfOperators.append(encodingConstants.LAND)
        if encodingConstants.LNOT not in self.listOfOperators:
            self.listOfOperators.append(encodingConstants.LNOT)
        if 'true' not in self.listOfOperators:
            self.listOfOperators.append('true')
        if 'false' not in self.listOfOperators:
            self.listOfOperators.append('false')

        if 'prop' in self.listOfOperators:
            self.listOfOperators.remove('prop')
        try:
            self.world_width = constants.WIDTH
            self.world_height = constants.HEIGHT
        except:
            self.world_width = world_width
            self.world_height = world_height

        self.wall_positions = wall_positions
        self.robot_position = robot_position
        self.water_locations = water_locations
        self.items_locations = items_locations



            
        
        self.unaryOperators = [op for op in self.listOfOperators if op in unary]
        self.binaryOperators = [op for op in self.listOfOperators if op in binary]
        if DEBUG_UNSAT_CORE:
            self.solver = Solver()
        else:
            self.solver = Optimize()
        if testing:
            self.solver.set("timeout", encodingConstants.SOLVER_TIMEOUT)
            # if random.randint(0,1) == 0:
            #     self.solver.set("timeout", 1)
            # else:
            #     self.solver.set("timeout", encodingConstants.SOLVER_TIMEOUT)

        all_subformulas = f.getSetOfSubformulas()
        self.formulaDepth = len(all_subformulas)
        self.literals = literals

        self.listOfVariables = self.literals

        # since we are disambiguating between two formulas, the only locations that matter are really the ones that are
        # mentioned in them
        self.relevant_named_locations, self.var_combinations = self._extract_relevant_locations(self.listOfVariables)


        logging.debug("relevant  locations are: {}".format(self.relevant_named_locations))

        self.variablesToIntMapping = {self.literals[i] : i for i in range(len(self.literals))}
        self.lassoStart = init_part_length
        self.traceLength = init_part_length + lasso_part_length




        self.listOfSubformulas = sorted(list(all_subformulas))

        logging.debug("subformulas of formula {0} are {1}".format(f, self.listOfSubformulas))
        self.indicesOfSubformulas = {self.listOfSubformulas[i] : i for i in range(len(self.listOfSubformulas))}
        logging.debug(self.indicesOfSubformulas)


    def _assignIndicesToSubformulas(self, number_of_subformulas):
        pass


    """
    IG:
    this is a very specific function in that it depends a lot on how variables are named.
    It would probably be a good idea to move it elsewhere in the future.
    """
    def _extract_relevant_locations(self, vars):
        relevant_locations = []
        interesting_combinations = {}

        for var in vars:
            var_items = []
            var_items_string = var.split('_')
            for i in var_items_string:
                try:
                    var_items.append(int(i))
                except:
                    var_items.append(i)

            if var_items[0] == "pick" or (var_items[0] == "at" and len(var_items) == 3):
                loc = (var_items[-2], var_items[-1])
                if not loc in relevant_locations:
                    relevant_locations.append(loc)

            if not var_items in interesting_combinations.values():
                interesting_combinations[var] = var_items
        return relevant_locations, interesting_combinations

    def getInformativeVariables(self):
        res = []
        res += [v for v in self.x.values()]
        res += [v for v in self.l.values()]
        res += [v for v in self.r.values()]


        return res
    """    
    the working variables are 
        - x[i][o]: i is a subformula (row) identifier, o is an operator or a propositional variable. Meaning is "subformula i is an operator (variable) o"
        - l[i][j]:  "left operand of subformula i is subformula j"
        - r[i][j]: "right operand of subformula i is subformula j"
        - y[i][t]: semantics of formula i in time point t
    """
    def encodeFormula(self, unsatCore=True):
        self.operatorsAndVariables = self.listOfOperators + self.listOfVariables




        
        self.x = { (i, o) : Bool('x_'+str(i)+'_'+str(o)) for i in range(self.formulaDepth) for o in self.operatorsAndVariables }

        self.l = {(parentOperator, childOperator) : Bool('l_'+str(parentOperator)+'_'+str(childOperator))\
                                                 for parentOperator in range(1, self.formulaDepth)\
                                                 for childOperator in range(parentOperator)}
        self.r = {(parentOperator, childOperator) : Bool('r_'+str(parentOperator)+'_'+str(childOperator))\
                                                 for parentOperator in range(1, self.formulaDepth)\
                                                 for childOperator in range(parentOperator)}

        self.y = { (i, timePoint) : Bool('y_'+str(i)+'_'+str(timePoint))\
                  for i in range(self.formulaDepth)\
                  for timePoint in range(self.traceLength)}

        self.items = {(x,y, color, shape, tmstp) : Int("item_{}_{}_{}_{}_{}".format(x,y,color, shape, tmstp))
                      for (x,y) in self.relevant_named_locations
                      for color in COLORS
                      for shape in SHAPES
                      for tmstp in range(self.traceLength)
                      }

        self.robot_position_x = {tmstp: Int("robot_x_{}".format(tmstp)) for tmstp in range(self.traceLength)}
        self.robot_position_y = {tmstp: Int("robot_y_{}".format(tmstp)) for tmstp in range(self.traceLength)}

        if not self.robot_position is None:
            self.solver.add(self.robot_position_x[0] == self.robot_position[0])
            self.solver.add(self.robot_position_y[0] == self.robot_position[1])

        if not self.items_locations is None:
            self.set_up_items(items_locations = self.items_locations)





        self.chosen_action = {tmstp: Int("action_{}".format(tmstp)) for tmstp in range(self.traceLength-1)}
        self.direction = {tmstp: Int("direction_{}".format(tmstp)) for tmstp in range(self.traceLength-1)}

        self.picked_color_shape = {(color, shape, tmstp):Int("picked_{}_{}_{}".format(color, shape, tmstp))
                                for color in COLORS
                                for shape in SHAPES
                                for tmstp in range(self.traceLength-1)}

        self.water = {(x,y): Int("water_at_{}_{}".format(x,y)) for x in range(self.world_width) for y in range(self.world_height)}

        self.wall = {(x,y): Int("wall_at_{}_{}".format(x,y)) for x in range(self.world_width) for y in range(self.world_height)}

        self.set_up_walls(wall_locations=self.wall_positions)

        if not self.water_locations is None:
            self.set_up_water(water_locations = self.water_locations)

        self.field_type_restrictions()

        self.connect_picked_items_with_items()






        self.witnessTrace = {(var, tmstp) : Bool('cex_'+str(var)+"_"+str(tmstp))\
                                    for var in self.listOfVariables\
                                    for tmstp in range(self.traceLength)}



        if DEBUG_UNSAT_CORE:
            self.solver.set(unsat_core=unsatCore)




        self.setOperatorValues()



        self.propVariablesSemantics()


        self.operatorsSemantics()

        if DEBUG_UNSAT_CORE:
            self.solver.assert_and_track(self.y[(self.formulaDepth-1, 0)], "evaluation should be true")
        else:
            self.solver.add(self.y[(self.formulaDepth - 1, 0)])

        self.worldSpecifics()

        #self.guideTowardsSolution()


        if logging.root.getEffectiveLevel() == logging.DEBUG:
            filename = "debug_files/solverExport.txt"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w") as solver_export:
                solver_export.write(self.solver.sexpr())

        if not DEBUG_UNSAT_CORE:
            self.minimize_num_items()
            self.minimize_num_picked_items()
            #self.maximize_num_passes()
            self.softly_require_number_of_passes()
            if self.water_locations is None:
                self.optimize_num_water_fields()








    def field_type_restrictions(self):
        self.solver.add(And([
            And(
                self.water[(x,y)] >= 0,
                self.water[(x,y)] + self.wall[(x,y)] <= 1,
                self.water[(x,y)] <= 1
            )
            for x in range(self.world_width) for y in range(self.world_height)
        ]))


        self.solver.add(
            And([
                Implies(
                    Sum([self.items[(x,y,c,s,0)] for c in COLORS for s in SHAPES]) > 0,
                    And(
                        self.wall[(x,y)] == 0,
                        #self.water[(x,y)] == 0
                    )
                )
                # only here there might be any items
                for (x,y) in self.relevant_named_locations
            ])
        )

    def set_up_water(self, water_locations):
        for x in range(self.world_width):
            for y in range(self.world_height):
                if (x,y) in water_locations:
                    self.solver.add(self.water[(x,y)] == 1)
                else:
                    self.solver.add(self.water[(x, y)] == 0)

    def set_up_items(self, items_locations):
        for (x, y) in self.relevant_named_locations:
            for c in COLORS:
                for s in SHAPES:
                    if (x,y, c, s) in items_locations:
                        self.solver.add(self.items[(x,y,c,s,0)] == items_locations[(x,y,c,s)])
                    else:
                        self.solver.add(self.items[(x, y, c, s, 0)] == 0)



    def set_up_walls(self, wall_locations):
        for x in range(self.world_width):
            for y in range(self.world_height):
                if (x,y) in wall_locations:
                    self.solver.add(self.wall[(x,y)] == 1)
                else:
                    self.solver.add(self.wall[(x, y)] == 0)

    def minimize_num_picked_items(self):
        self.total_picked_items = Sum([
            self.picked_color_shape[(c,s,tmstp)]
            for c in COLORS
            for s in SHAPES
            for tmstp in range(self.traceLength - 1)
        ])

        self.solver.minimize(self.total_picked_items)

    def softly_require_number_of_passes(self):
        self.pass_or_not = {tmstp: Int("pass_{}".format(tmstp)) for tmstp in range(self.traceLength - 1)}

        cond = And(
            And([
                Implies(
                    self.chosen_action[tmstp] == ACTION_CODES[constants.PASS],
                    self.pass_or_not[tmstp] == 1
                )
                for tmstp in range(self.traceLength - 1)
            ]),
            And([
                Implies(
                    Not(self.chosen_action[tmstp] == ACTION_CODES[constants.PASS]),
                    self.pass_or_not[tmstp] == 0
                )
                for tmstp in range(self.traceLength - 1)
            ])
        )

        self.solver.add(cond)
        self.total_passes = Sum([
            self.pass_or_not[tmstp]
            for tmstp in range(self.traceLength - 1)
        ])
        self.solver.add(self.total_passes < self.traceLength-1)
        # for i in range(constants.STEP_COARSE_RANGE):
        #     self.solver.add_soft(self.total_passes > i)
        self.solver.maximize(self.total_passes)


    # if passes can be used, use them (in order to avoid superfluous moves)
    def maximize_num_passes(self):
        #self.chosen_action = {tmstp: Int("action_{}".format(tmstp)) for tmstp in range(self.traceLength - 1)}
        self.pass_or_not = {tmstp : Int("pass_{}".format(tmstp)) for tmstp in range(self.traceLength-1)}

        cond = And(
                    And([
                        Implies(
                            self.chosen_action[tmstp] == ACTION_CODES[constants.PASS],
                            self.pass_or_not[tmstp] == 1
                        )
                        for tmstp in range(self.traceLength-1)
                    ]),
                    And([
                        Implies(
                            Not(self.chosen_action[tmstp] == ACTION_CODES[constants.PASS]),
                            self.pass_or_not[tmstp] == 0
                        )
                        for tmstp in range(self.traceLength-1)
                    ])
            )

        self.solver.add(cond)
        self.total_passes = Sum([
            self.pass_or_not[tmstp]
            for tmstp in range(self.traceLength-1)
        ])

        self.solver.maximize(self.total_passes)

    def connect_picked_items_with_items(self):

        connection = And([
                self.picked_color_shape[(c,s,t)] ==
                Sum([
                    (self.items[(x,y,c,s,t)] - self.items[(x,y,c,s,t+1)])
                    for (x,y) in self.relevant_named_locations
                    ])
                for c in COLORS
                for s in SHAPES
                for t in range(self.traceLength-1)
        ])
        if DEBUG_UNSAT_CORE:
            self.solver.assert_and_track(connection, "picked items and num of items at locations connection")
        else:
            self.solver.add(connection)



    def minimize_num_items(self):
        self.total_items = Sum([self.items[(x,y,c,s,0)]
                                for (x,y) in self.relevant_named_locations
                                for c in COLORS
                                for s in SHAPES
                                ])

        # otherwise self.total_items is empty
        if len(self.relevant_named_locations) > 0:
            self.solver.minimize(self.total_items)

    def optimize_num_water_fields(self):
        self.total_water_fields = Sum([
            self.water[(x,y)]
            for x in range(self.world_width)
            for y in range(self.world_height)
        ])

        self.solver.minimize(self.total_water_fields)
        #self.solver.add(self.total_water_fields < 10)

    def emitted_events_constraints(self):
        if logging.root.getEffectiveLevel() == logging.DEBUG:
            filename = "debug_files/solverExportBeforeEmit.txt"
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            with open(filename, "w") as solver_export:
                solver_export.write(self.solver.sexpr())

        for v in self.listOfVariables:

            v_desc = self.var_combinations[v]


            # emitting upon pick event

            # if quantity_desc == 1:
            #     quantity_desc = "one"

            action_desc = v_desc[0]
            if action_desc == "pick":
                action_desc = v_desc[0]
                quantity_desc = v_desc[1]
                color_desc = v_desc[2]
                shape_desc = v_desc[3]
                x_pos_desc = v_desc[6]
                y_pos_desc = v_desc[7]
                if quantity_desc in constants.numbersToWords:
                    quantity_desc = constants.numbersToWords[quantity_desc]

                if quantity_desc == "every":
                    goal_relation = lambda post, pre, num: And(pre > 0, post == 0)
                else:
                    goal_relation = lambda post, pre, num: (pre - post == num)



                # THIS SHOULD BE TAKEN CARE OF BY THE MINIMIZATION... LET'S SEE
                # # add a soft constraint to make every pick happen only if necessary
                #
                # if not DEBUG_UNSAT_CORE:
                #     for c in COLORS:
                #         logging.debug("adding soft")
                #         for s in SHAPES:
                #             for t in range(self.traceLength-1):
                #                 self.solver.add_soft(
                #                     self.items[(x_pos_desc, y_pos_desc, c, s, t)] == 0
                #                 )


                # special case when there is no specification neither on color nor on shape
                if color_desc == 'x' and shape_desc == 'x':
                    nothing_fixed_sum = {t: Sum([self.items[(x_pos_desc, y_pos_desc, c, s, t)]
                                                 for c in COLORS for s in SHAPES])
                                         for t in range(self.traceLength)}

                    cond = And([
                                Implies(
                                    self.x[(i, v)],
                                    goal_relation(nothing_fixed_sum[tmstp + 1], nothing_fixed_sum[tmstp], NUMBERS_CODES[quantity_desc])
                                    ==
                                    self.y[(i, tmstp + 1)]
                                )
                                for tmstp in range(self.traceLength - 1) for i in range(self.formulaDepth)
                            ])
                    if DEBUG_UNSAT_CORE:
                        self.solver.assert_and_track(
                            cond,
                            "emitted events for var {}".format(v)
                        )
                    else:
                        self.solver.add(
                            cond
                        )



                # there is a restriction on shape, but not on color
                elif color_desc == 'x' and not shape_desc == 'x':
                    shape_fixed_sum = {t: Sum([self.items[(x_pos_desc, y_pos_desc, c, shape_desc, t)] for c in COLORS])
                                       for t in range(self.traceLength)}



                    cond = And([
                                Implies(
                                    self.x[(i, v)],
                                    goal_relation(shape_fixed_sum[tmstp + 1], shape_fixed_sum[tmstp], NUMBERS_CODES[quantity_desc])
                                    ==
                                    self.y[(i, tmstp + 1)]
                                )
                                for tmstp in range(self.traceLength - 1) for i in range(self.formulaDepth)
                            ])

                    if DEBUG_UNSAT_CORE:
                        self.solver.assert_and_track(
                            cond,
                            "emitted events for var {}".format(v)
                        )
                    else:
                        self.solver.add(
                            cond
                        )

                    # there is a restriction on shape, but not on color
                elif not color_desc == 'x' and shape_desc == 'x':

                    color_fixed_sum = {t: Sum([self.items[(x_pos_desc, y_pos_desc, color_desc, s, t)] for s in SHAPES])
                                       for t in range(self.traceLength)}

                    cond = And([
                                Implies(
                                    self.x[(i, v)],
                                    goal_relation(color_fixed_sum[tmstp + 1], color_fixed_sum[tmstp], NUMBERS_CODES[quantity_desc])
                                    ==
                                    self.y[(i, tmstp + 1)]
                                )
                                for tmstp in range(self.traceLength - 1) for i in range(self.formulaDepth)
                            ])

                    if DEBUG_UNSAT_CORE:
                        self.solver.assert_and_track(
                            cond,
                            "emitted events for var {}".format(v)
                        )
                    else:
                        self.solver.add(
                            cond
                        )

                # there is a restriction on both color and shape
                elif not color_desc == 'x' and not shape_desc == 'x':
                    # this is a trivial summ, summing only one element

                    color_shape_fixed_sum = {t: Sum([self.items[(x_pos_desc, y_pos_desc, color_desc, shape_desc, t)]])
                                       for t in range(self.traceLength)}

                    cond = And([
                                Implies(
                                    self.x[(i, v)],
                                    goal_relation(color_shape_fixed_sum[tmstp + 1], color_shape_fixed_sum[tmstp], NUMBERS_CODES[quantity_desc])
                                    ==
                                    self.y[(i, tmstp + 1)]
                                )
                                for tmstp in range(self.traceLength - 1) for i in range(self.formulaDepth)
                            ])
                    if DEBUG_UNSAT_CORE:
                        self.solver.assert_and_track(
                            cond,
                            "emitted events for var {}".format(v)
                        )
                    else:
                        self.solver.add(
                            cond
                        )


            elif v_desc[0] == "at":
                quality_desc = v_desc[1]


                if quality_desc == "dry":
                    cond = And([
                            Implies(
                                self.x[(i,v)],
                                And([
                                    Implies(
                                        And(self.robot_position_x[tmstp] == x, self.robot_position_y[tmstp] == y),
                                        (self.water[(x,y)] == 0) == self.y[(i, tmstp)]
                                    )
                                    for x in range(self.world_width) for y in range(self.world_height)
                                ])
                            )
                            for tmstp in range(self.traceLength) for i in range(self.formulaDepth)
                        ])


                    if DEBUG_UNSAT_CORE:
                        self.solver.assert_and_track(
                            cond,
                            "emitted dry events for {}".format(v)
                        )
                    else:
                        self.solver.add(cond)


                # at_location case
                else:
                    # at special location case
                    if v_desc[1] in constants.SPECIAL_NAMES:
                        x_pos_desc = constants.SPECIAL_NAMES[v_desc[1]][0]
                        y_pos_desc = constants.SPECIAL_NAMES[v_desc[1]][1]
                    else:
                        x_pos_desc = v_desc[1]
                        y_pos_desc = v_desc[2]

                    cond = And([
                                Implies(
                                    self.x[(i, v)],
                                    And([
                                         self.robot_position_x[tmstp] == x_pos_desc,
                                         self.robot_position_y[tmstp] == y_pos_desc
                                         ])
                                    ==
                                    self.y[(i, tmstp)]
                                    )
                                for tmstp in range(self.traceLength) for i in range(self.formulaDepth)
                            ])

                    if DEBUG_UNSAT_CORE:
                        self.solver.assert_and_track(cond, "emitted at loc events for {}".format(v))
                    else:
                        self.solver.add(cond)





        
    def worldSpecifics(self):




        # robot's location should be inside world
        self.solver.add(And([And(self.robot_position_x[tmstp] < self.world_width, self.robot_position_x[tmstp] >= 0)
                                          for tmstp in range(self.traceLength)]))
        self.solver.add(And([And(self.robot_position_y[tmstp] < self.world_height, self.robot_position_y[tmstp]>=0)
                                          for tmstp in range(self.traceLength)]))

        # robot's location should never be on the wall
        self.solver.add(
            And([
                Not(And(self.robot_position_x[tmstp] == x, self.robot_position_y[tmstp] ==y, self.wall[x,y] == 1))
                for tmstp in range(self.traceLength)
                for x in range(self.world_width)
                for y in range(self.world_height)
            ])
        )

        # action is always either 0 or 1 or 2

        self.solver.add(And([self.chosen_action[tmstp] >= 0 for tmstp in range(self.traceLength-1)]))
        self.solver.add(And([self.chosen_action[tmstp] < len(ACTION_CODES) for tmstp in range(self.traceLength-1)]))

        # two consecutive pick actions are not allowed (we insist on having all picks from the same place grouped together)
        self.solver.add(
            And([
                Implies(
                    self.chosen_action[tmstp] == ACTION_CODES["pick"],
                    Not(self.chosen_action[tmstp+1] == ACTION_CODES["pick"])
                )
                for tmstp in range(self.traceLength-2)
            ])
        )

        # number of items should always be non-negative
        cond = And([
                    self.items[(x, y, color, shape, tmstp)] >= 0
                    for (x,y) in self.relevant_named_locations
                    for shape in SHAPES
                    for color in COLORS
                    for tmstp in range(self.traceLength)
                ])
        if DEBUG_UNSAT_CORE:
            self.solver.assert_and_track(
                    cond,
                "number of items is always non-negative"
            )
        else:
            self.solver.add(cond)

        # if the chosen action is move, then direction is restricted to one of the available directions
        cond = And([
                Implies(
                    self.chosen_action[tmstp] == ACTION_CODES["move"],
                    And(self.direction[tmstp] >= 0, self.direction[tmstp] < len(DIRECTION_CODES))
                )
                for tmstp in range(self.traceLength-1)
            ])
        if DEBUG_UNSAT_CORE:
            self.solver.assert_and_track(
                cond,
                "moves imply restriction on chosen direction"
            )
        else:
            self.solver.add(cond)


        # if the chosen action is pick, then quantity, color and shape have to be restricted
        cond = And([
                Implies(
                    self.chosen_action[tmstp] == ACTION_CODES["pick"],
                    And([
                        self.picked_color_shape[(c, s, tmstp)] >= 0,
                        self.picked_color_shape[(c, s, tmstp)] <= INFINITY,
                        Or([self.picked_color_shape[(c1, s1, tmstp)] > 0
                            for c1 in COLORS
                            for s1 in SHAPES
                            ])
                    ])
                )
                for tmstp in range(self.traceLength-1)
                for c in COLORS
                for s in SHAPES
            ])
        if DEBUG_UNSAT_CORE:
            self.solver.assert_and_track(
                cond,
                "picks imply restrictions for description of items"
            )
        else:
            self.solver.add(cond)


        # if the move action is chosen, how that changes robot position and items on the map
        cond = And([
                Implies(
                    self.chosen_action[tmstp] == ACTION_CODES["move"],
                    And([
                        Implies(
                            self.direction[tmstp] == DIRECTION_CODES["left"],
                            And(
                                self.robot_position_x[tmstp + 1] == self.robot_position_x[tmstp] - 1,
                                self.robot_position_y[tmstp + 1] == self.robot_position_y[tmstp]
                            )
                        ),
                        Implies(
                            self.direction[tmstp] == DIRECTION_CODES["right"],
                            And(
                                self.robot_position_x[tmstp + 1] == self.robot_position_x[tmstp] + 1,
                                self.robot_position_y[tmstp + 1] == self.robot_position_y[tmstp]
                            )
                        ),
                        Implies(
                            self.direction[tmstp] == DIRECTION_CODES["up"],
                            And(
                                self.robot_position_x[tmstp + 1] == self.robot_position_x[tmstp],
                                self.robot_position_y[tmstp + 1] == self.robot_position_y[tmstp] + 1
                            )
                        ),
                        Implies(
                            self.direction[tmstp] == DIRECTION_CODES["down"],
                            And(
                                self.robot_position_x[tmstp + 1] == self.robot_position_x[tmstp],
                                self.robot_position_y[tmstp + 1] == self.robot_position_y[tmstp] - 1
                            )
                        ),
                        # nothing changes for the state of the items
                        And([self.items[(x, y, color, shape, tmstp + 1)] == self.items[(x, y, color, shape, tmstp)]
                             for (x,y) in self.relevant_named_locations
                             for shape in SHAPES
                             for color in COLORS
                             ])
                    ])
                )
                for tmstp in range(self.traceLength - 1)
            ])
        if DEBUG_UNSAT_CORE:
            self.solver.assert_and_track(
                cond,
                "effects of choosing move action"
            )
        else:
            self.solver.add(cond)

        # alternatively, if the pick action is chosen, how that changes the items on the field
        cond = And([
                Implies(
                    self.chosen_action[tmstp] == ACTION_CODES["pick"],
                    And(
                        # update of items at the location where the robot is picking
                        And([
                            And(
                                # changes regarding the position at which the robot is standing
                                Implies(
                                    And(
                                        self.robot_position_x[tmstp] == x,
                                        self.robot_position_y[tmstp] == y
                                    ),
                                    And([
                                        self.items[(x,y,c,s,tmstp+1)] == self.items[(x,y,c,s,tmstp)] - self.picked_color_shape[(c,s,tmstp)]
                                        for c in COLORS for s in SHAPES
                                    ])
                                ),
                                # nothing changes for all other positions
                                Implies(
                                    Not(
                                        And(
                                            self.robot_position_x[tmstp] == x,
                                            self.robot_position_y[tmstp] == y
                                        ),
                                    ),
                                    And([
                                        self.items[(x, y, c, s, tmstp + 1)] == self.items[(x, y, c, s, tmstp)]
                                        for c in COLORS for s in SHAPES
                                    ])
                                )
                            )
                            for (x,y) in self.relevant_named_locations
                        ]),

                        #nothing changes regarding position
                        And(
                            self.robot_position_x[tmstp+1] == self.robot_position_x[tmstp],
                            self.robot_position_y[tmstp+1] == self.robot_position_y[tmstp]
                        )
                    )
                )
                for tmstp in range(self.traceLength - 1)
            ])

        if DEBUG_UNSAT_CORE:
            self.solver.assert_and_track(
                cond,
                "effects of choosing pick action"
            )
        else:
            self.solver.add(cond)


        # finally, if the pass action is chosen, nothing happens
        cond = And([
            Implies(
                self.chosen_action[tmstp] == ACTION_CODES[constants.PASS],
                And(
                    self.robot_position_x[tmstp+1] == self.robot_position_x[tmstp],
                    self.robot_position_y[tmstp+1] == self.robot_position_y[tmstp],
                    And([
                        self.items[(x,y,c,s,tmstp+1)] == self.items[(x,y,c,s,tmstp)]
                        for (x,y) in self.relevant_named_locations
                        for c in COLORS
                        for s in SHAPES
                    ])
                )
            )
            for tmstp in range(self.traceLength - 1)
        ])

        if DEBUG_UNSAT_CORE:
            self.solver.assert_and_track(
                cond,
                "effects of chossing pass action"
            )
        else:
            self.solver.add(cond)

        # we also want to restrict picking: one can only pick/drop from relevant locations
        cond = And([
            Implies(
                self.chosen_action[tmstp] == ACTION_CODES["pick"],
                Or([
                    And(self.robot_position_x[tmstp] == x, self.robot_position_y[tmstp] == y)
                    for (x,y) in self.relevant_named_locations
                ])
            )
            for tmstp in range(self.traceLength-1)
        ])
        if DEBUG_UNSAT_CORE:
            self.solver.assert_and_track(
                cond,
                "restricting picking to relevant locations"
            )
        else:
            self.solver.add(cond)

        self.emitted_events_constraints()










    
    def propVariablesSemantics(self):

        for (idx, subf) in enumerate(self.listOfSubformulas):
            if subf.label in self.listOfVariables:
                cond = And([
                            Implies(
                                self.x[(i, subf.label)],
                                And([self.y[(i, tmstp)] == self.witnessTrace[(subf.label, tmstp)] for tmstp in range(self.traceLength)]),
                            )
                            for i in range(self.formulaDepth)
                            ])
                if DEBUG_UNSAT_CORE:
                    self.solver.assert_and_track(
                        cond,
                        "cex and y values connection at position {0} for var {1}".format(str(idx), subf.label)
                    )
                else:
                    self.solver.add(
                        cond
                    )

                # we want to make sure that picked_... vars at position 0 are always 0 (because it is just a beginning,
                # nothing has been picked yet)
                var_desc = subf.label.split('_')
                if var_desc[0] == "pick":
                    self.solver.add(
                        And([
                            Implies(
                                self.x[(i, subf.label)],
                                Not(self.y[(i, 0)])
                            )
                            for i in range(self.formulaDepth)
                        ])
                    )

                # else:
                #     # if var is at_dry, we want to make sure that it is true if and only if robot is currently at location
                #     # dry
                #     if var_desc[1] == "dry":
                #         self.solver.add(
                #             And([
                #                 Implies(
                #                     self.x[(i, subf.label)],
                #                     self.y[(i,0)] == Not(self.water[]
                #                 )
                #             ])
                #         )

        
    

    
    def setOperatorValues(self):
        #pdb.set_trace()
        for (idx, subf) in enumerate(self.listOfSubformulas):
            self.solver.add(self.x[(idx, subf.label)])
            self.solver.add(And([Not(self.x[(idx, operator)]) for operator in self.operatorsAndVariables if not operator == subf.label]))
            if not subf.left is None:
                self.solver.add(self.l[(idx, self.indicesOfSubformulas[subf.left])])
                self.solver.add(And([Not(self.l[(idx, i)]) for i in range(idx) if not i == self.indicesOfSubformulas[subf.left]]))
            else:
                self.solver.add(And([Not(self.l[(idx, i)]) for i in range(idx)]))

            if not subf.right is None:
                self.solver.add(self.r[(idx, self.indicesOfSubformulas[subf.right])])
                self.solver.add(And([Not(self.r[(idx, i)]) for i in range(idx)if not i == self.indicesOfSubformulas[subf.right]]))
            else:
                self.solver.add(And([Not(self.r[(idx, i)]) for i in range(idx)]))



    def _nextPos(self, currentPos):
        if currentPos == self.traceLength - 1:
            raise ValueError("Only finite traces: no next positions after {}".format(currentPos))
        else:
            return currentPos + 1
    def _futurePos(self, currentPos):
        return list(range(currentPos, self.traceLength))

    def operatorsSemantics(self):



        for (idx, subf) in enumerate(self.listOfSubformulas):
            explanation = "operator {0} at depth {1}".format(str(subf.label), idx)
            if subf.label == encodingConstants.LOR:
                cond = And([self.y[(idx, tmstp)] ==
                         Or(\
                            self.y[(self.indicesOfSubformulas[subf.left], tmstp)],
                             self.y[(self.indicesOfSubformulas[subf.right], tmstp)]
                        )
                         for tmstp in range(self.traceLength)
                         ])
                if DEBUG_UNSAT_CORE:
                    self.solver.assert_and_track(
                        cond,
                        explanation
                    )
                else:
                    self.solver.add(cond)

            elif subf.label == "false":
                cond = And([Not(self.y[(idx, tmstp)])
                         for tmstp in range(self.traceLength)
                         ])
                if DEBUG_UNSAT_CORE:
                    self.solver.assert_and_track(
                        cond,
                        explanation
                    )
                else:
                    self.solver.add(cond)

            elif subf.label == "true":
                cond = And([self.y[(idx, tmstp)]
                         for tmstp in range(self.traceLength)
                         ])
                if DEBUG_UNSAT_CORE:
                    self.solver.assert_and_track(
                        cond,
                        explanation
                    )
                else:
                    self.solver.add(cond)

            elif subf.label == encodingConstants.LAND:
                cond = And([self.y[(idx, tmstp)] ==
                         And( \
                             self.y[(self.indicesOfSubformulas[subf.left], tmstp)],
                             self.y[(self.indicesOfSubformulas[subf.right], tmstp)]
                         )
                         for tmstp in range(self.traceLength)
                         ])
                if DEBUG_UNSAT_CORE:
                    self.solver.assert_and_track(
                        cond,
                        explanation
                    )
                else:
                    self.solver.add(cond)


            elif subf.label == encodingConstants.LNOT:
                cond = And([self.y[(idx, tmstp)] ==
                         Not( \
                             self.y[(self.indicesOfSubformulas[subf.left], tmstp)]
                         )
                         for tmstp in range(self.traceLength)
                         ])
                if DEBUG_UNSAT_CORE:
                    self.solver.assert_and_track(
                        cond,
                        explanation
                    )
                else:
                    self.solver.add(cond)

            elif subf.label == encodingConstants.IMPLIES:
                cond = And([self.y[(idx, tmstp)] ==
                         Implies( \
                             self.y[(self.indicesOfSubformulas[subf.left], tmstp)],
                             self.y[(self.indicesOfSubformulas[subf.right], tmstp)]
                         )
                         for tmstp in range(self.traceLength)
                         ])
                if DEBUG_UNSAT_CORE:
                    self.solver.assert_and_track(
                        cond,
                        explanation
                    )
                else:
                    self.solver.add(cond)

            elif subf.label == encodingConstants.G:
                cond = And([self.y[(idx, tmstp)] ==
                         And( [\
                              self.y[(self.indicesOfSubformulas[subf.left], futureTmstp)]
                             for futureTmstp in self._futurePos(tmstp)]
                         )
                         for tmstp in range(self.traceLength)
                         ])
                if DEBUG_UNSAT_CORE:
                    self.solver.assert_and_track(
                        cond,
                        explanation
                    )
                else:
                    self.solver.add(cond)

            elif subf.label == encodingConstants.ENDS:
                cond = And([
                        self.y[(idx, tmstp)] == self.y[(self.indicesOfSubformulas[subf.left], self.traceLength-1)]
                        for tmstp in range(self.traceLength)
                    ])
                if DEBUG_UNSAT_CORE:
                    self.solver.assert_and_track(
                        cond,
                        explanation
                    )
                else:
                    self.solver.add(cond)

            # p before q
            elif subf.label == encodingConstants.BEFORE:
                condition = And([
                        self.y[(idx, tmstp)]
                        ==
                        Or([
                            And([
                                self.y[(self.indicesOfSubformulas[subf.left], nearFuture)],
                                self.y[(self.indicesOfSubformulas[subf.right], distantFuture)]
                            ])
                            for nearFuture in self._futurePos(tmstp) for distantFuture in self._futurePos(nearFuture)
                        ])
                        for tmstp in range(self.traceLength)
                    ])
                if DEBUG_UNSAT_CORE:
                    self.solver.assert_and_track(
                        condition,
                        explanation
                    )
                else:
                    self.solver.add(condition)

                #logging.debug(condition)

            # p strictly before q
            elif subf.label == encodingConstants.STRICTLY_BEFORE:
                condition = And([
                        self.y[(idx, tmstp)]
                        ==
                        Or([
                            And([
                                self.y[(self.indicesOfSubformulas[subf.left], nearFuture)],
                                self.y[(self.indicesOfSubformulas[subf.right], distantFuture)]
                            ])
                            for nearFuture in self._futurePos(tmstp) for distantFuture in self._futurePos(nearFuture)[1:]
                        ])
                        for tmstp in range(self.traceLength)
                    ])
                if DEBUG_UNSAT_CORE:
                    self.solver.assert_and_track(
                        condition,
                        explanation
                    )
                else:
                    self.solver.add(condition)






            elif subf.label == encodingConstants.F:
                cond = And([self.y[(idx, tmstp)] ==
                         Or( [\
                              self.y[(self.indicesOfSubformulas[subf.left], futureTmstp)]
                             for futureTmstp in self._futurePos(tmstp)]
                         )
                         for tmstp in range(self.traceLength)
                         ])
                if DEBUG_UNSAT_CORE:
                    self.solver.assert_and_track(
                        cond,
                        explanation
                    )
                else:
                    self.solver.add(cond)

            elif subf.label == encodingConstants.X:
                cond = And([self.y[(idx, tmstp)] == self.y[(idx, self._nextPos(tmstp))]
                         for tmstp in range(self.traceLength)
                         ])
                if DEBUG_UNSAT_CORE:
                    self.solver.assert_and_track(
                        cond,
                        explanation
                    )
                else:
                    self.solver.add(cond)

            elif subf.label == encodingConstants.UNTIL:
                cond = And([ \
                        self.y[(idx, tmstp)] == \
                        Or([ \
                            And( \
                                [self.y[(self.indicesOfSubformulas[subf.left], futurePos)] for futurePos in self._futurePos(tmstp)[0:qIndex]] + \
                                [self.y[(self.indicesOfSubformulas[subf.right], self._futurePos(tmstp)[qIndex])]] \
                                ) \
                            for qIndex in range(len(self._futurePos(tmstp))) \
                            ]) \
                        for tmstp in range(self.traceLength)])
                if DEBUG_UNSAT_CORE:
                    self.solver.assert_and_track(
                        cond,
                        explanation
                    )
                else:
                    self.solver.add(cond)




    def reconstructWholeFormula(self, model):
        return self.reconstructFormula(self.formulaDepth-1, model)

    def reconstructFormula(self, rowId, model):

        def getValue(row, vars):
            tt = [k[1] for k in vars if k[0] == row and model[vars[k]] == True]
            if len(tt) > 1:
                raise Exception("more than one true value")
            else:
                return tt[0]

        operator = getValue(rowId, self.x)
        if operator in self.listOfVariables:
            return Formula(self.traces.literals[int(operator)])

        elif operator in self.unaryOperators:
            leftChild = getValue(rowId, self.l)
            return Formula([operator, self.reconstructFormula(leftChild, model)])
        elif operator in self.binaryOperators:
            leftChild = getValue(rowId, self.l)
            rightChild = getValue(rowId, self.r)
            return Formula([operator, self.reconstructFormula(leftChild, model), self.reconstructFormula(rightChild, model)])

    def reconstructWitnessTrace(self, model):

        if logging.root.getEffectiveLevel() == logging.DEBUG:
            filename = "debug_files/model.txt"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w") as model_file:
                for idx in range(len(model)):
                    model_file.writelines("{}: {}\n".format(model[idx], model[model[idx]]))


        witnessTraceVector = []
        actionWitnessVector = []
        world = {"robot":{}, "width": self.world_width, "height":self.world_height}

        robot_pos_x = model[self.robot_position_x[0]]
        robot_pos_y = model[self.robot_position_y[0]]
        world["robot"]["x"] = str(robot_pos_x)
        world["robot"]["y"] = str(robot_pos_y)

        world["items"] = []
        for x in range(self.world_width):
            for y in range(self.world_width):
                try:
                    water = model[self.water[(x,y)]].as_long()
                except:
                    water = 0
                if water == 1:
                    world["items"].append({"x":x, "y":y, "type":"water", "color":"null", "shape":"null", "quantity": "null"})

                try:
                    wall = model[self.wall[(x,y)]].as_long()
                except:
                    wall = 0
                if wall == 1:
                    world["items"].append({"x":x, "y":y, "type":"wall", "color":"null", "shape":"null", "quantity": "null"})
                for c in COLORS:
                    for s in SHAPES:

                        try:
                            num_items = model[self.items[(x,y,c,s,0)]].as_long()
                        except:
                            num_items = 0
                        if num_items > 0:
                            world["items"].append({"x":x, "y":y, "type":"item", "color":c, "shape":s, "quantity": num_items})



        #logging.info("initial world is \n{}\n\n".format(world))

        for tmstp in range(self.traceLength):
            singleTimestepData = []
            actionSingleTimestepData = []

            for var in self.listOfVariables:
                try:
                    g = model[self.witnessTrace[(var, tmstp)]]
                except:
                    g = False

                if g is None:
                    el = random.randint(0,1)
                    logging.debug("witness: {0} at tmstp {1} is chosen randomly ot be".format(var, str(tmstp), str(el)))
                else:
                    if g == True:
                        el = 1
                    elif g == False:
                        el = 0
                    else:
                        pdb.set_trace()
                    logging.debug("witness: {0} at tmstp {1} has to be {2}".format(var, str(tmstp), str(el)))
                singleTimestepData.append(el)

            robot_pos_x = model[self.robot_position_x[tmstp]]
            robot_pos_y = model[self.robot_position_y[tmstp]]

            if robot_pos_x is None:
                robot_pos_x = "undetermined"
            if robot_pos_y is None:
                robot_pos_y = "undetermined"
            logging.debug("robot position at tmstp {} is {}".format(tmstp, (robot_pos_x, robot_pos_y)))


            if tmstp < self.traceLength - 1:
                action = model[self.chosen_action[tmstp]]
                if action is None:
                    action = "undetermined"
                else:
                    action = action.as_long()

                logging.debug("robot action at tmstp {} is {}".format(tmstp, ACTION_CODES[action]))

                if action == ACTION_CODES["pick"]:
                    pick_data = ["pick"]

                    for c in COLORS:
                        for s in SHAPES:
                            num_picked_items = model[self.picked_color_shape[(c,s,tmstp)]].as_long()
                            if num_picked_items > 0:

                                logging.debug("at tmstp {}, robot is picking q = {}, color = {}, shape = {}".format(tmstp, num_picked_items, c, s))
                                x = model[self.robot_position_x[tmstp+1]].as_long()
                                y = model[self.robot_position_y[tmstp + 1]].as_long()
                                if (x,y) in self.relevant_named_locations:
                                    num_items_past = model[self.items[(x, y, c, s, tmstp)]]
                                    num_items_now = model[self.items[(x,y,c,s,tmstp+1)]]
                                else:
                                    num_items_past = 0
                                    num_items_now = 0
                                logging.debug("the number of {} {} items at {},{} used to be {}, and now is {}"
                                              .format(c,
                                                      s,
                                                      x,
                                                      y,
                                                      num_items_past,
                                                      num_items_now
                                                      )
                                              )
                                pick_data.append([num_picked_items, c, s])
                    actionSingleTimestepData = pick_data

                elif action == ACTION_CODES["move"]:
                    direction = model[self.direction[tmstp]].as_long()
                    logging.debug("at tmstp {} direction is {}".format(tmstp, DIRECTION_CODES[direction]))
                    actionSingleTimestepData = ["move", DIRECTION_CODES[direction]]
                elif action == ACTION_CODES[constants.PASS]:
                    actionSingleTimestepData = [constants.PASS]

                actionWitnessVector.append(actionSingleTimestepData)

            witnessTraceVector.append(singleTimestepData)

        generatedTrace = Trace(witnessTraceVector,  literals=self.listOfVariables)
        #logging.info("distinguishing sequence of actions is {}, witness trace vector is {}".format(actionWitnessVector, witnessTraceVector))
        logging.debug("++++++++++++++++++distinguishing sequence of actions is {}, witness trace vector is {}".format(actionWitnessVector,
                                                                                                   witnessTraceVector))
        return (generatedTrace, world, actionWitnessVector)