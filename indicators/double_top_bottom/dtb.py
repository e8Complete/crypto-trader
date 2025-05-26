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


class DoubleTopBottom(BaseIndicator):
    def __init__(self, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.logger.info("Initialized DoubleTopBottom indicator.")
        self.peak_similarity_threshold = 0.05 # Peaks/Valleys within 5% of each other
        self.min_data_points = 20 # Minimum data points to attempt pattern recognition

    def calculate(self, **data):
        closing_prices = data.get('closing_prices')
        if closing_prices is None or len(closing_prices) < self.min_data_points:
            self.logger.warning(f"Closing prices data is missing, empty, or too short (len: {len(closing_prices) if closing_prices is not None else 'None'}, required: {self.min_data_points}). Skipping Double Top/Bottom calculation.")
            return {'double_top_pattern': None, 'double_bottom_pattern': None}
        
        self.logger.info(f"Starting Double Top/Bottom calculation for {len(closing_prices)} closing prices.")
        if len(closing_prices) > 10: # Log sample only if data is somewhat substantial
            self.logger.debug(f"Closing prices sample (first 5): {closing_prices[:5]}, (last 5): {closing_prices[-5:]}")
        else:
            self.logger.debug(f"Closing prices: {closing_prices}")
        
        double_top_pattern_info = self.check_double_top(closing_prices)
        double_bottom_pattern_info = self.check_double_bottom(closing_prices)
        
        return {'double_top_pattern': double_top_pattern_info, 'double_bottom_pattern': double_bottom_pattern_info}

    def check_double_top(self, closing_prices):
        start_time = time.perf_counter()
        self.logger.info("Checking for Double Top pattern...")
        
        if len(closing_prices) < self.min_data_points:
            self.logger.debug(f"Not enough data points ({len(closing_prices)}) for Double Top calculation, requires {self.min_data_points}.")
            return None

        first_half_len = len(closing_prices) // 2
        p1_idx = np.argmax(closing_prices[:first_half_len])
        p1_price = closing_prices[p1_idx]
        self.logger.debug(f"Double Top: First peak (P1) at index {p1_idx}, price {p1_price:.2f}")

        if p1_idx == first_half_len - 1 : # First peak is at the end of the first half
            self.logger.debug("Double Top: P1 at the end of first half, no valid pattern.")
            return None

        second_peak_search_area = closing_prices[p1_idx + 1:]
        if len(second_peak_search_area) < self.min_data_points // 4 : # Require some minimal length for 2nd peak search
             self.logger.debug("Double Top: Second peak search area too small.")
             return None
        
        p2_relative_idx = np.argmax(second_peak_search_area)
        p2_idx = p2_relative_idx + p1_idx + 1
        p2_price = closing_prices[p2_idx]
        self.logger.debug(f"Double Top: Second peak (P2) at index {p2_idx}, price {p2_price:.2f}")

        if p2_idx - p1_idx <= 1 : # Peaks are adjacent
            self.logger.debug("Double Top: P1 and P2 are adjacent, no valid pattern.")
            return None
        
        neck_idx = np.argmin(closing_prices[p1_idx + 1:p2_idx]) + p1_idx + 1
        neck_price = closing_prices[neck_idx]
        self.logger.debug(f"Double Top: Neckline (valley) at index {neck_idx}, price {neck_price:.2f}")

        # Pattern conditions
        peaks_similar = abs(p1_price - p2_price) / p1_price < self.peak_similarity_threshold
        valley_lower_than_peaks = neck_price < p1_price and neck_price < p2_price
        # Ensure P2 is not the last point for potential breakdown observation
        # For this method, we just identify the pattern; breakdown is for signal logic or further analysis
        # p2_not_last = p2_idx < len(closing_prices) - 1 

        pattern_info = None
        if peaks_similar and valley_lower_than_peaks: # and p2_not_last:
            pattern_info = {
                'pattern_found': True, 'type': 'double_top',
                'p1_idx': p1_idx, 'p1_price': p1_price,
                'p2_idx': p2_idx, 'p2_price': p2_price,
                'neck_idx': neck_idx, 'neck_price': neck_price
            }
            self.logger.info(f"Double Top pattern identified: P1@({p1_idx},{p1_price:.2f}), P2@({p2_idx},{p2_price:.2f}), Neck@({neck_idx},{neck_price:.2f})")
        else:
            self.logger.info(f"No confirmed Double Top pattern. Peaks similar: {peaks_similar}, Valley distinct: {valley_lower_than_peaks}.")

        elapsed_time = time.perf_counter() - start_time
        self.logger.info(f"Double Top check finished in {elapsed_time:.4f} seconds. Result: {'Found' if pattern_info else 'Not found'}")
        return pattern_info
    
    def check_double_bottom(self, closing_prices):
        start_time = time.perf_counter()
        self.logger.info("Checking for Double Bottom pattern...")

        if len(closing_prices) < self.min_data_points:
            self.logger.debug(f"Not enough data points ({len(closing_prices)}) for Double Bottom calculation, requires {self.min_data_points}.")
            return None

        first_half_len = len(closing_prices) // 2
        v1_idx = np.argmin(closing_prices[:first_half_len])
        v1_price = closing_prices[v1_idx]
        self.logger.debug(f"Double Bottom: First valley (V1) at index {v1_idx}, price {v1_price:.2f}")
        
        if v1_idx == first_half_len - 1:
            self.logger.debug("Double Bottom: V1 at the end of first half, no valid pattern.")
            return None

        second_valley_search_area = closing_prices[v1_idx + 1:]
        if len(second_valley_search_area) < self.min_data_points // 4:
            self.logger.debug("Double Bottom: Second valley search area too small.")
            return None
            
        v2_relative_idx = np.argmin(second_valley_search_area)
        v2_idx = v2_relative_idx + v1_idx + 1
        v2_price = closing_prices[v2_idx]
        self.logger.debug(f"Double Bottom: Second valley (V2) at index {v2_idx}, price {v2_price:.2f}")

        if v2_idx - v1_idx <= 1:
            self.logger.debug("Double Bottom: V1 and V2 are adjacent, no valid pattern.")
            return None
            
        neck_idx = np.argmax(closing_prices[v1_idx + 1:v2_idx]) + v1_idx + 1
        neck_price = closing_prices[neck_idx]
        self.logger.debug(f"Double Bottom: Neckline (peak) at index {neck_idx}, price {neck_price:.2f}")

        valleys_similar = abs(v1_price - v2_price) / v1_price < self.peak_similarity_threshold
        peak_higher_than_valleys = neck_price > v1_price and neck_price > v2_price
        # v2_not_last = v2_idx < len(closing_prices) - 1

        pattern_info = None
        if valleys_similar and peak_higher_than_valleys: # and v2_not_last:
            pattern_info = {
                'pattern_found': True, 'type': 'double_bottom',
                'p1_idx': v1_idx, 'p1_price': v1_price, # Using generic p1/p2 for dict keys
                'p2_idx': v2_idx, 'p2_price': v2_price,
                'neck_idx': neck_idx, 'neck_price': neck_price
            }
            self.logger.info(f"Double Bottom pattern identified: V1@({v1_idx},{v1_price:.2f}), V2@({v2_idx},{v2_price:.2f}), Neck@({neck_idx},{neck_price:.2f})")
        else:
            self.logger.info(f"No confirmed Double Bottom pattern. Valleys similar: {valleys_similar}, Peak distinct: {peak_higher_than_valleys}.")
            
        elapsed_time = time.perf_counter() - start_time
        self.logger.info(f"Double Bottom check finished in {elapsed_time:.4f} seconds. Result: {'Found' if pattern_info else 'Not found'}")
        return pattern_info

    def decide_signal(self, **cv_data):
        dt_info = cv_data.get('double_top_pattern')
        db_info = cv_data.get('double_bottom_pattern')

        signal = Constants.HOLD_SIGNAL
        if db_info and db_info.get('pattern_found'):
            # For a true buy signal, price should typically break above neckline after V2.
            # For this simplified version, identifying the pattern is enough.
            # More advanced: check if current_price > db_info['neck_price'] and after db_info['p2_idx']
            self.logger.info(f"Double Bottom pattern confirmed: V1@({db_info['p1_idx']},{db_info['p1_price']:.2f}), V2@({db_info['p2_idx']},{db_info['p2_price']:.2f}), Neck@({db_info['neck_idx']},{db_info['neck_price']:.2f}). Signal: BUY")
            signal = Constants.BUY_SIGNAL
        elif dt_info and dt_info.get('pattern_found'):
            # For a true sell signal, price should typically break below neckline after P2.
            # More advanced: check if current_price < dt_info['neck_price'] and after dt_info['p2_idx']
            self.logger.info(f"Double Top pattern confirmed: P1@({dt_info['p1_idx']},{dt_info['p1_price']:.2f}), P2@({dt_info['p2_idx']},{dt_info['p2_price']:.2f}), Neck@({dt_info['neck_idx']},{dt_info['neck_price']:.2f}). Signal: SELL")
            signal = Constants.SELL_SIGNAL
        else:
            self.logger.info("No confirmed Double Top or Double Bottom pattern for signal.")
        
        return signal

    def plot(self, calculated_data, prices_df, output_path_prefix):
        try:
            dt_info = calculated_data.get('double_top_pattern')
            db_info = calculated_data.get('double_bottom_pattern')

            if not prices_df.empty and 'timestamp' in prices_df.columns and 'close' in prices_df.columns:
                timestamps = prices_df['timestamp']
                closing_prices = prices_df['close']
            else:
                self.logger.warning("Price data is missing or invalid for plotting. Skipping DoubleTopBottom plot.")
                return

            fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
            ax.plot(timestamps, closing_prices, label='Close Price', color='black', alpha=0.7, linewidth=1)

            plot_title = "Double Top / Bottom Pattern"
            pattern_plotted = False

            if dt_info and dt_info.get('pattern_found'):
                p1_ts = prices_df['timestamp'].iloc[dt_info['p1_idx']]
                p2_ts = prices_df['timestamp'].iloc[dt_info['p2_idx']]
                neck_ts = prices_df['timestamp'].iloc[dt_info['neck_idx']]
                
                points_x = [p1_ts, neck_ts, p2_ts]
                points_y = [dt_info['p1_price'], dt_info['neck_price'], dt_info['p2_price']]
                
                ax.plot(points_x, points_y, marker='o', linestyle='--', color='red', label=f"Double Top ({dt_info['p1_price']:.2f} / {dt_info['p2_price']:.2f})")
                ax.scatter(points_x, points_y, color='red', s=50, zorder=5)
                # Annotate points
                ax.text(p1_ts, dt_info['p1_price'], " P1", color='red')
                ax.text(p2_ts, dt_info['p2_price'], " P2", color='red')
                ax.text(neck_ts, dt_info['neck_price'], " N", color='red')
                plot_title = f"Double Top Detected (P1:{dt_info['p1_price']:.2f}, P2:{dt_info['p2_price']:.2f}, N:{dt_info['neck_price']:.2f})"
                pattern_plotted = True
            
            if db_info and db_info.get('pattern_found'):
                v1_ts = prices_df['timestamp'].iloc[db_info['p1_idx']] # Using p1_idx from dict
                v2_ts = prices_df['timestamp'].iloc[db_info['p2_idx']] # Using p2_idx from dict
                neck_ts = prices_df['timestamp'].iloc[db_info['neck_idx']]
                
                points_x = [v1_ts, neck_ts, v2_ts]
                points_y = [db_info['p1_price'], db_info['neck_price'], db_info['p2_price']]

                ax.plot(points_x, points_y, marker='o', linestyle='--', color='green', label=f"Double Bottom ({db_info['p1_price']:.2f} / {db_info['p2_price']:.2f})")
                ax.scatter(points_x, points_y, color='green', s=50, zorder=5)
                # Annotate points
                ax.text(v1_ts, db_info['p1_price'], " V1", color='green')
                ax.text(v2_ts, db_info['p2_price'], " V2", color='green')
                ax.text(neck_ts, db_info['neck_price'], " N", color='green')
                # If both patterns are somehow detected (e.g. in different parts of data if logic was changed), ensure title reflects this.
                plot_title = f"Double Bottom Detected (V1:{db_info['p1_price']:.2f}, V2:{db_info['p2_price']:.2f}, N:{db_info['neck_price']:.2f})" if not pattern_plotted else plot_title + " & Double Bottom"
                pattern_plotted = True

            if not pattern_plotted:
                self.logger.info("No Double Top or Bottom pattern found to plot.")
                plt.close(fig) # Close the figure if nothing was plotted on it beyond base price
                return

            ax.set_title(plot_title)
            ax.set_xlabel('Timestamp')
            ax.set_ylabel('Price')
            ax.legend()
            ax.grid(True)
            
            plot_filename = f"{output_path_prefix}double_top_bottom_plot.png"
            plt.savefig(plot_filename)
            self.logger.info(f"Double Top/Bottom plot saved to {plot_filename}")
        
        except Exception as e:
            self.logger.error(f"Error generating Double Top/Bottom plot: {e}", exc_info=True)
        finally:
            if 'fig' in locals() and fig is not None: # Ensure fig exists before trying to close
                plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Double Top/Bottom pattern to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
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
        closing_prices = [float(price) for price in args.closing_prices.split(',')]

    dtb_api = DoubleTopBottom()
    data = dtb_api.calculate(closing_prices=np.array(closing_prices))
    signal = dtb_api.decide_signal(**data)
