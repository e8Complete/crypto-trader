#!/usr/bin/env python3.5

import os
import argparse
import time
import random
import pandas as pd
import talib # Added for SMA
import numpy as np # Added for np.isnan
import matplotlib.pyplot as plt # Added for plotting
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class OBV(BaseIndicator):
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
        self.logger.info(f"Initialized OBV indicator with timeperiod (for OBV SMA): {self.timeperiod}")

    def calculate(self, **data):
        start_time = time.perf_counter()
        
        closing_prices = data.get("closing_prices", [])
        volume = data.get("volume", [])

        if not closing_prices or not volume or len(closing_prices) == 0 or len(volume) == 0:
            self.logger.warning("Closing prices or volume data is missing or empty. Skipping OBV calculation.")
            return pd.Series(dtype='float64'), pd.Series(dtype='float64') # Return tuple of empty Series
        if len(closing_prices) != len(volume):
            self.logger.warning(f"Closing prices (len {len(closing_prices)}) and volume (len {len(volume)}) have different lengths. Skipping OBV calculation.")
            return pd.Series(dtype='float64'), pd.Series(dtype='float64')
            
        self.logger.info(f"Calculating OBV for {len(closing_prices)} data points.")
        self.logger.debug(f"Closing prices sample (first 5): {closing_prices[:5]}")
        self.logger.debug(f"Volume sample (first 5): {volume[:5]}")

        df = pd.DataFrame({
            'close': closing_prices,
            'volume': volume
        })

        df['obv'] = 0
        df.loc[df['close'] > df['close'].shift(1), 'obv'] = df['volume']
        df.loc[df['close'] < df['close'].shift(1), 'obv'] = -df['volume']
        df['obv'] = df['obv'].cumsum()
        
        obv_series = df['obv']
        
        # Calculate OBV SMA
        if obv_series.empty or len(obv_series) < self.timeperiod:
            self.logger.warning(f"OBV series is too short (len {len(obv_series)}) for SMA period {self.timeperiod}. OBV SMA will be empty.")
            df['obv_sma'] = pd.Series(dtype='float64')
        else:
            try:
                # Ensure OBV is float for talib; it should be if volume is numeric.
                df['obv_sma'] = talib.SMA(obv_series.astype(float), timeperiod=self.timeperiod)
            except Exception as e:
                self.logger.error(f"Error calculating OBV SMA with TA-Lib: {e}")
                df['obv_sma'] = pd.Series(dtype='float64')
        
        obv_sma_series = df['obv_sma']

        # Helper function
        def summarize_series(name, series):
            if series is None or series.empty: return f"{name}: Empty or None"
            valid_values = series.dropna()
            if len(valid_values) > 6:
                return f"{name} (len {len(valid_values)}): First 3=[{', '.join(f'{x:.2f}' for x in valid_values.iloc[:3])}], Last 3=[{', '.join(f'{x:.2f}' for x in valid_values.iloc[-3:])}]"
            elif not valid_values.empty:
                return f"{name} (len {len(valid_values)}): Values=[{', '.join(f'{x:.2f}' for x in valid_values)}]"
            else: 
                return f"{name} (len {len(series)}): All values are NaN or series is empty after dropna."

        self.logger.info(summarize_series("On-Balance Volume (OBV)", obv_series))
        self.logger.info(summarize_series("OBV SMA", obv_sma_series))
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Calculated On-Balance Volume (OBV) and SMA in {:0.4f} seconds".format(elapsed_time))
       
        return obv_series, obv_sma_series # Return as a tuple
    
    def decide_signal(self, **data):
        calculations_tuple = data.get("calculations")
        if calculations_tuple is None or not isinstance(calculations_tuple, tuple) or len(calculations_tuple) != 2:
            self.logger.error("OBV calculation data is missing or not in expected tuple format. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL
        obv_series, obv_sma_series = calculations_tuple

        if not isinstance(obv_series, pd.Series) or obv_series.empty:
            self.logger.error("OBV series is invalid or empty. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL
        
        if len(obv_series) < 2: # Original check for OBV
            self.logger.warning(f"OBV series too short (len {len(obv_series)}) to decide signal. Needs at least 2 points.")
            return Constants.UNKNOWN_SIGNAL

        last_obv_sma_val = 'N/A'
        if isinstance(obv_sma_series, pd.Series) and not obv_sma_series.empty and len(obv_sma_series) > 0 and not np.isnan(obv_sma_series.iloc[-1]):
            last_obv_sma_val = f"{obv_sma_series.iloc[-1]:.2f}"
            
        self.logger.info(f"Making signal decision based on: Last OBV={obv_series.iloc[-1]:.2f}, Prev OBV={obv_series.iloc[-2]:.2f}, Last OBV_SMA={last_obv_sma_val}")

        # Current signal logic remains based on raw OBV direction
        if obv_series.iloc[-1] > obv_series.iloc[-2]:
            signal = Constants.BUY_SIGNAL
        elif obv_series.iloc[-1] < obv_series.iloc[-2]:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal
        
    def plot(self, calculated_data, prices_df, output_path_prefix):
        """
        Plots the OBV and its SMA.
        calculated_data: Tuple (obv_series, obv_sma_series) from calculate().
        prices_df: Pandas DataFrame with a 'timestamp' column.
        output_path_prefix: Prefix for the output plot file name.
        """
        try:
            if not isinstance(calculated_data, tuple) or len(calculated_data) != 2:
                self.logger.warning("OBV calculated data is not in expected tuple format, skipping plot.")
                return

            obv_series, obv_sma_series = calculated_data

            if not isinstance(obv_series, pd.Series) or obv_series.empty:
                self.logger.warning("OBV series is None or empty, skipping plot generation.")
                return
            # obv_sma_series can be empty if OBV was too short for SMA calc, handle gracefully

            if prices_df is None or 'timestamp' not in prices_df.columns:
                self.logger.warning("Prices DataFrame is invalid for OBV plot. Skipping.")
                return
            
            if len(prices_df) == 0:
                self.logger.warning("Price data is empty, skipping OBV plot.")
                return

            # Align timestamps with the OBV series (which should be the primary series)
            timestamps = prices_df['timestamp'].iloc[-len(obv_series):].copy() if len(prices_df) >= len(obv_series) else prices_df['timestamp'].copy()
            
            # Ensure obv_series and timestamps have the same length for plotting
            if len(timestamps) != len(obv_series):
                self.logger.warning(f"Timestamp length ({len(timestamps)}) and OBV series length ({len(obv_series)}) mismatch after initial alignment. Plotting with OBV length.")
                timestamps = timestamps.iloc[-len(obv_series):] if len(timestamps) > len(obv_series) else timestamps # Adjust again if needed, or take first N of OBV

            fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
            
            ax.plot(timestamps, obv_series.iloc[-len(timestamps):], label='OBV', color='purple', linewidth=0.8)
            if isinstance(obv_sma_series, pd.Series) and not obv_sma_series.empty:
                # Align SMA series with the (potentially shortened) timestamps
                aligned_obv_sma = obv_sma_series.iloc[-len(timestamps):]
                ax.plot(timestamps, aligned_obv_sma, label=f'OBV SMA ({self.timeperiod})', color='orange', linestyle='--', linewidth=0.8)
            
            ax.set_title(f'On-Balance Volume (OBV) and SMA ({self.timeperiod})')
            ax.set_xlabel('Timestamp')
            ax.set_ylabel('OBV Value')
            ax.legend()
            ax.grid(True, linestyle=':', alpha=0.5)
            
            plot_filename = f"{output_path_prefix}obv_plot.png"
            plt.savefig(plot_filename)
            plt.close(fig)
            self.logger.info(f"OBV plot saved to {plot_filename}")

        except Exception as e:
            self.logger.error(f"Error generating OBV plot: {e}", exc_info=True)
            if 'fig' in locals() and fig is not None:
                plt.close(fig)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use On-Balance Volume (OBV) to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('-V', '--volume', type=str,
                        help='Comma-separated list of volumes',
                        required=False)
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    args = parser.parse_args()

    if args.use_mock:
        closing_prices = [random.uniform(100, 200) for _ in range(100)]
        volume = [random.randint(1000, 5000) for _ in range(100)]
    else:
        if not args.closing_prices or not args.volume:
            raise ValueError("Missing required arguments: closing_prices, volume")
        closing_prices = [float(price) for price in args.closing_prices.split(',')]
        volume = [float(vol) for vol in args.volume.split(',')]

    obv_api = OBV()
    obv = obv_api.calculate(closing_prices=closing_prices, volume=volume)
    signal = obv_api.decide_signal(OBV={"calculations": obv})