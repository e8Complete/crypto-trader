import os
import logging
from utils.constants import Constants
from datetime import datetime

# logging.basicConfig(format='%(asctime)s in %(filename)s:%(lineno)d: [%(levelname)s]: %(message)s', level=logging.WARNING, datefmt='%Y/%m/%d - %H:%M:%S')
LOG_FORMAT = logging.Formatter('%(asctime)s in %(filename)s:%(lineno)d: [%(levelname)s]: %(message)s', datefmt='%Y/%m/%d-%H:%M:%S')

def setup_logger(name, level=logging.DEBUG):
    """
    Input: Log name, log-level (optional)
    Return: A logger that writes to disk and console
    Note: To turn off/down logging when running Timeliner.py, pass level=logging.CRITICAL
    """
    log_file = os.path.join(Constants.PROJECT_ROOT, 'tmp', 'logs', f'{name}.log')
    logger = logging.getLogger(name)
    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(LOG_FORMAT)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(LOG_FORMAT)
    logger.setLevel(level)
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    return logger

# Log levels
# CRITICAL    50
# ERROR       40
# WARNING     30
# INFO        20
# DEBUG       10
# NOTSET      0

# Logging format description
# %(pathname)s Full pathname of the source file where the logging call was issued(if available).
# %(filename)s Filename portion of pathname.
# %(module)s Module (name portion of filename).
# %(funcName)s Name of function containing the logging call.
# %(lineno)d Source line number where the logging call was issued (if available).


def log_output(dict_name, dict):
    """
    Input: A dictionary name, a dictionary
    Action: Writes the dictionary to disk for debugging purpose
    """
    now = datetime.now()
    dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
    output_log = os.path.join(Constants.PROJECT_ROOT, 'tmp', 'outputs', f'{dict_name}_output.txt')
    with open(output_log, 'a') as output:
        output.write(f'[{dt_string}]\n\n\n')
        for item in dict.items():
            key, val = item
            output.write(f'{key}: {val}\n\n')
        output.write('\n\n\n')
