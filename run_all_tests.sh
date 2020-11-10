echo "depth 4"
python experiments/interaction_experiment.py --tests_definition_folder=experiments/multiple_examples_experiment_worlds  --num_repetitions=5 --max_depth 4 --condensed_output=condensedResults.csv --num_init_candidates 5 --output=results.csv --optimizer_criterion=pareto --num_examples=1
echo "depth 5"
python experiments/interaction_experiment.py --tests_definition_folder=experiments/multiple_examples_experiment_worlds  --num_repetitions=5 --max_depth 5 --condensed_output=condensedResults5.csv --num_init_candidates 5 --output=results5.csv --optimizer_criterion=pareto --num_examples=1
echo "without no excessive effort, depth 4"
python experiments/interaction_experiment.py --exclude_no_excessive_effort_principle --tests_definition_folder=experiments/multiple_examples_experiment_worlds  --num_repetitions=5 --max_depth 4 --condensed_output=condensedResultsNoExcessiveEffort.csv --num_init_candidates 5 --output=resultsNoExcessiveEffort.csv --optimizer_criterion=pareto --num_examples=1
echo "without no excessive effort, depth 5"
python experiments/interaction_experiment.py --exclude_no_excessive_effort_principle --tests_definition_folder=experiments/multiple_examples_experiment_worlds  --num_repetitions=5 --max_depth 5 --condensed_output=condensedResults5NoExcessiveEffort.csv --num_init_candidates 5 --output=results5NoExcessiveEffort.csv --optimizer_criterion=pareto --num_examples=1
echo "without no excessive trace, depth 4"
python experiments/interaction_experiment.py --exclude_no_excessive_trace_principle --tests_definition_folder=experiments/multiple_examples_experiment_worlds  --num_repetitions=5 --max_depth 4 --condensed_output=condensedResultsNoExcessiveTrace.csv --num_init_candidates 5 --output=resultsNoExcessiveTrace.csv --optimizer_criterion=pareto --num_examples=1
echo "without no excessive trace, depth 5"
python experiments/interaction_experiment.py --exclude_no_excessive_trace_principle --tests_definition_folder=experiments/multiple_examples_experiment_worlds  --num_repetitions=5 --max_depth 5 --condensed_output=condensedResults5NoExcessiveTrace.csv --num_init_candidates 5 --output=results5NoExcessiveTrace.csv --optimizer_criterion=pareto --num_examples=1


