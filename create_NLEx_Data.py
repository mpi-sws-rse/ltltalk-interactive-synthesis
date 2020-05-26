import argparse
import json
import os
import pdb

import constants
from world import World


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--tests_definition_folder", dest="testsFolder")
    parser.add_argument("--tests_output_folder", dest="outputFolder")

    args, unknown = parser.parse_known_args()
    directory = args.testsFolder
    outputDirectory = args.outputFolder

    all_files = sorted(os.scandir(directory), key=lambda dir_entry: dir_entry.name)

    for test_filename in all_files:

        with open(test_filename.path) as test_file:
            emitted_events_seq = []
            collection_of_negative = []
            test_def = json.load(test_file)
            data = {}
            data["NL"] = test_def["description"]
            examplesOut = {}
            examplesOut["target-formula"] = test_def["target-formula"]

            ex = test_def["examples"][0]

            context = ex["context"]
            path = ex["init-path"]
            test_world = World(context, json_type=2)
            (emitted_events, pickup_locations_ex, collection_of_negative_ex,
             all_locations_ex) = test_world.execute_and_emit_events(
                path)
            emitted_events_seq.append(emitted_events)
            collection_of_negative += collection_of_negative_ex

            literals = []
            literals += constants.STATE_EVENTS
            for loc in pickup_locations_ex:
                literals += constants.PICKUP_EVENTS_PER_LOCATION[loc]

            for loc in all_locations_ex:
                literals.append(constants.AT_EVENTS_PER_LOCATION[loc])
                if loc in constants.SPECIAL_LOCATIONS:
                    literals.append("at_{}".format(constants.SPECIAL_LOCATIONS[loc]))


            examplesOut["literals"] = literals

            positive = [";".join([",".join([e for e in timestep_events])
                                  for timestep_events in emitted_events])
                        for emitted_events in emitted_events_seq]
            examplesOut["positive"] = positive
            negative = [";".join([",".join([e for e in timestep_events])
                                  for timestep_events in neg_emitted_events])
                        for neg_emitted_events in collection_of_negative]
            examplesOut["negative"] = negative

            data["examples"] = examplesOut

            out_file_path = os.path.join(outputDirectory, test_filename.name)

            with open(out_file_path, "w") as outF:
                json.dump(data, outF, indent=2)





if __name__ == '__main__':
    main()