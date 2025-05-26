#!/usr/bin/env python3.5

import os
import argparse
import time
import ta
import random
import pandas as pd
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger
import matplotlib.pyplot as plt
import numpy as np # Added for np.isnan, though not directly in plot, good for consistency if other plot methods use it


class IchimokuCloud(BaseIndicator):
    def __init__(self, tenkan_sen_n1=9, kijun_sen_n2=26,
                 senkou_span_b_n2=52, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.tenkan_sen_n1 = tenkan_sen_n1
        self.kijun_sen_n2 = kijun_sen_n2
        self.senkou_span_b_n2 = senkou_span_b_n2
        self.logger.info(f"Initialized IchimokuCloud with tenkan_sen_n1={self.tenkan_sen_n1}, kijun_sen_n2={self.kijun_sen_n2}, senkou_span_b_n2={self.senkou_span_b_n2}")

    def calculate(self, **data):
        start_time = time.perf_counter()
        high_prices = pd.Series(data.get("high_prices", []), dtype='float64') # Ensure dtype for empty Series
        low_prices = pd.Series(data.get("low_prices", []), dtype='float64')   # Ensure dtype for empty Series

        if high_prices.empty or low_prices.empty:
            self.logger.warning("High or low prices data is empty. Skipping Ichimoku calculation.")
            return pd.Series(dtype='float64'), pd.Series(dtype='float64'), pd.Series(dtype='float64'), pd.Series(dtype='float64')

        min_len_req = max(self.tenkan_sen_n1, self.kijun_sen_n2, self.senkou_span_b_n2)
        if len(high_prices) < min_len_req or len(low_prices) < min_len_req:
            self.logger.warning(f"Price data too short (High: {len(high_prices)}, Low: {len(low_prices)}) for configured periods (max: {min_len_req}). Skipping Ichimoku calculation.")
            return pd.Series(dtype='float64'), pd.Series(dtype='float64'), pd.Series(dtype='float64'), pd.Series(dtype='float64')

        self.logger.info(f"Calculating Ichimoku Cloud for {len(high_prices)} data points.")
        self.logger.debug(f"Input high_prices (first 5): {high_prices.head().tolist()}")
        self.logger.debug(f"Input low_prices (first 5): {low_prices.head().tolist()}")
        
        self.logger.info("Calculating Ichimoku Cloud Values...") # Original log, can be kept or removed if redundant with above
        tenkan_sen = (high_prices.rolling(window=self.tenkan_sen_n1).max() + 
                    low_prices.rolling(window=self.tenkan_sen_n1).min()) / 2
        kijun_sen = (high_prices.rolling(window=self.kijun_sen_n2).max() + 
                    low_prices.rolling(window=self.kijun_sen_n2).min()) / 2
        senkou_span_a = (tenkan_sen + kijun_sen) / 2
        senkou_span_b = (high_prices.rolling(window=self.senkou_span_b_n2).max() + 
                        low_prices.rolling(window=self.senkou_span_b_n2).min()) / 2
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        # Helper function (can be defined inside calculate or outside if used by plot too)
        def summarize_series(name, series):
            if series is None or series.empty: return f"{name}: Empty or None"
            # Filter out NaNs for logging actual values
            valid_values = series.dropna()
            if len(valid_values) > 6:
                return f"{name} (len {len(valid_values)}): First 3=[{', '.join(f'{x:.2f}' for x in valid_values.iloc[:3])}], Last 3=[{', '.join(f'{x:.2f}' for x in valid_values.iloc[-3:])}]"
            elif not valid_values.empty:
                return f"{name} (len {len(valid_values)}): Values=[{', '.join(f'{x:.2f}' for x in valid_values)}]"
            else: # All values were NaN
                return f"{name} (len {len(series)}): All values are NaN."

        self.logger.info("Calculated Ichimoku Components:")
        self.logger.info(summarize_series("Tenkan-sen", tenkan_sen))
        self.logger.info(summarize_series("Kijun-sen", kijun_sen))
        self.logger.info(summarize_series("Senkou Span A", senkou_span_a))
        self.logger.info(summarize_series("Senkou Span B", senkou_span_b))
        self.logger.info("Calculated Ichimoku Cloud Values in {:0.4f} seconds".format(elapsed_time))

        return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b

    def decide_signal(self, **data):
        current_price = data.get('current_price', '') # This is how main.py currently passes it if at all
        # Calculations are passed as a tuple from main.py via cv_data.get("calculations")
        # The tuple contains: (tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b)
        calculations = data.get("calculations") # Corrected key based on how process_indicators in main.py stores it

        if calculations is None or not isinstance(calculations, tuple) or len(calculations) != 4:
            self.logger.error("Missing or malformed Ichimoku calculation data. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL
        
        tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b = calculations
        
        if current_price == '' or current_price is None: # Check if current_price was not found or empty
            self.logger.warning("Current price is missing in decide_signal. Cannot make accurate decision.")
            # Depending on strategy, might return UNKNOWN_SIGNAL or proceed if logic allows partial data
            # For now, let's assume it's critical for this simplified logic
            # return Constants.UNKNOWN_SIGNAL # Or allow to proceed if logic can handle it

        # Use .iloc[-1] for latest value, ensure series is not empty first
        last_tenkan_val = f"{tenkan_sen.iloc[-1]:.2f}" if not tenkan_sen.empty else 'N/A'
        last_kijun_val = f"{kijun_sen.iloc[-1]:.2f}" if not kijun_sen.empty else 'N/A'
        last_span_a_val = f"{senkou_span_a.iloc[-1]:.2f}" if not senkou_span_a.empty else 'N/A'
        last_span_b_val = f"{senkou_span_b.iloc[-1]:.2f}" if not senkou_span_b.empty else 'N/A'

        self.logger.debug(f"Ichimoku signal inputs: current_price={current_price if current_price is not None else 'N/A'}, "
                         f"last_tenkan_sen={last_tenkan_val}, "
                         f"last_kijun_sen={last_kijun_val}, "
                         f"last_senkou_span_a={last_span_a_val}, "
                         f"last_senkou_span_b={last_span_b_val}")

        if senkou_span_a.empty or senkou_span_b.empty or current_price == '' or current_price is None: # Added current_price check here for safety
            self.logger.error("Missing required data (spans or current price) for decision. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL # Changed from signal = Constants.UNKNOWN_SIGNAL to direct return

        self.logger.info("Deciding Ichimoku Cloud buy/sell/hold signal...")
        # Original logic requires current_price to be a float for comparison
        try:
            current_price_float = float(current_price)
        except ValueError:
            self.logger.error(f"Could not convert current_price '{current_price}' to float. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        if current_price_float > max(senkou_span_a.iloc[-1], senkou_span_b.iloc[-1]):
            signal = Constants.BUY_SIGNAL
        elif current_price_float < min(senkou_span_a.iloc[-1], senkou_span_b.iloc[-1]):
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL

        self.logger.info("Signal detected: {}".format(signal))
        return signal

    def plot(self, calculated_data, prices_df, output_path_prefix):
        """
        Plots the Ichimoku Cloud components along with closing prices.
        calculated_data: Tuple (tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b) from calculate().
        prices_df: Pandas DataFrame with 'timestamp' and 'close' columns.
        output_path_prefix: Prefix for the output plot file name.
        """
        try:
            if not isinstance(calculated_data, tuple) or len(calculated_data) != 4:
                self.logger.warning("Ichimoku calculated data is not in the expected tuple format, skipping plot.")
                return

            tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b = calculated_data

            # Check if all required series are pandas Series and have data
            if not all(isinstance(s, pd.Series) for s in [tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b]):
                self.logger.warning("Ichimoku components are not all pandas Series. Skipping plot.")
                return
            if tenkan_sen.empty or kijun_sen.empty or senkou_span_a.empty or senkou_span_b.empty:
                self.logger.warning("One or more Ichimoku components are empty. Skipping plot.")
                return

            if prices_df is None or 'timestamp' not in prices_df.columns or 'close' not in prices_df.columns:
                self.logger.warning("Prices DataFrame is invalid for Ichimoku plot. Skipping.")
                return
            
            if len(prices_df) == 0:
                self.logger.warning("Price data is empty, skipping Ichimoku plot.")
                return

            # Align data lengths. Ichimoku components can have many NaNs at the start.
            # We'll plot based on the prices_df timestamps and align Ichimoku data to it.
            # TA-Lib's Ichimoku (if used) or manual rolling calcs often return same-length series with NaNs.
            timestamps = prices_df['timestamp']
            closing_prices = prices_df['close']
            
            # Ensure all series are aligned to the same index as timestamps for plotting
            # This assumes that the series from calculate() are already aligned with the end of the prices_df
            # and have the same length, possibly with NaNs at the beginning.
            # If prices_df is longer, we might need to take the tail of prices_df.
            # For simplicity, we assume direct plotting is possible if lengths match.
            # A more robust alignment would involve reindexing to prices_df.index if necessary.

            if not (len(timestamps) == len(tenkan_sen) == len(kijun_sen) == len(senkou_span_a) == len(senkou_span_b) == len(closing_prices)):
                 self.logger.warning(f"Length mismatch between price data ({len(prices_df)}) and Ichimoku components "
                                    f"(T: {len(tenkan_sen)}, K: {len(kijun_sen)}, SA: {len(senkou_span_a)}, SB: {len(senkou_span_b)}). "
                                     "Plotting might be misaligned or fail. Ensure 'calculate' provides series of same length as input prices.")
                # Attempting to plot what we have, but it might look odd if lengths truly differ due to an issue in calculate.
                # Or, could choose to return here. For now, proceed with caution.

            fig, ax = plt.subplots(figsize=(14, 7), dpi=100)
            
            ax.plot(timestamps, closing_prices, label='Close Price', color='black', alpha=0.7, linewidth=0.8)
            ax.plot(timestamps, tenkan_sen, label='Tenkan-sen', color='blue', linewidth=0.7)
            ax.plot(timestamps, kijun_sen, label='Kijun-sen', color='red', linewidth=0.7)
            
            # Plot Senkou Spans (Kumo Cloud) - NOT shifted forward as calculate() doesn't provide shifted data
            # When plotting Senkou Span A and B, they are typically shifted FORWARD.
            # The current `calculate` method does not do this shifting.
            # We will plot them as is, and note this limitation.
            ax.plot(timestamps, senkou_span_a, label='Senkou Span A (Unshifted)', color='green', linestyle='--', linewidth=0.7)
            ax.plot(timestamps, senkou_span_b, label='Senkou Span B (Unshifted)', color='magenta', linestyle='--', linewidth=0.7)
            
            # Fill the Kumo Cloud
            ax.fill_between(timestamps, senkou_span_a, senkou_span_b, 
                            where=senkou_span_a >= senkou_span_b, color='lightgreen', alpha=0.3, interpolate=True)
            ax.fill_between(timestamps, senkou_span_a, senkou_span_b, 
                            where=senkou_span_a < senkou_span_b, color='lightcoral', alpha=0.3, interpolate=True)

            # Chikou Span is not calculated by the current `calculate` method, so it cannot be plotted.
            self.logger.warning("Chikou Span is not calculated by this indicator version and will not be plotted.")
            self.logger.warning("Senkou Spans A & B are plotted without their typical forward shift.")

            ax.set_title(f'Ichimoku Cloud (Simplified - No Chikou, Unshifted Spans)')
            ax.set_xlabel('Timestamp')
            ax.set_ylabel('Price')
            ax.legend(loc='best', fontsize='small')
            ax.grid(True, linestyle=':', alpha=0.5)
            
            plot_filename = f"{output_path_prefix}ichimoku_plot.png"
            plt.savefig(plot_filename)
            plt.close(fig)
            self.logger.info(f"Ichimoku Cloud plot saved to {plot_filename}")

        except Exception as e:
            self.logger.error(f"Error generating Ichimoku Cloud plot: {e}", exc_info=True)
            if 'fig' in locals() and fig is not None:
                plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Ichimoku Cloud to determine buy or sell signals")
    parser.add_argument('-H', '--high_prices', type=str,
                        help='Comma-separated list of highest prices',
                        required=False)
    parser.add_argument('-L', '--low_prices', type=str,
                        help='Comma-separated list of lowest prices',
                        required=False)
    parser.add_argument('--tenkan_sen_n1', type=int, default=9,
                        help='Number of periods for Tenkan Sen calculation.')
    parser.add_argument('--kijun_sen_n2', type=int, default=26,
                        help='Number of periods for Kijun Sen calculation.')
    parser.add_argument('--senkou_span_b_n2', type=int, default=52,
                        help='Number of periods for Senkou Span B calculation.')
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    args = parser.parse_args()

    if args.use_mock:
        high_prices = [random.uniform(100, 200) for _ in range(100)]
        low_prices = [random.uniform(100, 200) for _ in range(100)]
        current_price = random.uniform(100, 200)
    else:
        if not args.high_prices or not args.low_prices:
            raise ValueError("Missing required arguments: high_prices, low_prices")
        high_prices = [float(price) for price in args.high_prices.split(',')]
        low_prices = [float(price) for price in args.low_prices.split(',')]
        current_price = high_prices[-1]  # Assuming the current price is the last high price

    ichimoku_api = IchimokuCloud(tenkan_sen_n1=args.tenkan_sen_n1, kijun_sen_n2=args.kijun_sen_n2,
                                 senkou_span_b_n2=args.senkou_span_b_n2)
    calculations = ichimoku_api.calculate(high_prices=high_prices, low_prices=low_prices)
    signal = ichimoku_api.decide_signal(IchimokuCloud={"calculations": calculations}, current_price=current_price)
