#!/usr/bin/env python3.5

import os
import time
import argparse
import numpy as np
import random
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger
import matplotlib.pyplot as plt

class RSI(BaseIndicator):
    def __init__(self, period_length=Constants.DEFAULT_PERIOD_LENGTH, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.period_length = period_length
        self.logger.info(f"Initialized RSI with period_length: {self.period_length}")

    def calculate(self, **data):
        start_time = time.perf_counter()
        closing_prices = data.get("closing_prices", "")
        
        if not closing_prices or len(closing_prices) <= self.period_length:
            self.logger.warning(f"Closing prices data is missing, empty, or too short (len: {len(closing_prices) if closing_prices else 'None'}) for period_length {self.period_length}. Skipping RSI calculation.")
            return np.array([]) # Return empty array
        self.logger.info(f"Calculating RSI for {len(closing_prices)} closing prices with period_length {self.period_length}.")
        
        # Ensure closing_prices is a list or np.array for slicing
        closing_prices_arr = np.array(closing_prices) # Convert if it's a list
        if len(closing_prices_arr) > 10:
            self.logger.debug(f"Closing prices sample (first 5): {closing_prices_arr[:5]}, (last 5): {closing_prices_arr[-5:]}")
        else:
            self.logger.debug(f"Closing prices: {closing_prices_arr}")
        # self.logger.debug("Period Length: {}".format(self.period_length)) # Moved to __init__
        self.logger.info("Calculating RSI...") # Original log, can be kept or merged.

        deltas = np.diff(closing_prices_arr) # Use closing_prices_arr
        seed = deltas[:self.period_length] # Corrected slicing for seed, should use period_length for average
        
        # Initial RSI calculation requires careful handling of up/down averages
        # Ensure division by zero is handled if no up or down movements in the initial seed
        up_sum = seed[seed >= 0].sum()
        down_sum = -seed[seed < 0].sum()

        if down_sum == 0: # Avoid division by zero if no losses in seed period
            rs = np.inf if up_sum > 0 else 1 # If up_sum also 0, RSI is neutral (50), rs=1. if up_sum > 0, RSI is 100, rs=inf.
        else:
            rs = (up_sum / self.period_length) / (down_sum / self.period_length) # Average gain / Average loss

        rsi = np.zeros_like(closing_prices_arr)
        rsi[:self.period_length] = 100. - 100. / (1. + rs) # Fill initial part with first RSI calc

        # Smoothed RSI for subsequent periods
        up = up_sum / self.period_length
        down = down_sum / self.period_length

        for i in range(self.period_length, len(closing_prices_arr)): # Iterate from period_length index
            delta = deltas[i - 1] 
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up * (self.period_length - 1) + upval) / self.period_length
            down = (down * (self.period_length - 1) + downval) / self.period_length
            
            if down == 0: # Avoid division by zero
                rs = np.inf if up > 0 else 1 
            else:
                rs = up / down
            rsi[i] = 100. - 100. / (1. + rs)
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        
        # Helper function (can be defined inside calculate or imported)
        def summarize_array(name, arr):
            if arr is None: return f"{name}: None"
            # RSI can have NaNs if Wilder's method starts with them, though this manual one might not.
            valid_values = arr[~np.isnan(arr)] 
            if len(valid_values) > 6:
                return f"{name} (len {len(valid_values)}): First 3=[{', '.join(f'{x:.2f}' for x in valid_values[:3])}], Last 3=[{', '.join(f'{x:.2f}' for x in valid_values[-3:])}]"
            elif len(valid_values) > 0:
                return f"{name} (len {len(valid_values)}): Values=[{', '.join(f'{x:.2f}' for x in valid_values)}]"
            elif len(arr) > 0: # Original array had data, but all were NaN after filtering
                 return f"{name} (len {len(arr)}): All values are NaN."
            else:
                return f"{name}: Result is an empty array."
        self.logger.info(summarize_array("RSI Series", rsi))
        self.logger.info("RSI calculation finished in {:0.4f} seconds".format(elapsed_time))
        
        return rsi

    def decide_signal(self, **data):
        rsi_series = data.get("calculations") # Corrected data retrieval
        
        if rsi_series is None or not isinstance(rsi_series, np.ndarray) or rsi_series.size < 1: # Check if it's a numpy array and has at least one element
            self.logger.error("RSI calculation data is missing, not a numpy array, or empty. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        # Ensure there are no NaNs in the last RSI value, if so, hold.
        if np.isnan(rsi_series[-1]):
            self.logger.warning(f"Last RSI value is NaN. Defaulting to HOLD signal. RSI series (last 5): {rsi_series[-5:]}")
            return Constants.HOLD_SIGNAL

        last_rsi_value = rsi_series[-1]
        self.logger.info(f"Making signal decision based on Last RSI Value: {last_rsi_value:.2f} (Thresholds: Buy < {Constants.RSI_BUY_THRESHOLD}, Sell > {Constants.RSI_SELL_THRESHOLD})")

        signal = Constants.HOLD_SIGNAL # Default to HOLD
        if last_rsi_value < Constants.RSI_BUY_THRESHOLD:
            signal = Constants.BUY_SIGNAL
        elif last_rsi_value > Constants.RSI_SELL_THRESHOLD:
            signal = Constants.SELL_SIGNAL
        
        self.logger.info(f"Signal detected: {signal}")
        return signal # Return the single, final signal string

    def plot(self, calculated_data, prices_df, output_path_prefix):
        """
        Plots the RSI series with overbought and oversold threshold lines.
        calculated_data: The RSI series (numpy array) from the calculate method.
        prices_df: Pandas DataFrame with a 'timestamp' column for the x-axis.
        output_path_prefix: Prefix for the output plot file name.
        """
        try:
            rsi_series = calculated_data # This is the output from self.calculate()
            
            if rsi_series is None or not isinstance(rsi_series, np.ndarray) or rsi_series.size == 0:
                self.logger.warning("RSI data is None or empty, skipping plot generation.")
                return

            if prices_df is None or 'timestamp' not in prices_df.columns:
                self.logger.warning("Prices DataFrame is invalid or missing 'timestamp'. Skipping RSI plot.")
                return
            
            # Align timestamps with RSI series length. TA-Lib (and this manual version) output NaNs at start.
            # The length of rsi_series should match prices_df if calculated on full df.
            if len(prices_df) != len(rsi_series):
                self.logger.warning(f"Length mismatch: Price data ({len(prices_df)}) vs RSI data ({len(rsi_series)}). "
                                     "Ensure 'calculate' provides series of same length as input prices for proper plotting alignment.")
                # Attempt to align by taking the tail if prices_df is longer
                if len(prices_df) > len(rsi_series):
                    timestamps = prices_df['timestamp'].iloc[-len(rsi_series):].copy()
                else: # If other mismatches or rsi_series is longer (unusual), skip.
                    self.logger.error("Cannot reliably align price data with RSI data for plotting. Skipping.")
                    return
            else:
                timestamps = prices_df['timestamp'].copy()


            fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
            
            ax.plot(timestamps, rsi_series, label=f'RSI ({self.period_length})', color='blue', linewidth=0.8)
            
            # Overbought and Oversold lines
            ax.axhline(Constants.RSI_SELL_THRESHOLD, color='red', linestyle='--', linewidth=0.7, label=f'Overbought ({Constants.RSI_SELL_THRESHOLD})')
            ax.axhline(Constants.RSI_BUY_THRESHOLD, color='green', linestyle='--', linewidth=0.7, label=f'Oversold ({Constants.RSI_BUY_THRESHOLD})')
            ax.axhline(50, color='grey', linestyle=':', linewidth=0.5, label='Mid-Level (50)')


            ax.set_title(f'Relative Strength Index (RSI - Period: {self.period_length})')
            ax.set_xlabel('Timestamp')
            ax.set_ylabel('RSI Value')
            ax.set_ylim(0, 100) # RSI is bounded between 0 and 100
            ax.legend()
            ax.grid(True, linestyle=':', alpha=0.5)
            
            plot_filename = f"{output_path_prefix}rsi_plot.png"
            plt.savefig(plot_filename)
            plt.close(fig) # Release memory
            self.logger.info(f"RSI plot saved to {plot_filename}")

        except Exception as e:
            self.logger.error(f"Error generating RSI plot: {e}", exc_info=True)
            if 'fig' in locals() and fig is not None:
                plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use RSI to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    parser.add_argument('-n', '--period_length', type=int, default=Constants.DEFAULT_PERIOD_LENGTH,
                        help='Length of period. Defaults to {} if not provided.'.format(Constants.DEFAULT_PERIOD_LENGTH),
                        required=False)
    args = parser.parse_args()

    if args.use_mock:
        closing_prices = [random.uniform(100, 200) for _ in range(100)]
    else:
        if not args.closing_prices:
            raise ValueError("Missing required argument: prices")
        closing_prices = [float(price) for price in args.closing_prices.split(',')]

    rsi_api = RSI(period_length=args.period_length)
    rsi = rsi_api.calculate(closing_prices=closing_prices)
    signals = rsi_api.decide_signal(rsi=rsi)
