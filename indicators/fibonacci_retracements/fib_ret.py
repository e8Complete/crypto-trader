#!/usr/bin/env python3.5

import os
import argparse
import time
import random
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger
import matplotlib.pyplot as plt


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
        self.logger.info(f"Initialized FibonacciRetracements with fib_levels: {self.fib_levels}")
    
    def calculate(self, **data):
        high_prices_list = data.get("high_prices", [])
        low_prices_list = data.get("low_prices", [])
        self.logger.debug(f"Input data lengths: high_prices_list={len(high_prices_list)}, low_prices_list={len(low_prices_list)}")

        if not high_prices_list or not low_prices_list:
            self.logger.error("High or low prices are missing or empty. Cannot calculate Fibonacci levels.")
            return [] # Return empty list, matching original error behavior

        start_time = time.perf_counter()
        self.logger.info("Calculating Fibonacci retracement levels...")
        # self.logger.info("Fibonacci levels: {}".format(", ".join(map(str, self.fib_levels)))) # Moved to __init__

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
        
        self.logger.info(f"Making signal decision based on: last_price={last_price:.2f}, fib38_price={fib38_price:.2f}, fib61_price={fib61_price:.2f}")

        signal = Constants.HOLD_SIGNAL # Default to HOLD
        if last_price <= fib38_price:
            signal = Constants.BUY_SIGNAL
        elif last_price >= fib61_price: # And price > fib38 (implicit, as it didn't trigger BUY)
            signal = Constants.SELL_SIGNAL
         
        self.logger.info("Signal detected: {}".format(signal))
        return signal

    def plot(self, calculated_data, prices_df, output_path_prefix):
        """
        Plots the closing prices and Fibonacci retracement levels.
        calculated_data: List of Fibonacci price levels from the calculate method.
        prices_df: Pandas DataFrame with 'timestamp' and 'close' columns.
        output_path_prefix: Prefix for the output plot file name.
        """
        try:
            # calculated_data is expected to be the list of fib_levels_prices
            # This comes from main.py as cv_data.get("calculations")
            fib_price_levels = calculated_data 

            if not fib_price_levels: # Checks if list is None or empty
                self.logger.warning("Fibonacci price levels data is missing or empty, skipping plot generation.")
                return

            if prices_df is None or 'timestamp' not in prices_df.columns or 'close' not in prices_df.columns:
                self.logger.warning("Prices DataFrame is invalid or missing 'timestamp'/'close' columns. Skipping Fibonacci plot.")
                return
            
            if len(prices_df) == 0:
                self.logger.warning("Price data is empty, skipping plot.")
                return

            timestamps = prices_df['timestamp']
            closing_prices = prices_df['close']

            fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
            
            ax.plot(timestamps, closing_prices, label='Close Price', color='black', alpha=0.9, linewidth=0.7)

            # Ensure self.fib_levels (the ratios) and fib_price_levels (the calculated prices) align
            # The calculate method uses self.fib_levels to generate fib_price_levels, so they should match in length.
            if len(self.fib_levels) != len(fib_price_levels):
                self.logger.error(f"Mismatch in length between configured fib_ratios ({len(self.fib_levels)}) and calculated price_levels ({len(fib_price_levels)}). Cannot plot accurately.")
                plt.close(fig) # Close the figure if created
                return

            for i, price_level in enumerate(fib_price_levels):
                ratio = self.fib_levels[i]
                ax.axhline(y=price_level, color='blue', linestyle='--', linewidth=0.6, 
                           label=f'Fib {ratio*100:.1f}% ({price_level:.2f})')

            # To avoid overcrowded legend if many levels, consider a different labeling strategy
            # For now, this will create a legend entry for each level.

            # Determine min/max for y-axis padding from price data and fib levels
            all_plot_values = list(closing_prices) + fib_price_levels
            plot_min = min(all_plot_values)
            plot_max = max(all_plot_values)
            padding = (plot_max - plot_min) * 0.05 # 5% padding
            ax.set_ylim(plot_min - padding, plot_max + padding)


            ax.set_title(f'Fibonacci Retracement Levels')
            ax.set_xlabel('Timestamp')
            ax.set_ylabel('Price')
            ax.legend(loc='best', fontsize='small') # Adjust legend location and size
            ax.grid(True, linestyle=':', alpha=0.5)
            
            plot_filename = f"{output_path_prefix}fibonacci_retracement_plot.png"
            plt.savefig(plot_filename)
            plt.close(fig) # Release memory
            self.logger.info(f"Fibonacci Retracement plot saved to {plot_filename}")

        except Exception as e:
            self.logger.error(f"Error generating Fibonacci Retracement plot: {e}", exc_info=True)
            if 'fig' in locals() and fig is not None:
                plt.close(fig)


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