#!/usr/bin/env python3.5

import os
import argparse
import time
import numpy as np
import talib
import random
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger
import matplotlib.pyplot as plt


class EWT(BaseIndicator):
    def __init__(self, timeperiod1=20, timeperiod2=50, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.timeperiod1 = timeperiod1
        self.timeperiod2 = timeperiod2
        self.logger.info(f"Initialized EWT indicator with SMA timeperiods: TMA1={self.timeperiod1}, TMA2={self.timeperiod2}")

    def calculate(self, **data):
        closing_prices = data.get('closing_prices', '')
        if not closing_prices or len(closing_prices) < max(self.timeperiod1, self.timeperiod2, 2): # Min length for SMAs and ew_pattern
            self.logger.warning(f"Closing prices data is missing, empty, or too short (len: {len(closing_prices) if closing_prices else 'None'}). Skipping EWT calculation.")
            return {"ew_pattern": 0, "sma1": np.array([]), "sma2": np.array([])} # Return defaults
        self.logger.info(f"Starting EWT calculation for {len(closing_prices)} closing prices.")

        start_time = time.perf_counter()
        self.logger.info("Calculating Elliott Wave Theory Values...")
        if len(closing_prices) > 10:
            self.logger.debug(f"Closing prices sample (first 5): {closing_prices[:5]}, (last 5): {closing_prices[-5:]}")
        else:
            self.logger.debug(f"Closing prices: {closing_prices}")

        self.logger.info("Identifying Elliott waves...")
        waves = []
        # Need at least 2 closing prices to determine the first wave direction.
        # And at least 3 to determine waves[-2:] for ew_pattern.
        if len(closing_prices) >= 2: # Ensure there's enough data for at least one wave calculation
            for i in range(1, len(closing_prices)):
                if closing_prices[i] > closing_prices[i-1]:
                    waves.append(1)
                elif closing_prices[i] < closing_prices[i-1]:
                    waves.append(-1)
                else:
                    waves.append(0)
            
            if len(waves) > 10:
                self.logger.debug(f"Directional waves (first 5): {waves[:5]}, (last 5): {waves[-5:]}")
            else:
                self.logger.debug(f"Directional waves: {waves}")

            self.logger.info("Identifying Elliott wave patterns...")
            if len(waves) >= 2 and waves[-2:] == [1, -1]: # Check if waves has at least 2 elements
                ew_pattern = 1
            elif len(waves) >= 2 and waves[-2:] == [-1, 1]: # Check if waves has at least 2 elements
                ew_pattern = -1
            else:
                ew_pattern = 0
        else: # Not enough data for wave pattern
            self.logger.warning("Not enough closing prices to determine Elliott wave pattern. Defaulting pattern to 0.")
            waves = [] # Ensure waves is defined for logging even if not used for pattern
            ew_pattern = 0
            
        self.logger.info("Elliott wave patterns: {}".format(ew_pattern))
        
        self.logger.info(f"Calculating SMAs with timeperiods: TMA1={self.timeperiod1}, TMA2={self.timeperiod2}")
        sma1 = talib.SMA(np.array(closing_prices), timeperiod=self.timeperiod1)
        sma2 = talib.SMA(np.array(closing_prices), timeperiod=self.timeperiod2)
        
        # Helper to create summary string for an SMA array (can be defined locally or imported if it becomes common)
        def summarize_array(name, arr):
            if arr is None: return f"{name}: None"
            if len(arr) > 6:
                valid_values = arr[~np.isnan(arr)]
                if len(valid_values) > 6:
                    return f"{name} (len {len(valid_values)}): First 3=[{', '.join(f'{x:.2f}' for x in valid_values[:3])}], Last 3=[{', '.join(f'{x:.2f}' for x in valid_values[-3:])}]"
                elif len(valid_values) > 0:
                    return f"{name} (len {len(valid_values)}): Values=[{', '.join(f'{x:.2f}' for x in valid_values)}]"
                else:
                    return f"{name}: All values are NaN after filtering."
            elif len(arr) > 0:
                return f"{name} (len {len(arr)}): Values=[{', '.join(f'{x:.2f}' if not np.isnan(x) else 'NaN' for x in arr)}]"
            else:
                return f"{name}: Result is an empty array."

        self.logger.info("Calculated SMAs:")
        self.logger.info(summarize_array("SMA1", sma1))
        self.logger.info(summarize_array("SMA2", sma2))
        
        result = {
            "ew_pattern": ew_pattern,
            "sma1": sma1,
            "sma2": sma2
        }

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Elliott wave pattern calculation finished in {:0.4f} seconds".format(elapsed_time))

        return result

    def decide_signal(self, **cv_data): # Renamed data to cv_data
        # Data directly from calculate() output
        ew_pattern = cv_data.get('ew_pattern')
        sma1_series = cv_data.get('sma1')
        sma2_series = cv_data.get('sma2')

        # Modified initial data check
        if ew_pattern is None or sma1_series is None or sma2_series is None or \
           len(sma1_series) == 0 or len(sma2_series) == 0:
            self.logger.error("Missing required calculation data (ew_pattern, sma1, or sma2). Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL
    
        self.logger.info("Deciding Elliott Wave Theory buy/sell/hold signal...")
        
        # last_closing = closing_prices[-1] # Cannot get closing_prices this way from cv_data
        # last_rsi = rsi[-1] # Cannot get rsi this way from cv_data
        last_sma1 = sma1_series[-1]
        last_sma2 = sma2_series[-1]

        # Handle NaN for SMAs
        if np.isnan(last_sma1) or np.isnan(last_sma2):
            self.logger.warning("Latest SMA values are NaN (insufficient data for period). Holding.")
            return Constants.HOLD_SIGNAL
        
        # Log available data that would have been used
        self.logger.info(f"EW Pattern: {ew_pattern}")
        self.logger.info(f"Last SMA1: {last_sma1}")
        self.logger.info(f"Last SMA2: {last_sma2}")

        # Temporarily adapt signal logic
        signal = Constants.HOLD_SIGNAL # Default to HOLD
        self.logger.warning("EWT signal logic is currently partially disabled due to missing closing_price and RSI inputs to decide_signal method. Defaulting to HOLD.")
        
        # Original logic commented out for now:
        # if ew_pattern == 1 and last_rsi < 30 and last_closing > last_sma1 and last_closing > last_sma2:
        #     signal = Constants.BUY_SIGNAL
        # elif ew_pattern == -1 and last_rsi > 70 and last_closing < last_sma1 and last_closing < last_sma2:
        #     signal = Constants.SELL_SIGNAL
        # else:
        #     signal = Constants.HOLD_SIGNAL # This is already the default
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal

    def plot(self, calculated_data, prices_df, output_path_prefix):
        """
        Plots the closing prices, SMAs, and marks the latest EW Pattern.
        calculated_data: Dict from calculate() -> {"ew_pattern": int, "sma1": np.array, "sma2": np.array}.
        prices_df: Pandas DataFrame with 'timestamp' and 'close' columns.
        output_path_prefix: Prefix for the output plot file name.
        """
        try:
            ew_pattern = calculated_data.get('ew_pattern')
            sma1_series = calculated_data.get('sma1')
            sma2_series = calculated_data.get('sma2')

            if sma1_series is None or sma2_series is None or ew_pattern is None:
                self.logger.warning("EWT calculated data is missing components, skipping plot.")
                return

            if prices_df is None or 'timestamp' not in prices_df.columns or 'close' not in prices_df.columns:
                self.logger.warning("Prices DataFrame is invalid. Skipping EWT plot.")
                return

            # Align data lengths, assuming SMAs and ew_pattern correspond to the end of prices_df
            min_len = len(prices_df)
            if len(sma1_series) < min_len: min_len = len(sma1_series)
            if len(sma2_series) < min_len: min_len = len(sma2_series)
            
            if min_len == 0 : # No data to plot after considering SMA lengths
                 self.logger.warning("Not enough data points to plot EWT after aligning series. SMA series might be empty.")
                 return


            # Align all series to the shortest available length from the end
            timestamps = prices_df['timestamp'].iloc[-min_len:]
            closing_prices = prices_df['close'].iloc[-min_len:]
            sma1_aligned = sma1_series[-min_len:]
            sma2_aligned = sma2_series[-min_len:]


            fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
            
            ax.plot(timestamps, closing_prices, label='Close Price', color='black', alpha=0.7)
            ax.plot(timestamps, sma1_aligned, label=f'SMA ({self.timeperiod1})', linestyle='--')
            ax.plot(timestamps, sma2_aligned, label=f'SMA ({self.timeperiod2})', linestyle='-.')

            # Mark the latest EW Pattern
            # ew_pattern is a single value for the most recent 2-bar sequence. Mark it on the last point.
            pattern_text = "Neutral (0)" # Default text for title
            if len(timestamps) > 0: # Ensure there's a point to mark
                last_timestamp = timestamps.iloc[-1]
                last_close_price = closing_prices.iloc[-1]
                marker_style = 'o'
                marker_color = 'grey'

                if ew_pattern == 1: # Up then down (potential peak)
                    pattern_text = "Potential Peak (1)"
                    marker_style = 'v' 
                    marker_color = 'red'
                    ax.scatter(last_timestamp, last_close_price, 
                               marker=marker_style, color=marker_color, s=100, zorder=5, 
                               label=f'EW Pattern: {pattern_text}')
                elif ew_pattern == -1: # Down then up (potential trough)
                    pattern_text = "Potential Trough (-1)"
                    marker_style = '^'
                    marker_color = 'green'
                    ax.scatter(last_timestamp, last_close_price, 
                               marker=marker_style, color=marker_color, s=100, zorder=5, 
                               label=f'EW Pattern: {pattern_text}')
                else: # ew_pattern == 0
                    # pattern_text is already "Neutral (0)"
                    # Optionally, don't mark neutral patterns or use a small dot
                    # ax.scatter(last_timestamp, last_close_price, 
                    #            marker=marker_style, color=marker_color, s=50, zorder=5, 
                    #            label=f'EW Pattern: {pattern_text}')
                    self.logger.debug(f"EW Pattern is neutral (0) at last point: {last_timestamp}")


            ax.set_title(f'Simplified EWT (SMAs & Last 2-Bar Pattern: {pattern_text})')
            ax.set_xlabel('Timestamp')
            ax.set_ylabel('Price')
            ax.legend()
            ax.grid(True)
            
            plot_filename = f"{output_path_prefix}ewt_plot.png"
            plt.savefig(plot_filename)
            plt.close(fig)
            self.logger.info(f"EWT plot saved to {plot_filename}")

        except Exception as e:
            self.logger.error(f"Error generating EWT plot: {e}", exc_info=True)
            if 'fig' in locals() and fig is not None:
                plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Elliott Wave Theory to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    parser.add_argument('-n', '--period_length', type=int, default=Constants.DEFAULT_PERIOD_LENGTH,
                        help='Length of period. Defaults to {} if not provided.'.format(Constants.DEFAULT_PERIOD_LENGTH),
                        required=False)
    parser.add_argument('-t1', '--timeperiod1', type=int, default=20,
                        help="Time period for moving average 1")
    parser.add_argument('-t2', '--timeperiod2', type=int, default=50,
                        help='Time period for moving average 2')
    args = parser.parse_args()

    if args.use_mock:
        closing_prices = [random.uniform(100, 200) for _ in range(100)]
    else:
        if not args.closing_prices:
            raise ValueError("Missing required argument: closing_prices")
        closing_prices = [float(price) for price in args.closing_prices.split(',')]

    # Fetch RSI
    from indicators.relative_strength_index.rsi import RSI
    rsi_api = RSI(period_length=args.period_length)
    rsi = rsi_api.calculate(closing_prices=closing_prices)

    # Decide EWT signal
    ewt_api = EWT(timeperiod1=args.timeperiod1, timeperiod2=args.timeperiod2)
    ewt_data = ewt_api.calculate(closing_prices=closing_prices)
    signal = ewt_api.decide_signal(closing_prices=closing_prices,
                                   RSI={"calculations": rsi}, **ewt_data)
