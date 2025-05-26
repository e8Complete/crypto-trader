#!/usr/bin/env python3.5

import os
import argparse
import time
import random
import talib
import pandas as pd
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger
import matplotlib.pyplot as plt # Ensure matplotlib is imported
import numpy as np # Ensure numpy is imported

class Supertrend(BaseIndicator):
    def __init__(self, lookback=10, multiplier=3, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.lookback = lookback
        self.multiplier = multiplier
        self.logger.info(f"Initialized Supertrend with lookback={self.lookback}, multiplier={self.multiplier}")

    def supertrend(self, high_prices, low_prices, closing_prices, period, multiplier):
        self.logger.debug(f"Supertrend helper: period={period}, multiplier={multiplier}, data length={len(closing_prices)}")
        df = pd.DataFrame({
            'high': high_prices,
            'low': low_prices,
            'close': closing_prices
        })

        hl2 = (df['high'] + df['low']) / 2
        df['atr'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=period)
        self.logger.debug(f"ATR calculated (first 5 non-NaN): {df['atr'].dropna().head().tolist()}")
        
        df['upper_band'] = hl2 + multiplier * df['atr']
        df['lower_band'] = hl2 - multiplier * df['atr']
        self.logger.debug(f"Initial Upper Band (first 5): {df['upper_band'].head().tolist()}")
        self.logger.debug(f"Initial Lower Band (first 5): {df['lower_band'].head().tolist()}")
        
        df['in_uptrend'] = True # Initialize all as in uptrend
        
        for current in range(1, len(df.index)):
            previous = current - 1
            
            if df['close'][current] > df['upper_band'][previous]:
                if not df['in_uptrend'][previous]:
                    self.logger.debug(f"Index {current}: Trend changed to UP. Close={df['close'][current]:.2f} > Prev UpperBand={df['upper_band'][previous]:.2f}")
                df['in_uptrend'][current] = True
            elif df['close'][current] < df['lower_band'][previous]:
                if df['in_uptrend'][previous]:
                     self.logger.debug(f"Index {current}: Trend changed to DOWN. Close={df['close'][current]:.2f} < Prev LowerBand={df['lower_band'][previous]:.2f}")
                df['in_uptrend'][current] = False
            else:
                df.loc[current, 'in_uptrend'] = df.loc[previous, 'in_uptrend']
                
                if df['in_uptrend'][current] and df['lower_band'][current] < df['lower_band'][previous]:
                    self.logger.debug(f"Index {current}: Uptrend. Lower band adjusted from {df['lower_band'][previous]:.2f} to {df.loc[current, 'lower_band']:.2f} (would be {df['lower_band'][current]:.2f}, kept previous)")
                    df.loc[current, 'lower_band'] = df.loc[previous, 'lower_band']
                    
                if not df['in_uptrend'][current] and df['upper_band'][current] > df['upper_band'][previous]:
                    self.logger.debug(f"Index {current}: Downtrend. Upper band adjusted from {df['upper_band'][previous]:.2f} to {df.loc[current, 'upper_band']:.2f} (would be {df['upper_band'][current]:.2f}, kept previous)")
                    df['upper_band'][current] = df['upper_band'][previous]
                    
        return df

    def calculate(self, **data):
        start_time = time.perf_counter()
        high_prices = data.get("high_prices", [])
        low_prices = data.get("low_prices", [])
        closing_prices = data.get("closing_prices", [])

        required_len = self.lookback + 1 # ATR needs lookback, supertrend loop needs 1 previous
        if not all(p is not None and len(p) >= required_len for p in [high_prices, low_prices, closing_prices]):
            self.logger.warning(f"Price data is missing, empty, or too short (H:{len(high_prices if high_prices is not None else [])}, L:{len(low_prices if low_prices is not None else [])}, C:{len(closing_prices if closing_prices is not None else [])}) for lookback {self.lookback}. Skipping Supertrend.")
            return pd.DataFrame() # Return empty DataFrame

        self.logger.info(f"Calculating Supertrend for {len(closing_prices)} data points.")
        self.logger.debug(f"Input prices sample (first 5): H={high_prices[:5]}, L={low_prices[:5]}, C={closing_prices[:5]}")

        st_df = self.supertrend(high_prices, low_prices, closing_prices, self.lookback, self.multiplier)
        
        if not st_df.empty:
            st_df['supertrend_line'] = np.where(st_df['in_uptrend'], st_df['lower_band'], st_df['upper_band'])
            self.logger.info("Calculated Supertrend DataFrame (showing head and tail of key columns):")
            self.logger.info(f"ATR (sample): {st_df['atr'].dropna().head(3).tolist()} ... {st_df['atr'].dropna().tail(3).tolist()}")
            self.logger.info(f"Upper Band (sample): {st_df['upper_band'].dropna().head(3).tolist()} ... {st_df['upper_band'].dropna().tail(3).tolist()}")
            self.logger.info(f"Lower Band (sample): {st_df['lower_band'].dropna().head(3).tolist()} ... {st_df['lower_band'].dropna().tail(3).tolist()}")
            self.logger.info(f"Supertrend Line (sample): {st_df['supertrend_line'].dropna().head(3).tolist()} ... {st_df['supertrend_line'].dropna().tail(3).tolist()}")
            self.logger.info(f"In Uptrend (tail): {st_df['in_uptrend'].tail(5).tolist()}")
        else:
            self.logger.info("Supertrend calculation resulted in an empty DataFrame.")

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Determined Supertrend Indicator in {:0.4f} seconds".format(elapsed_time))
        
        return st_df

    def decide_signal(self, **data):
        st_df = data.get("calculations") # Corrected: main.py passes calculations directly via this key
        # Assuming 'closing_prices' passed in **data is the full kline closing price list for current_close
        closing_prices_input = data.get("closing_prices", []) 

        if st_df is None or not isinstance(st_df, pd.DataFrame) or st_df.empty:
            self.logger.error("Supertrend calculation data (st_df) is missing or empty. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL
        
        if not closing_prices_input or len(closing_prices_input) < 2:
            self.logger.error("Closing prices for signal decision not available or too short. Needs at least current and previous close.")
            return Constants.UNKNOWN_SIGNAL
        
        current_close = closing_prices_input[-1]
        # prev_close = closing_prices_input[-2] # Not used in this revised logic, but good to have if needed

        if len(st_df) < 2:
            self.logger.error("Supertrend DataFrame too short for signal decision. Needs at least 2 rows for prev/current state.")
            return Constants.UNKNOWN_SIGNAL

        last_st_data = st_df.iloc[-1]
        prev_st_data = st_df.iloc[-2]
        
        # Ensure 'supertrend_line' exists, if not, calculate it (though it should be from calculate method)
        if 'supertrend_line' not in st_df.columns:
             st_df['supertrend_line'] = np.where(st_df['in_uptrend'], st_df['lower_band'], st_df['upper_band'])
             last_st_data = st_df.iloc[-1] # Recalculate last_st_data if column was missing
             prev_st_data = st_df.iloc[-2]

        self.logger.info(f"Making Supertrend signal decision based on: Current Close={current_close:.2f}")
        self.logger.info(f"Last ST: Line={last_st_data['supertrend_line']:.2f}, Uptrend={last_st_data['in_uptrend']}. Prev ST: Line={prev_st_data['supertrend_line']:.2f}, Uptrend={prev_st_data['in_uptrend']}")
        
        signal = Constants.HOLD_SIGNAL
        if not prev_st_data['in_uptrend'] and last_st_data['in_uptrend']: # Trend flipped to UP
             self.logger.info("Supertrend flipped to UP.")
             signal = Constants.BUY_SIGNAL
        elif prev_st_data['in_uptrend'] and not last_st_data['in_uptrend']: # Trend flipped to DOWN
             self.logger.info("Supertrend flipped to DOWN.")
             signal = Constants.SELL_SIGNAL
        else: # No trend change, maintain current signal based on trend
            if last_st_data['in_uptrend']:
                self.logger.info("Currently in uptrend, maintaining HOLD (or implied BUY if already long).")
                # signal = Constants.BUY_SIGNAL # Or HOLD, depending on strategy if already in position
            else:
                self.logger.info("Currently in downtrend, maintaining HOLD (or implied SELL if already short).")
                # signal = Constants.SELL_SIGNAL # Or HOLD
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal

    def plot(self, calculated_data, prices_df, output_path_prefix):
        """
        Plots the closing prices and the Supertrend line.
        calculated_data: The Supertrend DataFrame from the calculate method.
        prices_df: Pandas DataFrame with 'timestamp' and 'close' columns.
        output_path_prefix: Prefix for the output plot file name.
        """
        try:
            st_df = calculated_data # This is the DataFrame from self.calculate()
            
            if st_df is None or not isinstance(st_df, pd.DataFrame) or st_df.empty:
                self.logger.warning("Supertrend data is None or empty, skipping plot generation.")
                return

            if prices_df is None or 'timestamp' not in prices_df.columns or 'close' not in prices_df.columns:
                self.logger.warning("Prices DataFrame is invalid or missing 'timestamp'/'close'. Skipping Supertrend plot.")
                return
            
            if 'supertrend_line' not in st_df.columns or 'in_uptrend' not in st_df.columns:
                self.logger.warning("Supertrend DataFrame is missing 'supertrend_line' or 'in_uptrend' columns. Calculating them for plot.")
                # Fallback: Recalculate 'supertrend_line' if it wasn't in the df from calculate (though it should be)
                if 'lower_band' in st_df.columns and 'upper_band' in st_df.columns and 'in_uptrend' in st_df.columns:
                     st_df['supertrend_line'] = np.where(st_df['in_uptrend'], st_df['lower_band'], st_df['upper_band'])
                else:
                    self.logger.error("Cannot generate supertrend_line for plot due to missing band/trend columns.")
                    return


            # Align data for plotting. Supertrend calculation might result in NaNs at the start.
            # Plotting from the first valid Supertrend value might be cleaner.
            first_valid_idx = st_df['supertrend_line'].first_valid_index()
            if first_valid_idx is None:
                self.logger.warning("Supertrend line contains all NaNs. Skipping plot.")
                return
                
            # Slice all data from the first valid Supertrend index onwards
            # Ensure indices are compatible for slicing. If prices_df has a different index (e.g., DatetimeIndex vs RangeIndex for st_df),
            # direct slicing with .loc[first_valid_idx:] might fail or misalign if st_df's index was reset.
            # Assuming st_df's index corresponds to row numbers after potential NaNs from ATR.
            # And prices_df's index (from klines) also corresponds to these row numbers.
            
            # If st_df's index is RangeIndex (0, 1, 2...), and prices_df's index is DatetimeIndex,
            # we need to align based on the number of rows from the end, or reindex st_df.
            # For simplicity, let's assume `prices_df` is the source of truth for timestamps and length.
            # And `st_df` is aligned with `prices_df` in terms of rows.
            
            st_df_plot = st_df.copy() # Use a copy for any modifications
            prices_df_plot = prices_df.copy()

            # Align based on the length of the shorter DataFrame, taking the tail
            min_len = min(len(prices_df_plot), len(st_df_plot))
            if min_len == 0:
                self.logger.warning("Not enough data after length alignment for Supertrend plot.")
                return

            prices_df_plot = prices_df_plot.iloc[-min_len:]
            st_df_plot = st_df_plot.iloc[-min_len:]
            
            # Reset index to ensure simple integer indexing for masks if needed, though boolean indexing should work on current index.
            # prices_df_plot.reset_index(drop=True, inplace=True)
            # st_df_plot.reset_index(drop=True, inplace=True)


            timestamps = prices_df_plot['timestamp']
            closing_prices = prices_df_plot['close']
            supertrend_line = st_df_plot['supertrend_line']
            in_uptrend = st_df_plot['in_uptrend']


            fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
            
            ax.plot(timestamps, closing_prices, label='Close Price', color='black', alpha=0.7, linewidth=0.8)
            
            # Plot Supertrend line segments based on trend direction for different colors
            uptrend_mask = in_uptrend
            downtrend_mask = ~in_uptrend 

            ax.plot(timestamps[uptrend_mask], supertrend_line[uptrend_mask], label='Supertrend (Uptrend)', color='green', linewidth=1.2)
            ax.plot(timestamps[downtrend_mask], supertrend_line[downtrend_mask], label='Supertrend (Downtrend)', color='red', linewidth=1.2)
            
            ax.set_title(f'Supertrend Indicator (Lookback: {self.lookback}, Multiplier: {self.multiplier})')
            ax.set_xlabel('Timestamp')
            ax.set_ylabel('Price')
            ax.legend()
            ax.grid(True, linestyle=':', alpha=0.5)
            
            plot_filename = f"{output_path_prefix}supertrend_plot.png"
            plt.savefig(plot_filename)
            plt.close(fig) # Release memory
            self.logger.info(f"Supertrend plot saved to {plot_filename}")

        except Exception as e:
            self.logger.error(f"Error generating Supertrend plot: {e}", exc_info=True)
            if 'fig' in locals() and fig is not None:
                plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Supertrend Indicator to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('-H', '--high_prices', type=str,
                        help='Comma-separated list of highest prices',
                        required=False)
    parser.add_argument('-L', '--low_prices', type=str,
                        help='Comma-separated list of lowest prices',
                        required=False)
    parser.add_argument("--lookback", type=int, default=10,
                        help="Lookback window for the Supertrend indicator. It is the number of periods used to calculate the average true range (ATR) that is used in the Supertrend calculation.")
    parser.add_argument('--multiplier', type=int, default=3,
                        help='Multiplier factor for the Supertrend indicator. It is the factor by which the ATR is multiplied to calculate the upper and lower bands of the Supertrend line.')
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    args = parser.parse_args()

    if args.use_mock:
        high_prices = [random.uniform(100, 200) for _ in range(100)]
        low_prices = [random.uniform(100, 200) for _ in range(100)]
        closing_prices = [random.uniform(100, 200) for _ in range(100)]
    else:
        if not args.high_prices or not args.low_prices or not args.closing_prices:
            raise ValueError("Missing required arguments: high_prices, low_prices, closing_prices")
        high_prices = [float(price) for price in args.high_prices.split(',')]
        low_prices = [float(price) for price in args.low_prices.split(',')]
        closing_prices = [float(price) for price in args.closing_prices.split(',')]

    st_api = Supertrend(lookback=args.lookback, multiplier=args.multiplier)
    st = st_api.calculate(high_prices=high_prices, low_prices=low_prices, closing_prices=closing_prices)
    signal = st_api.decide_signal(Supertrend={"calculations": st}, closing_prices=closing_prices)