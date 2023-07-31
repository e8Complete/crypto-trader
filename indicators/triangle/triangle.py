#!/usr/bin/env python3.5

import os
import argparse
import time
import talib
import random
import numpy as np
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class Triangle(BaseIndicator):
    def __init__(self, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))

    def calculate(self, **data):
        opening_prices = np.array(data.get('opening_prices'))
        high_prices = np.array(data.get('high_prices'))
        low_prices = np.array(data.get('low_prices'))
        closing_prices = np.array(data.get('closing_prices'))
        start_time = time.perf_counter()
        self.logger.info("Calculating Triangle pattern...")

        pattern = talib.CDLMORNINGSTAR(opening_prices, high_prices, low_prices, closing_prices)
        self.logger.info("Triangle pattern:\n{}".format(pattern))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Calulated Triangle pattern in {:0.4f} seconds".format(elapsed_time))
 
        return pattern

    def decide_signal(self, **data):
        pattern = data.get("Triangle", {}).get("calculations", [])
        if pattern is None:
            self.logger.error("Missing required data. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        self.logger.info("Deciding Triangle buy/sell/hold signal...")
        if pattern[-1] == 100:
            signal = Constants.BUY_SIGNAL
        elif pattern[-1] == -100:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Triangle pattern to determine buy or sell signals")
    parser.add_argument('-O', '--opening_prices', type=str,
                        help='Comma-separated list of opening prices',
                        required=False)
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('-H', '--high_prices', type=str,
                        help='Comma-separated list of highest prices',
                        required=False)
    parser.add_argument('-L', '--low_prices', type=str,
                        help='Comma-separated list of lowest prices',
                        required=False)
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    args = parser.parse_args()

    if args.use_mock:
        opening_prices = [random.uniform(100, 200) for _ in range(100)]
        high_prices = [random.uniform(100, 200) for _ in range(100)]
        low_prices = [random.uniform(100, 200) for _ in range(100)]
        closing_prices = [random.uniform(100, 200) for _ in range(100)]
    else:
        if not args.opening_prices or not args.high_prices or not args.low_prices or not args.closing_prices:
            raise ValueError("Missing required arguments: opening_prices, high_prices, low_prices, closing_prices")
        opening_prices = [float(price) for price in args.opening_prices.split(',')]
        high_prices = [float(price) for price in args.high_prices.split(',')]
        low_prices = [float(price) for price in args.low_prices.split(',')]
        closing_prices = [float(price) for price in args.closing_prices.split(',')]

    triangle_api = Triangle()
    pattern = triangle_api.calculate(opening_prices=opening_prices,
                                     high_prices=high_prices,
                                     low_prices=low_prices,
                                     closing_prices=closing_prices)
    signal = triangle_api.decide_signal(Triangle={"calculations": pattern})