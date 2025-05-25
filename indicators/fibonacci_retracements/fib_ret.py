#!/usr/bin/env python3.5

import os
import argparse
import time
import random
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


DEFAULT_FIB_LEVELS = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]


class FibonacciRetracements(BaseIndicator):
    def __init__(self, fib_levels=DEFAULT_FIB_LEVELS, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.fib_levels = [float(level) for level in fib_levels] if fib_levels else DEFAULT_FIB_LEVELS
    
    def calculate(self, **data):
        high_prices_list = data.get("high_prices", [])
        low_prices_list = data.get("low_prices", [])

        if not high_prices_list or not low_prices_list:
            self.logger.error("High or low prices are missing or empty. Cannot calculate Fibonacci levels.")
            return [] # Return empty list, matching original error behavior

        start_time = time.perf_counter()
        self.logger.info("Calculating Fibonacci retracement levels...")
        self.logger.info("Fibonacci levels: {}".format(", ".join(map(str, self.fib_levels))))

        # Determine the absolute highest high and lowest low from the provided series
        overall_max_price = max(high_prices_list)
        self.logger.info("Overall Max Price: {}".format(overall_max_price))
        overall_min_price = min(low_prices_list)
        self.logger.info("Overall Min Price: {}".format(overall_min_price))

        if overall_max_price == overall_min_price:
            self.logger.warning("Max price and min price are the same. Cannot calculate Fibonacci levels.")
            return []

        diff = overall_max_price - overall_min_price
        self.logger.info("Diff: {}".format(diff))
        # Ensure levels are calculated from min_price up for retracements from a low,
        # or from max_price down for retracements from a high.
        # Standard approach is to find range and apply ratios.
        # If current price is in an uptrend (min_price is the start), levels are above min_price.
        # If current price is in a downtrend (max_price is the start), levels are below max_price.
        # The provided logic `min_price + level * diff` assumes an uptrend for retracement levels.
        # For a more general approach, one might need to detect trend first or define levels from both ends.
        # Sticking to the provided calculation logic:
        fib_levels_prices = [overall_min_price + level * diff for level in self.fib_levels]
        self.logger.info("Fibonacci Level Prices: {}".format(", ".join(map(str, fib_levels_prices))))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Fibonacci retracement levels calculation finished in {:0.4f} seconds".format(elapsed_time))

        return fib_levels_prices # This is a list of calculated price levels
    
    def decide_signal(self, current_closing_price=None, **cv_data): # cv_data is the output from calculate()
        if current_closing_price is None:
            self.logger.error("Current closing price not provided. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        fib_levels_prices = cv_data.get("calculations") # Expects main.py to pass the list under this key

        if not fib_levels_prices: # Checks if list is None or empty
            self.logger.error("Fibonacci levels data is missing or empty. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL
        
        last_price = current_closing_price # Use the passed current_closing_price
        self.logger.info("Last Price: {}".format(last_price))

        # fib_levels_map maps the configured ratio (e.g. 0.382) to the calculated price level
        # self.fib_levels should be used here as it's what the user configured (or default in __init__)
        if len(self.fib_levels) != len(fib_levels_prices):
            self.logger.error("Mismatch between configured fib_levels and calculated fib_level_prices. Cannot accurately map.")
            return Constants.UNKNOWN_SIGNAL
         
        fib_levels_map = dict(zip(self.fib_levels, fib_levels_prices))

        fib38_price = fib_levels_map.get(0.382)
        fib61_price = fib_levels_map.get(0.618)

        if fib38_price is None or fib61_price is None:
            self.logger.warning("0.382 or 0.618 level not found in configured fib_levels. Adjust config or signal logic. Holding.")
            return Constants.HOLD_SIGNAL # Changed from UNKNOWN to HOLD

        signal = Constants.HOLD_SIGNAL # Default to HOLD
        if last_price <= fib38_price:
            signal = Constants.BUY_SIGNAL
        elif last_price >= fib61_price: # And price > fib38 (implicit, as it didn't trigger BUY)
            signal = Constants.SELL_SIGNAL
         
        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Fibonacci retracement levels to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('-H', '--high_prices', type=str,
                        help='Comma-separated list of highest prices',
                        required=False)
    parser.add_argument('-L', '--low_prices', type=str,
                        help='Comma-separated list of lowest prices',
                        required=False)
    parser.add_argument('-l', '--fib_levels',
                        help='Comma-separated list of Fibonacci retracement levels',
                        required=False)
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    args = parser.parse_args()

    if args.use_mock:
        high_prices = [random.uniform(150, 200) for _ in range(100)]
        low_prices = [random.uniform(100, 149) for _ in range(100)]
        closing_prices = [random.uniform(low, high) for low, high in zip(low_prices, high_prices)]
    else:
        if not args.closing_prices or not args.high_prices or not args.low_prices:
            raise ValueError("Missing required arguments: closing_prices, high_prices, low_prices")
        high_prices = [float(price) for price in args.high_prices.split(',')]
        low_prices = [float(price) for price in args.low_prices.split(',')]
        closing_prices = [float(price) for price in args.closing_prices.split(',')]
    
    if args.fib_levels:
        fib_levels = args.fib_levels.split(',')
    else:
        fib_levels = DEFAULT_FIB_LEVELS
    fr_api = FibonacciRetracements(fib_levels=args.fib_levels)
    fr_levels = fr_api.calculate(high_prices=high_prices, low_prices=low_prices)
    signal = fr_api.decide_signal(closing_prices=closing_prices, FibonacciRetracements={"calculations": fr_levels})