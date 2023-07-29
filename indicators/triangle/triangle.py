#!/usr/bin/env python3.5

import os
import argparse
import time
import talib
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class Triangle:
    def __init__(self, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))

    def get_triangle_pattern(self, opening_prices, high_prices, low_prices, closing_prices):
        start_time = time.perf_counter()
        self.logger.info("Calculating Triangle pattern...")

        pattern = talib.CDLMORNINGSTAR(opening_prices, high_prices, low_prices, closing_prices)
        self.logger.info("Triangle pattern: {}".format(pattern))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Calulated Triangle pattern in {:0.4f} seconds".format(elapsed_time))
 
        return pattern

    def decide_buy_sell_hold_signals(self, pattern):
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
    parser.add_argument('-H', '--high', type=float,
                        help='Highest price',
                        required=True)
    parser.add_argument('-L', '--low', type=float,
                        help='Lowest price',
                        required=True)
    parser.add_argument('-C', '--closing_price', type=float,
                        help='Closing price',
                        required=True)
    parser.add_argument("--interval", type=str, default="1d",
                        help="candlestick interval (default: 1d)")
    parser.add_argument('--k_period', type=int, default=14,
                        help='The number of periods to use in smoothing the %K line')
    parser.add_argument('--d_period', type=int, default=3,
                        help='The number of periods to use in calculating the %D line.')
    parser.add_argument("--threshold", type=float, default=20,
                        help="buy/sell threshold percentage (default: 20)")
    parser.add_argument('-s', '--symbol',
                        help='The symbol being plotted.',
                        required=False)
    args = parser.parse_args()

    triangle_api = Triangle()
    pattern = triangle_api.get_triangle_pattern(opening_prices, high_prices, low_prices, closing_prices)
    signal = triangle_api.decide_buy_sell_hold_signals(pattern)