#!/usr/bin/env python3.5

import os
import argparse
import time
import numpy as np
import random
import talib # Added for STOCHF
import matplotlib.pyplot as plt # Added for plotting
# import pandas as pd # Not explicitly used in core logic, but prices_df in plot is pd.DataFrame
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class StochasticOscillator(BaseIndicator):
    def __init__(self, interval="1d", k_period=14, d_period=3, threshold=20, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        # self.interval = interval # Interval is not used by TA-Lib's STOCHF
        self.k_period = k_period # This will be fastk_period for STOCHF
        self.d_period = d_period # This will be fastd_period for STOCHF
        self.raw_threshold = threshold # Store original config value (e.g., 20)
        self.oversold_level = self.raw_threshold # e.g. 20
        self.overbought_level = 100.0 - self.raw_threshold # e.g. 80
        self.logger.info(f"Initialized StochasticOscillator with k_period={self.k_period}, d_period={self.d_period}, Oversold={self.oversold_level}, Overbought={self.overbought_level}")

    def calculate(self, **data):
        high_prices = data.get('high_prices')
        low_prices = data.get('low_prices')
        closing_prices = data.get('closing_prices')

        # Ensure inputs are numpy arrays
        if not all(isinstance(p, np.ndarray) for p in [high_prices, low_prices, closing_prices]):
             # Attempt conversion if they are lists, else log error
            try:
                high_prices = np.array(high_prices, dtype=float)
                low_prices = np.array(low_prices, dtype=float)
                closing_prices = np.array(closing_prices, dtype=float)
            except Exception as e:
                self.logger.error(f"Error converting price data to numpy arrays: {e}. Skipping STOCHF calculation.")
                return np.array([]), np.array([])

        # TA-Lib STOCHF requires fastk_period >= 1 and fastd_period >= 1.
        # fastk_period is the lookback period for %K.
        # fastd_period is the SMA period for %D (which is an SMA of %K).
        # Minimum length for STOCHF output to be meaningful: fastk_period + fastd_period - 1
        # (e.g., k=5, d=3 -> 5 for first K, then 2 more for first D => 7 points)
        # TA-Lib functions typically return arrays of the same length as input, padded with NaNs.
        min_len_req = self.k_period + self.d_period - 1 
        if not (high_prices.size >= min_len_req and low_prices.size >= min_len_req and closing_prices.size >= min_len_req):
            self.logger.warning(f"Price data too short (H:{high_prices.size}, L:{low_prices.size}, C:{closing_prices.size}) for STOCHF (k_period={self.k_period}, d_period={self.d_period}). Min len: {min_len_req}. Skipping.")
            return np.array([]), np.array([])

        self.logger.info(f"Calculating Fast Stochastic Oscillator for {len(closing_prices)} data points using TA-Lib STOCHF.")
        start_time = time.perf_counter()
        try:
            fastk, fastd = talib.STOCHF(high_prices, low_prices, closing_prices,
                                        fastk_period=self.k_period,
                                        fastd_period=self.d_period,
                                        fastd_matype=0) # MAType 0 for SMA
        except Exception as e:
            self.logger.error(f"Error calculating STOCHF with TA-Lib: {e}")
            return np.array([]), np.array([])
        
        elapsed_time = time.perf_counter() - start_time
        
        def summarize_array(name, arr): # Helper for logging
            if arr is None: return f"{name}: None"
            valid_values = arr[~np.isnan(arr)]
            if len(valid_values) > 6:
                return f"{name} (len {len(valid_values)}): First 3=[{', '.join(f'{x:.2f}' for x in valid_values[:3])}], Last 3=[{', '.join(f'{x:.2f}' for x in valid_values[-3:])}]"
            elif len(valid_values) > 0:
                return f"{name} (len {len(valid_values)}): Values=[{', '.join(f'{x:.2f}' for x in valid_values)}]"
            elif len(arr) > 0:
                 return f"{name} (len {len(arr)}): All values are NaN."
            else:
                return f"{name}: Result is an empty array."

        self.logger.info(summarize_array("%K (Fast)", fastk))
        self.logger.info(summarize_array("%D (Fast)", fastd))
        self.logger.info(f"Calculated STOCHF in {elapsed_time:.4f} seconds.")
        return fastk, fastd

    def decide_signal(self, **cv_data):
        calculations_tuple = cv_data.get("calculations")
        if calculations_tuple is None or not isinstance(calculations_tuple, tuple) or len(calculations_tuple) != 2:
            self.logger.error("Stochastic calculation data is missing or not a tuple of two elements. Cannot decide.")
            return Constants.UNKNOWN_SIGNAL
        
        fastk_series, fastd_series = calculations_tuple
        if not all(isinstance(s, np.ndarray) and s.size >= 2 for s in [fastk_series, fastd_series]):
            self.logger.error(f"Stochastic %K (size {fastk_series.size if isinstance(fastk_series, np.ndarray) else 'N/A'}) or %D (size {fastd_series.size if isinstance(fastd_series, np.ndarray) else 'N/A'}) series too short or not numpy arrays. Cannot decide.")
            return Constants.UNKNOWN_SIGNAL

        # Get last two non-NaN values
        last_k = fastk_series[~np.isnan(fastk_series)][-1] if len(fastk_series[~np.isnan(fastk_series)]) > 0 else np.nan
        prev_k = fastk_series[~np.isnan(fastk_series)][-2] if len(fastk_series[~np.isnan(fastk_series)]) > 1 else np.nan
        last_d = fastd_series[~np.isnan(fastd_series)][-1] if len(fastd_series[~np.isnan(fastd_series)]) > 0 else np.nan
        prev_d = fastd_series[~np.isnan(fastd_series)][-2] if len(fastd_series[~np.isnan(fastd_series)]) > 1 else np.nan

        if any(np.isnan(v) for v in [last_k, prev_k, last_d, prev_d]):
            self.logger.warning(f"NaN values in recent K or D (LastK:{last_k}, PrevK:{prev_k}, LastD:{last_d}, PrevD:{prev_d}). Cannot reliably determine crossover or levels. Holding.")
            return Constants.HOLD_SIGNAL

        self.logger.info(f"Making signal decision based on: LastK={last_k:.2f}, PrevK={prev_k:.2f}, LastD={last_d:.2f}, PrevD={prev_d:.2f}. OB/OS Levels: {self.overbought_level}/{self.oversold_level}")

        signal = Constants.HOLD_SIGNAL
        # Buy signal: %K crosses above %D AND the crossover happens below the oversold level, OR %K moves up from oversold.
        if prev_k < prev_d and last_k > last_d and last_k < self.oversold_level: # Crossover up in oversold region
            self.logger.info(f"Buy Signal: %K crossed above %D in oversold region (K={last_k:.2f} < {self.oversold_level}).")
            signal = Constants.BUY_SIGNAL
        elif prev_k < self.oversold_level and last_k > self.oversold_level: # %K moved up from oversold
             self.logger.info(f"Buy Signal: %K moved up from oversold region (PrevK={prev_k:.2f} < {self.oversold_level}, LastK={last_k:.2f} > {self.oversold_level}).")
             signal = Constants.BUY_SIGNAL
        # Sell signal: %K crosses below %D AND the crossover happens above the overbought level, OR %K moves down from overbought.
        elif prev_k > prev_d and last_k < last_d and last_k > self.overbought_level: # Crossover down in overbought region
            self.logger.info(f"Sell Signal: %K crossed below %D in overbought region (K={last_k:.2f} > {self.overbought_level}).")
            signal = Constants.SELL_SIGNAL
        elif prev_k > self.overbought_level and last_k < self.overbought_level: # %K moved down from overbought
            self.logger.info(f"Sell Signal: %K moved down from overbought region (PrevK={prev_k:.2f} > {self.overbought_level}, LastK={last_k:.2f} < {self.overbought_level}).")
            signal = Constants.SELL_SIGNAL
            
        self.logger.info(f"Final Signal detected: {signal}")
        return signal

    def plot(self, calculated_data, prices_df, output_path_prefix):
        try:
            if not isinstance(calculated_data, tuple) or len(calculated_data) != 2:
                self.logger.warning("Stochastic calculated data is not tuple of two elements, skipping plot.")
                return
            fastk, fastd = calculated_data

            if not all(isinstance(s, np.ndarray) and s.size > 0 for s in [fastk, fastd]):
                self.logger.warning("%K or %D data is None or empty, skipping plot generation.")
                return

            if prices_df is None or 'timestamp' not in prices_df.columns:
                self.logger.warning("Prices DataFrame is invalid. Skipping Stochastic plot.")
                return
            
            # Align timestamps with stochastic series length.
            if len(prices_df) != len(fastk):
                self.logger.warning(f"Length mismatch: Price data ({len(prices_df)}) vs Stochastic data ({len(fastk)}). Aligning by tail.")
                timestamps = prices_df['timestamp'].iloc[-len(fastk):].copy() if len(prices_df) > len(fastk) else prices_df['timestamp'].copy()
                # Ensure fastk and fastd are also sliced if timestamps were shorter
                if len(timestamps) < len(fastk):
                    fastk = fastk[-len(timestamps):]
                    fastd = fastd[-len(timestamps):]
            else:
                timestamps = prices_df['timestamp'].copy()
            
            if len(timestamps) == 0: # Check after potential slicing
                self.logger.warning("Timestamps are empty after alignment, skipping plot.")
                return


            fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
            ax.plot(timestamps, fastk, label=f'%K ({self.k_period})', color='blue', linewidth=0.8)
            ax.plot(timestamps, fastd, label=f'%D ({self.d_period})', color='red', linestyle='--', linewidth=0.8)
            
            ax.axhline(self.overbought_level, color='grey', linestyle='--', linewidth=0.7, label=f'Overbought ({self.overbought_level:.0f})')
            ax.axhline(self.oversold_level, color='grey', linestyle='--', linewidth=0.7, label=f'Oversold ({self.oversold_level:.0f})')
            ax.axhline(50, color='lightgrey', linestyle=':', linewidth=0.5) # Mid-level

            ax.set_title(f'Fast Stochastic Oscillator ({self.k_period}, {self.d_period})')
            ax.set_xlabel('Timestamp')
            ax.set_ylabel('Value (0-100)')
            ax.set_ylim(0, 100)
            ax.legend()
            ax.grid(True, linestyle=':', alpha=0.5)
            
            plot_filename = f"{output_path_prefix}stochastic_plot.png"
            plt.tight_layout()
            plt.savefig(plot_filename)
            plt.close(fig)
            self.logger.info(f"Stochastic Oscillator plot saved to {plot_filename}")

        except Exception as e:
            self.logger.error(f"Error generating Stochastic Oscillator plot: {e}", exc_info=True)
            if 'fig' in locals() and fig is not None:
                plt.close(fig)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Stochastic Oscillator to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('-H', '--high_prices', type=str,
                        help='Comma-separated list of highest prices',
                        required=False)
    parser.add_argument('-L', '--low_prices', type=str,
                        help='Comma-separated list of lowest prices',
                        required=False)
    parser.add_argument("--interval", type=str, default="1d",
                        help="candlestick interval (default: 1d)")
    parser.add_argument('--k_period', type=int, default=14,
                        help='The number of periods to use in smoothing the %K line')
    parser.add_argument('--d_period', type=int, default=3,
                        help='The number of periods to use in calculating the %D line.')
    parser.add_argument("--threshold", type=float, default=20,
                        help="buy/sell threshold percentage (default: 20)")
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    args = parser.parse_args()

    if args.use_mock:
        high_prices = [random.uniform(1, 10) for _ in range(100)]
        low_prices = [random.uniform(1, 10) for _ in range(100)]
        closing_prices = [random.uniform(1, 10) for _ in range(100)]
    else:
        if not args.high_prices or not args.low_prices or not args.closing_prices:
            raise ValueError("Missing required arguments: high_prices, low_prices, closing_prices")
        high_prices = [float(price) for price in args.high_prices.split(',')]
        low_prices = [float(price) for price in args.low_prices.split(',')]
        closing_prices = [float(price) for price in args.closing_prices.split(',')]

    stoc_osc_api = StochasticOscillator(args.interval, args.k_period, args.d_period, args.threshold)
    K, D = stoc_osc_api.calculate(high_prices=high_prices, low_prices=low_prices, closing_prices=closing_prices)
    signal = stoc_osc_api.decide_signal(StochasticOscillator={"calculations": (K, D)})
