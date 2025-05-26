#!/usr/bin/env python3.5

import os
import argparse
import time
import numpy as np
import pandas as pd
import talib
import random
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger
import matplotlib.pyplot as plt


class MACD(BaseIndicator):
    def __init__(self, fast_period=12, slow_period=26, signal_period=9, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.logger.info(f"Initialized MACD with fast_period={self.fast_period}, slow_period={self.slow_period}, signal_period={self.signal_period}")
    
    def calculate(self, **data):
        closing_prices = data.get("closing_prices", [])
        if not closing_prices or len(closing_prices) < self.slow_period: # MACD needs enough data for the slowest EMA
            self.logger.warning(f"Closing prices data is missing, empty, or too short (len: {len(closing_prices) if closing_prices else 'None'}) for slow_period {self.slow_period}. Skipping MACD calculation.")
            # Return empty arrays matching talib.MACD output structure on error/empty
            return np.array([]), np.array([]), np.array([]) 
        self.logger.info(f"Calculating MACD for {len(closing_prices)} closing prices.")
        self.logger.debug(f"Closing prices sample (first 5): {closing_prices[:5]}")

        start_time = time.perf_counter()
        self.logger.info("Calculating MACD...") # This is fine, or could be merged with the one above.
        # Removed period logging from here as it's in __init__

        try:
            macd_line, signal_line, histogram = talib.MACD(np.array(closing_prices),
                        fastperiod=self.fast_period, slowperiod=self.slow_period,
                        signalperiod=self.signal_period)
        except Exception as e:
            self.logger.error(f"Error calculating MACD with TA-Lib: {e}")
            return np.array([]), np.array([]), np.array([])
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        # Helper function (can be defined inside calculate or imported)
        def summarize_array(name, arr):
            if arr is None: return f"{name}: None"
            # TA-Lib MACD components can have NaNs at the beginning
            valid_values = arr[~np.isnan(arr)]
            if len(valid_values) > 6:
                return f"{name} (len {len(valid_values)}): First 3=[{', '.join(f'{x:.2f}' for x in valid_values[:3])}], Last 3=[{', '.join(f'{x:.2f}' for x in valid_values[-3:])}]"
            elif len(valid_values) > 0: # Handles cases where most/all are NaNs but some valid exist
                return f"{name} (len {len(valid_values)}): Values=[{', '.join(f'{x:.2f}' for x in valid_values)}]"
            elif len(arr) > 0 : # Original array had data, but all were NaN
                 return f"{name} (len {len(arr)}): All values are NaN."
            else: # Empty array returned from TA-Lib (e.g. due to very short input)
                return f"{name}: Result is an empty array."

        self.logger.info("Calculated MACD Components:")
        self.logger.info(summarize_array("MACD Line", macd_line))
        self.logger.info(summarize_array("Signal Line", signal_line))
        self.logger.info(summarize_array("Histogram", histogram))
        self.logger.info("Calculated MACD in {:0.4f} seconds".format(elapsed_time))
 
        return macd_line, signal_line, histogram

    def decide_signal(self, **data):
        # calculations_tuple is (macd_line, signal_line, histogram)
        calculations_tuple = data.get("calculations") 
        if calculations_tuple is None or not isinstance(calculations_tuple, tuple) or len(calculations_tuple) != 3:
            self.logger.error("MACD calculation data is missing or not in expected tuple format. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL
        macd_line, signal_line, _ = calculations_tuple
        
        # Check if TA-Lib returned empty arrays (e.g. due to insufficient data) or if arrays are too short for comparison
        if macd_line.size < 2 or signal_line.size < 2: # Need at least two points for prev/last comparison
            self.logger.warning(f"MACD lines (MACD: {macd_line.size}, Signal: {signal_line.size}) too short for signal decision. Possibly due to insufficient input data to TA-Lib.")
            return Constants.UNKNOWN_SIGNAL

        self.logger.info("Deciding MACD buy/sell/hold signal...")
        # Create DataFrame from the numpy arrays for easier handling of last two rows
        # Ensure we only use valid (non-NaN) parts if necessary, though TA-Lib MACD usually populates with NaNs at start
        # For this logic, we need the last two actual values, NaNs would cause issues if not handled.
        # However, the .size check above should ensure we have plottable/comparable points.
        # If the arrays still contain NaNs at the end (unlikely for MACD), more robust handling would be needed.
        
        # Drop NaNs to ensure correct indexing for last_row and prev_row if arrays are padded with NaNs
        # This is crucial if the input `closing_prices` was just barely enough, leading to NaNs in initial MACD outputs.
        df_macd = pd.DataFrame({'MACD': macd_line, 'Signal Line': signal_line}).dropna()
        
        if len(df_macd) < 2:
            self.logger.warning(f"Not enough valid (non-NaN) MACD data points ({len(df_macd)}) for signal decision after dropping NaNs.")
            return Constants.UNKNOWN_SIGNAL

        last_row = df_macd.iloc[-1]
        prev_row = df_macd.iloc[-2]
        
        self.logger.info(f"Making signal decision based on: "
                         f"Prev MACD={prev_row['MACD']:.2f}, Prev Signal={prev_row['Signal Line']:.2f}, "
                         f"Last MACD={last_row['MACD']:.2f}, Last Signal={last_row['Signal Line']:.2f}")

        if last_row['MACD'] > last_row['Signal Line'] and prev_row['MACD'] <= prev_row['Signal Line']:
            signal = Constants.BUY_SIGNAL
        elif last_row['MACD'] < last_row['Signal Line'] and prev_row['MACD'] >= prev_row['Signal Line']:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal

    def plot(self, calculated_data, prices_df, output_path_prefix):
        """
        Plots the MACD line, signal line, and histogram.
        calculated_data: Tuple (macd_line, signal_line, macd_hist) from calculate().
        prices_df: Pandas DataFrame with a 'timestamp' column for the x-axis.
        output_path_prefix: Prefix for the output plot file name.
        """
        try:
            if not isinstance(calculated_data, tuple) or len(calculated_data) != 3:
                self.logger.warning("MACD calculated data is not in the expected tuple format, skipping plot.")
                return

            macd_line, signal_line, macd_hist = calculated_data

            if macd_line is None or signal_line is None or macd_hist is None or \
               len(macd_line) == 0 or len(signal_line) == 0 or len(macd_hist) == 0:
                self.logger.warning("MACD components are None or empty, skipping plot generation.")
                return

            if prices_df is None or 'timestamp' not in prices_df.columns:
                self.logger.warning("Prices DataFrame is invalid or missing 'timestamp'. Skipping MACD plot.")
                return
            
            # Align data lengths. TA-Lib functions return arrays same length as input.
            # prices_df['timestamp'] should align with MACD components.
            if len(prices_df) != len(macd_line):
                self.logger.warning(f"Length mismatch: Price data ({len(prices_df)}) vs MACD data ({len(macd_line)}). "
                                     "Ensure 'calculate' provides series of same length as input prices for proper plotting alignment.")
                # Attempt to align by taking the tail if prices_df is longer
                if len(prices_df) > len(macd_line):
                    timestamps = prices_df['timestamp'].iloc[-len(macd_line):].copy()
                else: # If other mismatches or MACD line is longer (unusual), skip.
                    self.logger.error("Cannot reliably align price data with MACD data for plotting. Skipping.")
                    return
            else:
                timestamps = prices_df['timestamp'].copy()


            fig, axes = plt.subplots(2, 1, figsize=(14, 8), dpi=100, sharex=True, 
                                     gridspec_kw={'height_ratios': [3, 1]}) # Main plot 3x taller than histogram

            # Plot MACD and Signal Line
            axes[0].plot(timestamps, macd_line, label='MACD Line', color='blue', linewidth=0.8)
            axes[0].plot(timestamps, signal_line, label='Signal Line', color='red', linestyle='--', linewidth=0.8)
            axes[0].axhline(0, color='grey', linestyle='--', linewidth=0.5) # Zero line for reference
            axes[0].set_title(f'MACD ({self.fast_period},{self.slow_period},{self.signal_period})')
            axes[0].set_ylabel('MACD Value')
            axes[0].legend(loc='upper left')
            axes[0].grid(True, linestyle=':', alpha=0.5)

            # Plot MACD Histogram
            # Color bars based on positive or negative values
            bar_colors = ['green' if x >= 0 else 'maroon' for x in macd_hist]
            axes[1].bar(timestamps, macd_hist, label='MACD Histogram', color=bar_colors, width=0.7) # Adjust width as needed
            axes[1].axhline(0, color='grey', linestyle='--', linewidth=0.5)
            axes[1].set_ylabel('Histogram')
            axes[1].set_xlabel('Timestamp')
            axes[1].legend(loc='upper left')
            axes[1].grid(True, linestyle=':', alpha=0.5)
            
            plt.tight_layout() # Adjust layout to prevent overlapping titles/labels
            plot_filename = f"{output_path_prefix}macd_plot.png"
            plt.savefig(plot_filename)
            plt.close(fig)
            self.logger.info(f"MACD plot saved to {plot_filename}")

        except Exception as e:
            self.logger.error(f"Error generating MACD plot: {e}", exc_info=True)
            if 'fig' in locals() and fig is not None:
                plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use MACD to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('-f', '--fast_period', type=int, default=12,
                        help='Fast period',
                        required=False)
    parser.add_argument('-sl', '--slow_period', type=int, default=26,
                        help='Slow period',
                        required=False)
    parser.add_argument('-sig', '--signal_period', type=int, default=9,
                        help='Signal period',
                        required=False)
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    args = parser.parse_args()

    if args.use_mock:
        closing_prices = [random.uniform(100, 200) for _ in range(100)]
    else:
        if not args.closing_prices:
            raise ValueError("Missing required argument: closing_prices")
        closing_prices = [float(price) for price in args.closing_prices.split(",")]

    macd_api = MACD(args.fast_period, args.slow_period, args.signal_period)
    calculations = macd_api.calculate(closing_prices=closing_prices)
    signal = macd_api.decide_signal(MACD={"calculations": calculations})