import pdb

from nlp_helpers import get_hints_from_utterance
import os
import json
from world import World


my_path = os.path.abspath(os.path.dirname(__file__))
directory = os.path.join(my_path, "../../experiments/multiple_examples_experiment_worlds/")
#directory = os.path.join(my_path, "../../experiments/playground/")
all_files = sorted(os.scandir(directory), key= lambda dir_entry: dir_entry.name)

def test_basic():
    for test_filename in all_files:
        print("testing {}".format(test_filename.name))
        with open(test_filename.path) as test_file:
            test_def = json.load(test_file)
            nl_utterance = test_def["description"]
            example = test_def["examples"][0]
            world = World(example["context"], json_type=2)
            path = example["init-path"]

            (emitted_events, pickup_locations, collection_of_negative,
             all_locations) = world.execute_and_emit_events(
                path)


            hintsWithLocations = get_hints_from_utterance(nl_utterance, pickup_locations, all_locations,
                                                                      emitted_events)
            print("for nl {}, I got hints {}\n".format(nl_utterance, hintsWithLocations))
            expected_hints = test_def["expected-hints"]
            for h in expected_hints:
                assert h in hintsWithLocations



if __name__ == "__main__":
    test_basic()