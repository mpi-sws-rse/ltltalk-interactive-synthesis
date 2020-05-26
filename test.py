"""
a dummy file to test world functionality before it can be completely integrated
"""

from world import World
import json
import pdb
import nlp_helpers
from utils import create_json_spec
import constants
from encoding.experiment import start_experiment
from candidatesCreation import create_candidates, update_candidates, create_disambiguation_example

"""
problems: if the actions is a more complicated one, the system will find "underapproximation explanation", that specify
that parts of the picked items really are picked, but treats the rest as noise. How to fight that? Add all the picking 
subsets as additional negative examples?


"""


def main():


    with open("temp.json") as world_file:
        w = json.load(world_file)
        test_world = World(w, json_type=2)






        # sequence_of_actions = []
        # # sequence_of_actions += [("move", "right") for _ in range(5)]
        # # sequence_of_actions += [("pick", [("red", "circle")])]
        #
        # sequence_of_actions += [("move", "right") for _ in range(5)]
        # # sequence_of_actions += [("move", "up")]
        # # sequence_of_actions += [("move", "down")]
        # #sequence_of_actions += [("pick", [("red", "circle"),("red", "circle"),("blue", "circle"), ("green", "square"), ("green", "circle")])]
        # #sequence_of_actions += [("pick", [("red", "circle"), ("red", "circle"), ("blue", "circle"), ("green", "circle"), ("green","square")])]
        # sequence_of_actions += [("pick", [("red", "circle")])]
        sequence_of_actions = [('pick', [('red', 'circle'), ('blue', 'triangle')]), ('move', 'left'), ('move', 'right'), ('pick', [('red', 'circle'), ('blue', 'circle')])]


        pdb.set_trace()
        (emitted_events, pickup_locations, collection_of_negative, all_locations) = test_world.execute_and_emit_events(sequence_of_actions)


        utterance = "get one triangle from [4,0] and then one item from [11,1]"
        hints = nlp_helpers.get_hints_from_utterance(utterance)
        pdb.set_trace()
        relevant_locations = nlp_helpers.get_locations_from_utterance(utterance)



        hintsWithLocations = {hint+"_"+str(l[0])+"_"+str(l[1]) : hints[hint] for hint in hints for l in pickup_locations}
        maxHintsWithLocations = max(hintsWithLocations.values())
        minHintsWithLocations = min(hintsWithLocations.values())
        middleValue = (maxHintsWithLocations + minHintsWithLocations)/2

        atLocationsHints = {"at_{}_{}".format(loc[0], loc[1]) :middleValue for loc in relevant_locations}
        hintsWithLocations.update(atLocationsHints)

        create_json_spec(file_name="data/exampleWithHints.json", emitted_events=emitted_events, hints = hintsWithLocations,
                         pickup_locations=pickup_locations, all_locations=all_locations, negative_sequences=collection_of_negative)

        start_experiment(experiment_specification = "data/exampleWithHints.json")


if __name__ == '__main__':
    main()