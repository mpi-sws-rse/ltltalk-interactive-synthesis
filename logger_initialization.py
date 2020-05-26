import logging
import os

if not os.path.exists("logs"):
    os.makedirs("logs")

stats_log = logging.getLogger('stats_logger')
stats_log.setLevel(logging.DEBUG)

fh = logging.FileHandler('logs/stats.log')
fh.setLevel(logging.INFO)

detailed_fh = logging.FileHandler('logs/detailed_stats.log')
detailed_fh.setLevel(logging.DEBUG)

stats_formatter = logging.Formatter('%(message)s')
fh.setFormatter(stats_formatter)
detailed_fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

stats_log.addHandler(fh)
stats_log.addHandler(detailed_fh)


error_log = logging.getLogger('error_logger')
error_log.setLevel(logging.ERROR)

error_fh = logging.FileHandler('logs/error.log')
error_fh.setLevel(logging.INFO)
error_fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

error_log.addHandler(error_fh)
