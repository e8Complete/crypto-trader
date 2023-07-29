#!/usr/bin/env python3.5

import os
import argparse
import time
import numpy as np
import matplotlib.pyplot as plt
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class DoubleTopBottom:
    def __init__(self, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))

    def check_double_top(self, closes):
        start_time = time.perf_counter()
        self.logger.info("Caclulating Double Top...")

        self.logger.info("Finding highest close in the first half of the array...")
        first_peak = np.argmax(closes[:len(closes)//2])
        self.logger.info("Finding highest close in the second half of the array...")
        second_peak = np.argmax(closes[first_peak:len(closes)]) + first_peak
        # Check if there is a valley between the two peaks
        self.logger.info("Checking if there is a valley between the two peaks...")
        if (np.min(closes[first_peak:second_peak]) < np.min(closes[:first_peak]) and
            np.min(closes[first_peak:second_peak]) < np.min(closes[second_peak:])):
            double_top = second_peak
        else:
            double_top = -1
        
        self.logger.info("Double Top: {}".format(double_top))
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Double Top calculation finished in {:0.4f} seconds".format(elapsed_time))

        return double_top
    
    def check_double_bottom(self, closes):
        start_time = time.perf_counter()
        self.logger.info("Caclulating Double Bottom...")

        self.logger.info("Finding the lowest close in the first half of the array...")
        first_valley = np.argmin(closes[:len(closes)//2])
        self.logger.info("Finding the lowest close in the second half of the array...")
        second_valley = np.argmin(closes[first_valley:len(closes)]) + first_valley
        self.logger.info("Checking if there is a peak between the two valleys...")
        if (np.max(closes[first_valley:second_valley]) > np.max(closes[:first_valley]) and
            np.max(closes[first_valley:second_valley]) > np.max(closes[second_valley:])):
            double_bottom = second_valley
        else:
            double_bottom = -1
        
        self.logger.info("Double Bottom: {}".format(double_bottom))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Double Bottom calculation finished in {:0.4f} seconds".format(elapsed_time))
        
        return double_bottom
    
    def plot_double_top_bottom(timestamps, highs, lows, double_top, double_bottom):
        fig, ax = plt.subplots()
        ax.plot(timestamps, highs, color='green')
        ax.plot(timestamps, lows, color='red')
        if double_top != -1:
            ax.plot(timestamps[double_top], highs[double_top], marker='^', markersize=10, color='red')
        if double_bottom != -1:
            ax.plot(timestamps[double_bottom], lows[double_bottom], marker='v', markersize=10, color='green')
        plt.show()

    def decide_buy_sell_hold_signals(self, double_top, double_bottom):
        self.logger.info("Deciding Double Top/Bottom buy/sell/hold signal...")
        if double_bottom != -1:
            signal = Constants.BUY_SIGNAL
        elif double_top != -1:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Triangle pattern to determine buy or sell signals")
    parser.add_argument('-H', '--high', type=float,
                        help='Highest price',
                        required=True)
    parser.add_argument('-L', '--low', type=float,
                        help='Lowest price',
                        required=True)
    parser.add_argument('-C', '--closing_price', type=float,
                        help='Closing price',
                        required=True)
    parser.add_argument("--interval", type=str, default="1d",
                        help="candlestick interval (default: 1d)")
    parser.add_argument('--k_period', type=int, default=14,
                        help='The number of periods to use in smoothing the %K line')
    parser.add_argument('--d_period', type=int, default=3,
                        help='The number of periods to use in calculating the %D line.')
    parser.add_argument("--threshold", type=float, default=20,
                        help="buy/sell threshold percentage (default: 20)")
    parser.add_argument('-s', '--symbol',
                        help='The symbol being plotted.',
                        required=False)
    args = parser.parse_args()

    dtb_api = DoubleTopBottom()
    double_top = dtb_api.check_double_top(closing_prices)
    double_bottom = dtb_api.check_double_bottom(closing_prices)
    signal = dtb_api.decide_buy_sell_hold_signals(double_top, double_bottom)