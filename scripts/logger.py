#!/usr/bin/env python3.5

import os
import logging
from scripts.constants import Constants
from scripts.utils import get_timestamp


LOG_FORMAT = logging.Formatter('%(asctime)s [%(filename)s:%(lineno)d] \t%(levelname)-8s \t%(message)s', datefmt='%Y-%m-%d-%H:%M:%S')


def setup_logger(name, is_test=True, timestamp=get_timestamp(), level=logging.DEBUG):
    if is_test:
        log_dir = os.path.join('tests', timestamp)
    else:
        log_dir = os.path.join('runs', timestamp)
    log_file = os.path.join(Constants.PROJECT_ROOT, 'logs', log_dir, '{}.log'.format(name))
    log_path = os.path.dirname(log_file)
    os.makedirs(log_path, exist_ok=True)
    logger = logging.getLogger(name)
    fileHandler = logging.FileHandler(log_file, mode='a')
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

