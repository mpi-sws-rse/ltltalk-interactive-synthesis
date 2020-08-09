import constants
import nltk
# nltk.download('punkt')
# nltk.download('wordnet')
import re
import pdb
import logging


try:
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
except:
    pdb.set_trace()
    nltk.download('wordnet')
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer


def get_locations_from_utterance(nl_utterance):
    locations_strings = re.findall(r"(\d+,[\n\t ]*\d+)", nl_utterance)

    locations = []
    for loc in locations_strings:

        try:
            location_pair = loc.split(',')
            locations.append((int(location_pair[0]), int(location_pair[1])))
        except:
            continue

    return locations

"""
this function takes hints and keeps only the maximal value of those hints
that actually appear in the emitted events of the example
"""
def filter_hints_with_emitted_events(hints, seq_of_events):

    new_hints = {}
    for events in seq_of_events:
        for e in events:

            hints_in_e = {h:hints[h] for h in hints if h in e}

            if len(hints_in_e) > 0:
                max_hints_value = max(hints_in_e.values())
                for k in hints_in_e:
                    if hints_in_e[k] == max_hints_value:
                        new_hints[k] = max_hints_value
    if constants.DRY in hints:
        new_hints[constants.DRY] = hints[constants.DRY]
    for op in constants.OPERATORS:
        if op in hints:
            new_hints[op] = hints[op]

    return new_hints


def get_hints_from_utterance(nl_utterance, pickup_locations, all_locations, emitted_events_seq):


    """
    the function takes the natural language utterance as an input and tries to distill relevant propositional variables
(a subset of constants.EVENTS) with the weights attached to them. This is a crude implementation based on the appearences
of individual subwords. --->  SHOULD BE REPLACED BY SOMETHING BETTER

    :param nl_utterance: string
    :param pickup_locations: list of all locations at which a pickup was happening in the user's demonstration
    :param all_locations: list of all locations in the user's demonstration
    :return: dictionary {prop_variable: weight}
    """





    lemmatizer = WordNetLemmatizer()
    # all the tokens that correspond to the notions we care about (such as quantities, colors, or shapes), or the synonyms of those words
    utterance_tokens = [lemmatizer.lemmatize(token) for token in nl_utterance.split() if token in constants.ALL_SIGNIFICANT_WORDS]

    scores = {}
    for prop_variable in constants.EVENTS:
        score = 0
        # because the input here are propositional variables (and not the core-language expressions),
        # we need to detach different elements of the prop variables (e.g., referring to color, shape, quantity)
        list_of_descriptors = [lemmatizer.lemmatize(el) for el in prop_variable.split("_") if not (el == "x" or el == "item" or el == "at")]

        for desc in list_of_descriptors:
            candidates = [desc]
            if desc in constants.SYNONYMS:
                candidates += constants.SYNONYMS[desc]
            if desc in constants.CONNECTED_WORDS:
                candidates += constants.CONNECTED_WORDS[desc]
            for candidate in candidates:
                if candidate in utterance_tokens:
                    score += 1
                    continue
        # denominator consists of number of tokens in the descriptor of prop_variable (to account for things not
        # mentioned in the utterance) and number of tokens in the utterance (to account for things mentioned in the
        # utterance but not in the propositional variable)
        try:
            score = score / (len(list_of_descriptors) + len(utterance_tokens))
        except:
            score = 0
        logging.debug("assigning score of {} to prop_var {}".format(score, prop_variable))

        scores[prop_variable] = score


    for operator in constants.CONNECTED_WORDS:
        if not operator in constants.OPERATORS:
            continue
        score = 0
        for operator_description in constants.CONNECTED_WORDS[operator]:
            if operator_description in utterance_tokens:
                score += 1
        scores[operator] = score


    hints = {k : (1 + scores[k]) for k in scores if scores[k] > constants.HINTS_CUTOFF_VALUE}


    # locations that are mentioned in the uttera
    utterance_relevant_locations = get_locations_from_utterance(nl_utterance)

    hintsWithLocations = {}

    for hint in hints:

        if hint == constants.DRY:
            
            hintsWithLocations[hint] = hints[hint]

            continue
        if hint in constants.OPERATORS or hint in constants.AT_SPECIAL_LOCATION_EVENTS:
            hintsWithLocations[hint] = hints[hint]

        for l in pickup_locations:
            hintsWithLocations["{}_at_{}_{}".format(hint, l[0], l[1])] = hints[hint]


    if len(hintsWithLocations) > 0:
        maxHintsWithLocations = max(hintsWithLocations.values())
        minHintsWithLocations = min(hintsWithLocations.values())
    else:
        maxHintsWithLocations = 0
        minHintsWithLocations = 0

    # for all the locations that appear in the utterance, give them some value as well
    atLocationsHints = {"at_{}_{}".format(loc[0], loc[1]): max(minHintsWithLocations, 1) for loc in utterance_relevant_locations}

    hintsWithLocations = filter_hints_with_emitted_events(hintsWithLocations, emitted_events_seq)
    hintsWithLocations.update(atLocationsHints)
    
    if constants.DRY in hintsWithLocations:
        hintsWithLocations[constants.DRY] = hintsWithLocations[constants.DRY] + 1

    return hintsWithLocations
