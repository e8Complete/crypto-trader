#!/usr/bin/env python3.5

import os
import argparse
import time
import numpy as np
import random
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger
import matplotlib.pyplot as plt


class BollingerBands(BaseIndicator): # This is the first occurrence, will be ignored by targeting the second one if it exists.
    def __init__(self,  window_size=20, num_std=2, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
# talib import is already here. Ensure matplotlib.pyplot is added if not part of first block.
# Given the structure, the first SEARCH block for adding plt import should handle it.

class BollingerBands(BaseIndicator): # This is the targeted class definition
    def __init__(self,  window_size=20, num_std=2, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp)) # This line is part of the context
        self.logger.debug("Is test: {}".format(is_test)) # This line is part of the context
        self.window_size = window_size
        self.num_std = num_std
        self.logger.info(f"Initialized BollingerBands with window_size: {self.window_size}, num_std: {self.num_std}")

    def calculate(self, **data):
        closing_prices = data.get('closing_prices')
        if closing_prices is None:
            self.logger.error("Closing prices are missing.")
            return {"upper_band": None, "middle_band": None, "lower_band": None}

        np_closing_prices = np.array(closing_prices)
        self.logger.debug(f"Input closing_prices length: {len(np_closing_prices)}")
        if len(np_closing_prices) < self.window_size:
            self.logger.warning("Not enough data points to calculate Bollinger Bands accurately for window size {}. Data length: {}".format(self.window_size, len(np_closing_prices)))
            return {"upper_band": None, "middle_band": None, "lower_band": None} 

        start_time = time.perf_counter()
        self.logger.info("Calculating Bollinger Bands using TA-Lib...")
        self.logger.info("Window size: {}".format(self.window_size))
        self.logger.info("Number of STD: {}".format(self.num_std))

        try:
            upper, middle, lower = talib.BBANDS(np_closing_prices, 
                                                timeperiod=self.window_size,
                                                nbdevup=self.num_std,
                                                nbdevdn=self.num_std,
                                                matype=0) # Using SMA as default
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands with TA-Lib: {e}")
            return {"upper_band": None, "middle_band": None, "lower_band": None}

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Bollinger Bands TA-Lib calculation finished in {:0.4f} seconds".format(elapsed_time))

        if upper is not None and middle is not None and lower is not None:
            # Helper to create summary string for a band array
            def summarize_band(band_name, band_array):
                if len(band_array) > 6:
                    # Filter out NaNs for logging as they don't format well with .2f
                    valid_values = band_array[~np.isnan(band_array)]
                    if len(valid_values) > 6:
                        return f"{band_name} (len {len(valid_values)}): First 3=[{', '.join(f'{x:.2f}' for x in valid_values[:3])}], Last 3=[{', '.join(f'{x:.2f}' for x in valid_values[-3:])}]"
                    elif len(valid_values) > 0:
                        return f"{band_name} (len {len(valid_values)}): Values=[{', '.join(f'{x:.2f}' for x in valid_values)}]"
                    else:
                        return f"{band_name}: All values are NaN after filtering."
                elif len(band_array) > 0: # For very short arrays
                    return f"{band_name} (len {len(band_array)}): Values=[{', '.join(f'{x:.2f}' if not np.isnan(x) else 'NaN' for x in band_array)}]"
                else:
                    return f"{band_name}: Result is an empty array."

            self.logger.info("Calculated Bands:")
            self.logger.info(summarize_band("Upper", upper))
            self.logger.info(summarize_band("Middle", middle))
            self.logger.info(summarize_band("Lower", lower))
        else:
            self.logger.info("Calculated Bollinger Bands: Result contains None (calculation failed or input error).")

        return {"upper_band": upper, "middle_band": middle, "lower_band": lower}

    def decide_signal(self, current_closing_price=None, **cv_data): # cv_data is the output from calculate()
        if current_closing_price is None:
            self.logger.error("Current closing price not provided. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        upper_band_series = cv_data.get('upper_band')
        # middle_band_series = cv_data.get('middle_band') # Fetched but not used in original logic
        lower_band_series = cv_data.get('lower_band')

        if upper_band_series is None or lower_band_series is None or \
           len(upper_band_series) == 0 or len(lower_band_series) == 0:
            self.logger.error("Bollinger Bands data is missing or empty. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        # Get the latest band values
        latest_upper_band = upper_band_series[-1]
        latest_lower_band = lower_band_series[-1]
           
        # Check for NaN values which can occur at the beginning of TA-Lib results
        if np.isnan(latest_upper_band) or np.isnan(latest_lower_band):
            self.logger.warning("Latest Bollinger Band values are NaN (insufficient data for period). Holding.")
            return Constants.HOLD_SIGNAL
        
        self.logger.info(f"Making signal decision based on: current_closing_price={current_closing_price:.2f}, latest_upper_band={latest_upper_band:.2f}, latest_lower_band={latest_lower_band:.2f}")

        signal = Constants.HOLD_SIGNAL # Default to hold
        if current_closing_price < latest_lower_band:
            self.logger.info(f"Possible buy signal. Last price: {current_closing_price}, Lower band: {latest_lower_band}")
            signal = Constants.BUY_SIGNAL
        elif current_closing_price > latest_upper_band:
            self.logger.info(f"Possible sell signal. Last price: {current_closing_price}, Upper band: {latest_upper_band}")
            signal = Constants.SELL_SIGNAL
        else:
            self.logger.info(f"Possible hold signal. Last price: {current_closing_price} is between bands {latest_lower_band} and {latest_upper_band}.")
            
        self.logger.info("Signal detected: {}".format(signal))
        return signal

    def plot(self, calculated_data, prices_df, output_path_prefix):
        """
        Plots the Bollinger Bands along with the closing prices.
        calculated_data: Dict containing 'upper_band', 'middle_band', 'lower_band' numpy arrays.
        prices_df: Pandas DataFrame with 'timestamp' and 'close' columns.
        output_path_prefix: Prefix for the output plot file name.
        """
        try:
            upper_band = calculated_data.get('upper_band')
            middle_band = calculated_data.get('middle_band')
            lower_band = calculated_data.get('lower_band')
            
            if upper_band is None or middle_band is None or lower_band is None or \
               len(upper_band) == 0 or len(middle_band) == 0 or len(lower_band) == 0:
                self.logger.warning("Bollinger Bands data is None or empty, skipping plot generation.")
                return

            if prices_df is None or 'timestamp' not in prices_df.columns or 'close' not in prices_df.columns:
                self.logger.warning("Prices DataFrame is invalid or missing 'timestamp'/'close' columns. Skipping Bollinger Bands plot.")
                return
            
            # Align data: TA-Lib functions return arrays same length as input.
            # prices_df['close'] should align with band arrays.
            # If klines had more data initially than used for BB calc (due to window warmup),
            # we might need to align. For now, assume direct alignment.
            if len(prices_df) != len(upper_band):
                self.logger.warning(f"Length mismatch: Price data ({len(prices_df)}) vs BBands data ({len(upper_band)}). Trying to align by taking tail of price data if longer.")
                # Attempt to align if prices_df is longer (e.g. original klines) 
                # and bands have NaNs at the start from TA-Lib.
                # This assumes band arrays are same length as each other.
                if len(prices_df) > len(upper_band):
                     prices_df_aligned = prices_df.iloc[-len(upper_band):].copy() # Use .copy() to avoid SettingWithCopyWarning
                else: # If price data is shorter or equal, or alignment is complex, skip plot for safety.
                     self.logger.error("Cannot reliably align price data with BBands data for plotting. Skipping.")
                     return
            else:
                prices_df_aligned = prices_df.copy()


            timestamps = prices_df_aligned['timestamp']
            closing_prices = prices_df_aligned['close']

            fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
            
            ax.plot(timestamps, closing_prices, label='Close Price', color='black', alpha=0.7)
            ax.plot(timestamps, upper_band, label='Upper Band', color='red', linestyle='--')
            ax.plot(timestamps, middle_band, label='Middle Band (SMA)', color='blue', linestyle='-.')
            ax.plot(timestamps, lower_band, label='Lower Band', color='green', linestyle='--')
            
            # Fill between bands (optional, can be performance heavy for very large datasets)
            # ax.fill_between(timestamps, lower_band, upper_band, color='gray', alpha=0.1)

            ax.set_title(f'Bollinger Bands (Window: {self.window_size}, StdDev: {self.num_std})')
            ax.set_xlabel('Timestamp')
            ax.set_ylabel('Price')
            ax.legend()
            ax.grid(True)
            
            plot_filename = f"{output_path_prefix}bollingerbands_plot.png"
            plt.savefig(plot_filename)
            plt.close(fig) # Release memory
            self.logger.info(f"Bollinger Bands plot saved to {plot_filename}")

        except Exception as e:
            self.logger.error(f"Error generating Bollinger Bands plot: {e}", exc_info=True)
            if 'fig' in locals() and fig is not None:
                plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Bollinger Bands to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices_str', type=str,  # Renamed to avoid conflict with internal var name
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('-w', '--window_size', type=int, default=20,
                        help='Window size')
    parser.add_argument('-n', '--num_std', type=float, default=2,
                        help='Num std')
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example')
    args = parser.parse_args()

    closing_prices_data = [] # Initialize with an empty list

    if args.use_mock:
        base_price = 100
        # Generate more realistic mock data for BBands
        closing_prices_data = [base_price + random.uniform(-5, 5) for _ in range(100)]
        for i in range(1, len(closing_prices_data)):
            movement = random.uniform(-2, 2)
            closing_prices_data[i] = max(10, closing_prices_data[i-1] + movement) # Ensure prices stay positive
    else:
        if not args.closing_prices_str:
            raise ValueError("Missing required argument: --closing_prices_str")
        closing_prices_data = [float(price) for price in args.closing_prices_str.split(',')]

    bb_api = BollingerBands(window_size=args.window_size, num_std=args.num_std)
    
    # Calculate Bollinger Bands
    # The 'calculate' method expects a dictionary with 'closing_prices' key
    calculated_data = bb_api.calculate(closing_prices=closing_prices_data) 
    
    # Decide signal
    # The 'decide_signal' method expects current_closing_price and the output of calculate (cv_data)
    if closing_prices_data and calculated_data.get("upper_band") is not None : # Ensure there's data to decide upon
        current_price_for_signal = closing_prices_data[-1]
        signal = bb_api.decide_signal(current_closing_price=current_price_for_signal, **calculated_data)
        print(f"Calculated Bands (last 5 values):")
        if calculated_data["upper_band"] is not None:
             print(f"Upper: {calculated_data['upper_band'][-5:]}")
        if calculated_data["middle_band"] is not None:
            print(f"Middle: {calculated_data['middle_band'][-5:]}")
        if calculated_data["lower_band"] is not None:
            print(f"Lower: {calculated_data['lower_band'][-5:]}")
        print(f"Current Price: {current_price_for_signal}")
        print(f"Signal: {signal}")
    else:
        print("Could not generate signal due to insufficient data or calculation error.")
