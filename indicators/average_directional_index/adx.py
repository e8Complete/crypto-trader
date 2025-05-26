#!/usr/bin/env python3.5

import os
import argparse
import time
import talib
import numpy as np
import random
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger
import matplotlib.pyplot as plt
# import pandas as pd # Not strictly needed here if prices_df is used as passed


class ADX(BaseIndicator):
    def __init__(self, timeperiod=14, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.timeperiod = timeperiod
        self.logger.info(f"Initialized ADX with timeperiod: {self.timeperiod}")

    def calculate(self, **data):
        high_prices = data.get('high_prices')
        low_prices = data.get('low_prices')
        closing_prices = data.get('closing_prices')

        if high_prices is None or len(high_prices) == 0:
            self.logger.error("High prices data is missing or empty.")
            return None
        if low_prices is None or len(low_prices) == 0:
            self.logger.error("Low prices data is missing or empty.")
            return None
        if closing_prices is None or len(closing_prices) == 0:
            self.logger.error("Closing prices data is missing or empty.")
            return None
            
        self.logger.debug(f"Input data lengths: high_prices={len(high_prices)}, low_prices={len(low_prices)}, closing_prices={len(closing_prices)}")

        np_high_prices = np.array(high_prices)
        np_low_prices = np.array(low_prices)
        np_close_prices = np.array(closing_prices)

        start_time = time.perf_counter()
        self.logger.info("Calculating Average Directional Index (ADX)...")
        self.logger.info("Timeperiod: {}".format(self.timeperiod))

        try:
            adx = talib.ADX(np_high_prices, np_low_prices, np_close_prices, timeperiod=self.timeperiod)
        except Exception as e:
            self.logger.error(f"Failed to calculate ADX: {e}")
            return None

        if adx is not None:
            # Log a summary of the ADX array to avoid overly long messages
            if len(adx) > 6: # TA-Lib ADX output might have NaNs at the start
                # Filter out NaNs for logging, as they don't format well with .2f
                adx_valid = adx[~np.isnan(adx)]
                if len(adx_valid) > 6:
                    self.logger.info(f"Calculated ADX (length {len(adx_valid)}): First 3=[{', '.join(f'{x:.2f}' for x in adx_valid[:3])}], Last 3=[{', '.join(f'{x:.2f}' for x in adx_valid[-3:])}]")
                elif len(adx_valid) > 0:
                    self.logger.info(f"Calculated ADX (length {len(adx_valid)}): Values=[{', '.join(f'{x:.2f}' for x in adx_valid)}]")
                else:
                    self.logger.info("Calculated ADX: All values are NaN after filtering.")
            elif len(adx) > 0 : # For very short arrays (mostly NaNs from TA-Lib)
                 self.logger.info(f"Calculated ADX (length {len(adx)}): Values (may include NaNs)=[{', '.join(f'{x:.2f}' if not np.isnan(x) else 'NaN' for x in adx)}]")
            else:
                self.logger.info("Calculated ADX: Result is an empty array.")
        else:
            self.logger.info("Calculated ADX: Result is None (calculation failed or input error).")

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Average Directional Index (ADX) calculation finished in {:0.4f} seconds".format(elapsed_time))
        return adx

    def decide_signal(self, **data):
        # Retrieve the ADX series passed by main.py under the "calculations" key
        adx_series = data.get("calculations") 
        
        # Check if adx_series is None or not long enough
        if adx_series is None or len(adx_series) < 2:
            self.logger.error("Missing required ADX calculation data or data too short. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL
        
        self.logger.debug(f"ADX series for decision (last 5 values): {adx_series[-5:] if adx_series is not None and len(adx_series) >= 5 else adx_series}")

        self.logger.info("Deciding ADX buy/sell/hold signal...")
        last_adx = adx_series[-1]
        prev_adx = adx_series[-2] # Store previous ADX value for clarity
        
        self.logger.info(f"Making signal decision based on: last_adx={last_adx:.2f}, prev_adx={prev_adx:.2f}")

        if last_adx > 25:
            # Condition for BUY: ADX crosses above 25
            if prev_adx < 25:
                signal = Constants.BUY_SIGNAL
            # Condition for HOLD (when ADX is above 25 and still rising)
            elif prev_adx < last_adx: 
                signal = Constants.HOLD_SIGNAL
            # Condition for SELL (when ADX is above 25 but starts falling)
            else:
                signal = Constants.SELL_SIGNAL
        else:
            # If ADX is below 25, it's considered a weak or non-trending market
            signal = Constants.HOLD_SIGNAL

        self.logger.info(f"Signal detected: {signal}")
        return signal

    def plot(self, calculated_data, prices_df, output_path_prefix):
        """
        Plots the ADX indicator values.
        calculated_data: The ADX series (numpy array) from the calculate method.
        prices_df: Pandas DataFrame with a 'timestamp' column for the x-axis.
        output_path_prefix: Prefix for the output plot file name.
        """
        try:
            adx_series = calculated_data # This is the output from self.calculate()
            
            if adx_series is None or len(adx_series) == 0:
                self.logger.warning("ADX data is None or empty, skipping plot generation.")
                return

            if prices_df is None or 'timestamp' not in prices_df.columns or len(prices_df) != len(adx_series):
                self.logger.warning(f"Prices DataFrame is invalid or length mismatch (ADX: {len(adx_series)}, Price: {len(prices_df) if prices_df is not None else 'None'}). Skipping ADX plot.")
                # As a fallback, if timestamps are missing, we could plot against sequence numbers,
                # but it's less informative. For now, require timestamps.
                # If price_df has more data than adx_series (due to TA-Lib NaNs at start of adx_series),
                # align them by taking the tail of prices_df.
                # However, TA-Lib functions usually return arrays of the same length as input, padded with NaNs.
                # So, prices_df and adx_series should ideally have same length.
                # Let's assume they are of same length for now.
                # A more robust solution would align based on non-NaN ADX values and corresponding timestamps.
                return

            fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
            
            # Ensure timestamps are in a plottable format if coming directly from klines
            # If prices_df['timestamp'] is already datetime objects, this is fine.
            # If they are strings or milliseconds, they need conversion.
            # Assuming prices_df['timestamp'] is compatible with matplotlib plotting.
            timestamps = prices_df['timestamp']

            ax.plot(timestamps, adx_series, label='ADX', color='blue')
            ax.axhline(25, color='red', linestyle='--', linewidth=0.7, label='ADX Threshold (25)')
            
            ax.set_title(f'Average Directional Index (ADX) - Timeperiod: {self.timeperiod}')
            ax.set_xlabel('Timestamp')
            ax.set_ylabel('ADX Value')
            ax.legend()
            ax.grid(True)
            
            plot_filename = f"{output_path_prefix}adx_plot.png"
            plt.savefig(plot_filename)
            plt.close(fig) # Release memory
            self.logger.info(f"ADX plot saved to {plot_filename}")

        except Exception as e:
            self.logger.error(f"Error generating ADX plot: {e}", exc_info=True)
            if 'fig' in locals() and fig is not None: # Ensure fig exists before trying to close if error occurs mid-plot
                plt.close(fig)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Average Directional Index (ADX) to determine buy or sell signals")
    parser.add_argument('-H', '--high_prices', type=str,
                        help='Comma-separated list of highest prices',
                        required=False)
    parser.add_argument('-L', '--low_prices', type=str,
                        help='Comma-separated list of lowest prices',
                        required=False)
    parser.add_argument('-C', '--close_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    parser.add_argument("--timeperiod", type=int, default=14,
                        help="Time period")
    args = parser.parse_args()

    if args.use_mock:
        high_prices = [random.uniform(100, 200) for _ in range(100)]
        low_prices = [random.uniform(50, 100) for _ in range(100)]
        close_prices = [random.uniform(75, 125) for _ in range(100)]
    else:
        if not args.high_prices or not args.low_prices or not args.close_prices:
            raise ValueError("Missing required arguments: high_prices, low_prices, close_prices")

        high_prices = [float(price) for price in args.high_prices.split(',')]
        low_prices = [float(price) for price in args.low_prices.split(',')]
        close_prices = [float(price) for price in args.close_prices.split(',')]
    
    adx_api = ADX(args.timeperiod)
    data = adx_api.calculate(high_prices=high_prices, low_prices=low_prices, closing_prices=close_prices)
    adx_api.decide_signal(adx=data)