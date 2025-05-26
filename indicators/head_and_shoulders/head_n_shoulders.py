#!/usr/bin/env python3.5

import os
import argparse
import time
import random
import pandas as pd
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger
import matplotlib.pyplot as plt


class HeadAndShoulders(BaseIndicator):
    def __init__(self, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-"),
                 window_size=5):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.window_size = window_size
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.logger.info(f"Initialized HeadAndShoulders with window_size: {self.window_size}")

    def find_head_and_shoulders(self, data):
        self.logger.debug(f"Attempting to find H&S patterns. Input data length: {len(data)}")
        maxima = data[data == data.rolling(window=self.window_size, center=True).max()]
        minima = data[data == data.rolling(window=self.window_size, center=True).min()] # Minima calculated but not directly used in H&S logic
        maxima = maxima.dropna()
        minima = minima.dropna() # Minima calculation is present, so log its size
        self.logger.debug(f"Found {len(maxima)} initial maxima and {len(minima)} initial minima using window_size {self.window_size}.")
        pattern = []
        for i in range(self.window_size, len(maxima) - self.window_size):
            window = maxima.iloc[i - self.window_size: i + self.window_size]
            self.logger.debug(f"H&S check: Processing window around maxima index {maxima.index[i]}. Window values: {window.values}")
            if window.iloc[self.window_size] == window.max():
                idx_found = window.index[self.window_size]
                pattern.append(idx_found)
                self.logger.info(f"Potential H&S point identified at index: {idx_found}")
        self.logger.debug(f"Returning H&S pattern indices: {pattern}")
        return pattern

    def find_inverted_head_and_shoulders(self, data):
        self.logger.debug(f"Attempting to find Inverted H&S patterns. Input data length: {len(data)}")
        maxima = data[data == data.rolling(window=self.window_size, center=True).max()] # Maxima calculated but not directly used in Inv H&S logic
        minima = data[data == data.rolling(window=self.window_size, center=True).min()]
        maxima = maxima.dropna() # Maxima calculation is present, so log its size
        minima = minima.dropna()
        self.logger.debug(f"Found {len(maxima)} initial maxima and {len(minima)} initial minima using window_size {self.window_size}.")
        pattern = []
        for i in range(self.window_size, len(minima) - self.window_size):
            window = minima.iloc[i - self.window_size: i + self.window_size]
            self.logger.debug(f"Inverted H&S check: Processing window around minima index {minima.index[i]}. Window values: {window.values}")
            if window.iloc[self.window_size] == window.min():
                idx_found = window.index[self.window_size]
                pattern.append(idx_found)
                self.logger.info(f"Potential Inverted H&S point identified at index: {idx_found}")
        self.logger.debug(f"Returning Inverted H&S pattern indices: {pattern}")
        return pattern

    def calculate(self, **data):
        start_time = time.perf_counter()
        closing_prices = data.get("closing_prices", "")
        if not closing_prices or len(closing_prices) < self.window_size * 3: # Min length for potential H&S
            self.logger.warning(f"Closing prices data is missing, empty, or too short (len: {len(closing_prices) if closing_prices else 'None'}). Skipping H&S calculation.")
            return [], [] # Return empty lists
        self.logger.info(f"Starting Head and Shoulders calculation for {len(closing_prices)} closing prices with window_size {self.window_size}.")
        self.logger.debug(f"Closing prices (first 10): {list(closing_prices[:10])}") # Ensure closing_prices is list/array for slicing
        
        self.logger.info("Determining Head and Shoulders...") # This log is a bit redundant now with the one above. Can be removed or kept.
        cdl_head_shoulders = self.find_head_and_shoulders(pd.Series(closing_prices))
        cdl_head_shoulders_inverted = self.find_inverted_head_and_shoulders(pd.Series(closing_prices))
        self.logger.info(f"Found {len(cdl_head_shoulders)} potential Head & Shoulders pattern points at indices: {cdl_head_shoulders}")
        self.logger.info(f"Found {len(cdl_head_shoulders_inverted)} potential Inverted Head & Shoulders pattern points at indices: {cdl_head_shoulders_inverted}")
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Head and Shoulders calculation finished in {:0.4f} seconds".format(elapsed_time))

        return cdl_head_shoulders, cdl_head_shoulders_inverted

    def decide_signal(self, **data):
        cdl_head_shoulders, cdl_head_shoulders_inverted = data.get("HeadAndShoulders", {}).get("calculations", [])
        # The original code had `if not cdl_head_shoulders or not cdl_head_shoulders_inverted:`.
        # An empty list is falsy. So `not []` is true.
        # This check means if *either* list is empty, it errors. This might be too strict if one pattern type is optional.
        # However, the current calculate method always returns two lists, even if empty.
        # So, this check is more about whether the `calculations` key itself was missing or if it wasn't a tuple/list of two items.
        # Given calculate now always returns ([],[]), this error condition might only trigger if "calculations" is totally absent or malformed.
        if cdl_head_shoulders is None or cdl_head_shoulders_inverted is None: # Check if the values themselves are None
            self.logger.error("Missing required H&S calculation data. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL
        
        self.logger.debug(f"H&S signals input: cdl_head_shoulders={cdl_head_shoulders}, cdl_head_shoulders_inverted={cdl_head_shoulders_inverted}")

        self.logger.info("Deciding Head and Shoulders buy/sell/hold signal...")
        if len(cdl_head_shoulders) > 0 and cdl_head_shoulders[-1] == max(cdl_head_shoulders):
            self.logger.info(f"H&S BUY signal triggered: Last H&S top index ({cdl_head_shoulders[-1]}) is the max H&S top index found.")
            signal = Constants.BUY_SIGNAL
        elif len(cdl_head_shoulders_inverted) > 0 and cdl_head_shoulders_inverted[-1] == min(cdl_head_shoulders_inverted):
            self.logger.info(f"H&S SELL signal triggered: Last Inverted H&S bottom index ({cdl_head_shoulders_inverted[-1]}) is the min Inverted H&S bottom index found.")
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal

    def plot(self, calculated_data, prices_df, output_path_prefix):
        """
        Plots the closing prices and marks points identified by the H&S logic.
        calculated_data: Tuple (cdl_head_shoulders_indices, cdl_head_shoulders_inverted_indices).
        prices_df: Pandas DataFrame with 'timestamp' and 'close' columns.
        output_path_prefix: Prefix for the output plot file name.
        """
        try:
            # calculated_data is the direct output of self.calculate()
            # In main.py, it's passed as cv_data.get("calculations")
            # So, we expect calculated_data to be the tuple (list_hs_indices, list_inv_hs_indices)
            if not isinstance(calculated_data, tuple) or len(calculated_data) != 2:
                self.logger.warning("H&S calculated data is not in the expected tuple format, skipping plot.")
                return

            hs_indices = calculated_data[0]
            inv_hs_indices = calculated_data[1]

            if prices_df is None or 'timestamp' not in prices_df.columns or 'close' not in prices_df.columns:
                self.logger.warning("Prices DataFrame is invalid for H&S plot. Skipping.")
                return
            
            if len(prices_df) == 0:
                self.logger.warning("Price data is empty, skipping H&S plot.")
                return

            timestamps = prices_df['timestamp']
            closing_prices = prices_df['close']

            fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
            ax.plot(timestamps, closing_prices, label='Close Price', color='black', alpha=0.7, linewidth=0.8)

            # Plot potential H&S points (local maxima identified by find_head_and_shoulders)
            if hs_indices:
                hs_timestamps = prices_df['timestamp'].iloc[hs_indices]
                hs_prices = prices_df['close'].iloc[hs_indices]
                ax.scatter(hs_timestamps, hs_prices, marker='v', color='red', s=50, label='Potential H&S Peak Points')

            # Plot potential Inverted H&S points (local minima identified by find_inverted_head_and_shoulders)
            if inv_hs_indices:
                inv_hs_timestamps = prices_df['timestamp'].iloc[inv_hs_indices]
                inv_hs_prices = prices_df['close'].iloc[inv_hs_indices]
                ax.scatter(inv_hs_timestamps, inv_hs_prices, marker='^', color='green', s=50, label='Potential Inv H&S Trough Points')
            
            ax.set_title(f'Head & Shoulders Pattern Points (Window: {self.window_size})')
            ax.set_xlabel('Timestamp')
            ax.set_ylabel('Price')
            if hs_indices or inv_hs_indices: # Only show legend if there's something to label
                ax.legend()
            ax.grid(True, linestyle=':', alpha=0.5)
            
            plot_filename = f"{output_path_prefix}head_shoulders_plot.png"
            plt.savefig(plot_filename)
            plt.close(fig)
            self.logger.info(f"Head & Shoulders plot saved to {plot_filename}")

        except Exception as e:
            self.logger.error(f"Error generating Head & Shoulders plot: {e}", exc_info=True)
            if 'fig' in locals() and fig is not None:
                plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Head and Shoulrders to determine buy or sell signals")
    parser.add_argument('-O', '--opening_prices', type=float,
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
    parser.add_argument('-w', '--window_size', type=int, default=5,
                        help='Window size')
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
        if not args.opening_prices or not args.closing_prices or not args.high_prices or not args.low_prices:
            raise ValueError("Missing required arguments: opening_prices, closing_prices, high_prices, low_prices")
        opening_prices = [float(price) for price in args.opening_prices.split(',')]
        high_prices = [float(price) for price in args.high_prices.split(',')]
        low_prices = [float(price) for price in args.low_prices.split(',')]
        closing_prices = [float(price) for price in args.closing_prices.split(',')]

    head_n_shoulders_api = HeadAndShoulders(window_size=args.window_size)
    calculations = head_n_shoulders_api.calculate(opening_prices=opening_prices,
                                                  high_prices=high_prices,
                                                  low_prices=low_prices,
                                                  closing_prices=closing_prices)
    signal = head_n_shoulders_api.decide_signal(HeadAndShoulders={"calculations": calculations})

