#!/usr/bin/env python3.5

import os
import argparse
import time
import matplotlib.pyplot as plt
from typing import List
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


DEFAULT_FIB_LEVELS = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]

class FibonacciRetracements:
    def __init__(self, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        if args.fib_levels:
            self.fib_levels = args.fib_levels.split(',')
        else:
            self.fib_levels = DEFAULT_FIB_LEVELS
    
    def calculate_fib_levels(self, prices: List[float]) -> List[float]:
        """
        Calculate the Fibonacci retracement levels for the given prices.
        Args:
        - prices (List[float]): A list of prices.
        Returns:
        - List[float]: A list of Fibonacci retracement levels.
        """
        start_time = time.perf_counter()
        self.logger.info("Calculating Fibonacci retracement levels...")
        self.logger.info("Fibonacci levels: {}".format(", ".join(self.fib_levels)))

        max_price = max(prices)
        self.logger.info("Max Price: {}".format(max_price))
        min_price = min(prices)
        self.logger.info("Min Price: {}".format(min_price))
        diff = max_price - min_price
        self.logger.info("Diff: {}".format(diff))
        fib_levels_prices = [min_price + level * diff for level in self.fib_levels]
        self.logger.info("Fibonacci Level Prices: {}".format(", ".join(fib_levels_prices)))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Fibonacci retracement levels calculation finished in {:0.4f} seconds".format(elapsed_time))

        return fib_levels_prices
    
    def plot_fib_levels(self, prices: List[float], symbol: str) -> None:
        """
        Plot the Fibonacci retracement levels for the given prices using matplotlib.
        Args:
        - prices (List[float]): A list of prices.
        - symbol (str): The symbol being plotted.
        """
        fib_levels_prices = self.calculate_fib_levels(prices)
        fig, ax = plt.subplots()
        ax.plot(prices, label="Price")
        for i in range(1, len(self.fib_levels)):
            ax.axhline(fib_levels_prices[i], linestyle='--', color='grey', alpha=0.5, label=f"{int(self.fib_levels[i] * 100)}%")
        ax.legend(loc='upper left')
        ax.set_xlabel("Time")
        ax.set_ylabel("Price")
        ax.set_title(f"Fibonacci Retracement Levels for {symbol}")
        plt.show()

    def decide_buy_sell_hold_signals(self, prices: List[float], fib_levels, symbol_df):
        self.logger.info("Deciding Fibonacci Retracements buy/sell/hold signal...")
        last_price = float(symbol_df['close'].iloc[-1])
        self.logger.info("Last Price: {}".format(last_price))
        fib38 = fib_levels['38.2']
        self.logger.info("fib38: {}".format(fib38))
        fib50 = fib_levels['50.0']  # TODO: This is not in use? Check if this is right
        self.logger.info("fib50: {}".format(fib50))
        fib61 = fib_levels['61.8']
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
    parser.add_argument('-p', '--prices', type=list,
                        help='List of prices',
                        required=True)
    parser.add_argument('-l', '--fib_levels',
                        help='Comma seperated list of Fibonacci retracement levels,',
                        required=False)
    parser.add_argument('-s', '--symbol',
                        help='The symbol being plotted.',
                        required=False)
    args = parser.parse_args()

    fr_api = FibonacciRetracements(args)
    fr_levels = fr_api.calculate_fib_levels(args.prices)
    fr_api.plot_fib_levels(args.prices, args.symbol)
    signals = fr_api.decide_buy_sell_hold_signals(args.prices, args.fib_levels, args.symbol)