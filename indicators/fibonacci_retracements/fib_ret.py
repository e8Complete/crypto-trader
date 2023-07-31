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
        high_prices = data.get("high_prices", [])
        low_prices = data.get("low_prices", [])
        prices = high_prices + low_prices
        if not prices:
            self.logger.error("No prices. No Fibonacci retracement")
            return []
        start_time = time.perf_counter()
        self.logger.info("Calculating Fibonacci retracement levels...")
        self.logger.info("Fibonacci levels: {}".format(", ".join(map(str, self.fib_levels))))

        max_price = max(prices)
        self.logger.info("Max Price: {}".format(max_price))
        min_price = min(prices)
        self.logger.info("Min Price: {}".format(min_price))
        diff = max_price - min_price
        self.logger.info("Diff: {}".format(diff))
        fib_levels_prices = [min_price + level * diff for level in self.fib_levels]
        self.logger.info("Fibonacci Level Prices: {}".format(", ".join(map(str, fib_levels_prices))))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Fibonacci retracement levels calculation finished in {:0.4f} seconds".format(elapsed_time))

        return fib_levels_prices
    
    def decide_signal(self, **data):
        fib_levels = data.get("FibonacciRetracements", {}).get("calculations", [])
        closing_prices = data.get("closing_prices", [])
        
        if not fib_levels or not closing_prices:
            self.logger.error("Missing required data. Cannot decide signal.")
            return None
        
        self.logger.info("Deciding Fibonacci Retracements buy/sell/hold signal...")
        last_price = closing_prices[-1]
        self.logger.info("Last Price: {}".format(last_price))

        fib_levels_dict = dict(zip(self.fib_levels, fib_levels))

        fib38 = fib_levels_dict.get(0.382)
        self.logger.info("fib38: {}".format(fib38))
        #   fib50 = fib_levels_dict.get(50.0)
        fib61 = fib_levels_dict.get(0.618)
        self.logger.info("fib61: {}".format(fib61))

        if last_price <= fib38:
            signal = Constants.BUY_SIGNAL
        elif last_price >= fib61:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL

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