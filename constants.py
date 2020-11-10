import pdb
import sys

#try:
from encoding import encodingConstants
import logging
try:
    from nltk.corpus import wordnet
except:
    pdb.set_trace()
    import nltk
    nltk.download('wordnet')
    from nltk.corpus import wordnet

def get_wordnet_synonyms(word):
    return [l.name() for syn in wordnet.synsets(word) for l in syn.lemmas() ]



UP = "up"
DOWN = "down"
LEFT = "left"
RIGHT = "right"
DRY = "at_dry"


#actions
PICK = "pick"
MOVE = "move"
PASS = "pass"


DIRECTIONS = [UP, DOWN, LEFT, RIGHT]

WIDTH = 12
HEIGHT = 9

# steps when looking for a solution
MIN_FINE_RANGE = 5
MAX_FINE_RANGE = 9
STEP_FINE_RANGE = 2

MIN_COARSE_RANGE = MAX_FINE_RANGE + 1
MAX_COARSE_RANGE = 40
STEP_COARSE_RANGE = 4

# steps when looking for disambiguation
MIN_RANGE_DISAMBIGUATION = 3
MAX_RANGE_DISAMBIGUATION = 30
STEP_DISAMBIGUATION = 4


COLORS = ["red", "green", "blue", "yellow"]
COLOR_CODES = {"red": 1, "green": 2, "blue": 3, "yellow":4, "x": 0}
SHAPES = ["square", "circle", "triangle"]
SHAPE_CODES = {"square": 1, "circle": 2, "triangle": 3, "x": 0}
QUANTIFIERS = ["one","two", "three", "every"]
ACTION_CODES = {MOVE: 0, PICK: 1, PASS: 2}
DIRECTION_CODES = {LEFT: 0, RIGHT: 1, UP: 2, DOWN: 3}
numbersToWords = {1: "one", 2: "two", 3: "three", -1: "every"}

HINTS_CUTOFF_VALUE = 0.15



SPECIAL_LOCATIONS = {(20,20): "kitchen", (21,21): "bathroom"} # add meaningful coordinates for experimenting
# with special locations
SPECIAL_NAMES = {v: k for k, v in SPECIAL_LOCATIONS.items()}

# x is sa symbol for don't care
PICKUP_EVENTS = ["{}_{}_{}_{}_item".format(PICK, quantifier, color, shape)
                for quantifier in QUANTIFIERS
                for color in COLORS+["x"]
                for shape in SHAPES+["x"]]

STATE_EVENTS = [DRY]

AT_SPECIAL_LOCATION_EVENTS = ["at_"+ l for l in SPECIAL_NAMES]

AT_EVENTS_PER_LOCATION ={(i,j): "at_{}_{}".format(i,j) for i in range(WIDTH) for j in range(HEIGHT)}

PICKUP_EVENTS_PER_LOCATION = {}
for x in range(WIDTH):
    for y in range(HEIGHT):
        for p in PICKUP_EVENTS:
            if (x,y) in PICKUP_EVENTS_PER_LOCATION:
                PICKUP_EVENTS_PER_LOCATION[(x,y)].append(p+"_at_"+str(x)+"_"+str(y))
            else:
                PICKUP_EVENTS_PER_LOCATION[(x, y)] = [(p + "_at_" + str(x)+"_"+str(y))]



EVENTS = PICKUP_EVENTS + STATE_EVENTS + AT_SPECIAL_LOCATION_EVENTS

SYNONYMS = {"every": ["all"], PICK: ["grab", "collect", "take"],
            "one": ["1", "single", "individual", "the"], "two": ["2"], "three": ["3"],
            "bathroom":["bathroom"], "kitchen":["kitchen"]}
WORDNET_SYNONYMS = { k:  get_wordnet_synonyms(k) for k in SYNONYMS}
CONNECTED_WORDS = {"dry": ["water"], "water": ["dry"], encodingConstants.STRICTLY_BEFORE: ["first", "then", "before"],
                   encodingConstants.UNTIL: ["until", "while"], encodingConstants.F: ["eventually"],
                   encodingConstants.LAND: ["simultaneously", "also", "togetherWith"]}
#pdb.set_trace()
ALL_SIGNIFICANT_WORDS = list(set(COLORS + SHAPES + QUANTIFIERS + [syn for syns in SYNONYMS.values() for syn in syns] + \
                        DIRECTIONS + [MOVE] + [con for cons in CONNECTED_WORDS.values() for con in cons] + \
                        list(SPECIAL_NAMES.keys()) + [syn for syns in WORDNET_SYNONYMS.values() for syn in syns]))




OPERATORS = [
    encodingConstants.F,
    encodingConstants.G,
    encodingConstants.LAND,
    encodingConstants.UNTIL,
    encodingConstants.STRICTLY_BEFORE,
    encodingConstants.LNOT
  ]

NUM_CANDIDATE_FORMULAS = 5
NUM_CANDIDATE_FORMULAS_OF_SAME_DEPTH = 3
NUM_ATTEMPTS_PER_DEPTH = NUM_CANDIDATE_FORMULAS_OF_SAME_DEPTH + 2
MAX_NUM_ATTEMPTS = NUM_CANDIDATE_FORMULAS + 3


CANDIDATE_MAX_DEPTH = 4

DEBUG_UNSAT_CORE = False
LOGGING_LEVEL = logging.INFO

TESTING = True

UNKNOWN_SOLVER_RES = "timeout"

FAILED_CANDIDATES_GENERATION_STATUS = "failed"

TOP_VALUES = [1,3,5]

EXPORT_JSON_TASK = False

USE_HINTS = True
