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

    def calculate(self, **data):
        closing_prices = data.get('closing_prices')
        double_top = self.check_double_top(closing_prices)
        double_bottom = self.check_double_bottom(closing_prices)
        return {'double_top': double_top, 'double_bottom': double_bottom}

    def check_double_top(self, closing_prices):
        start_time = time.perf_counter()
        self.logger.info("Calculating Double Top...")
        self.logger.info("Finding highest close in the first half of the array...")
        first_peak = np.argmax(closing_prices[:len(closing_prices)//2])
        self.logger.info(f"First peak index: {first_peak}")
        self.logger.info(f"Second half of closing_prices: {closing_prices[first_peak:len(closing_prices)]}")
        if first_peak == len(closing_prices)//2 - 1:
            self.logger.info("First peak is the last element in the first half of closing_prices. No valid double top pattern.")
            return -1
        self.logger.info("Finding highest closing price in the second half of the array...")
        second_peak = np.argmax(closing_prices[first_peak:]) + first_peak
        self.logger.info(f"Second peak index: {second_peak}")
        self.logger.info(f"Remaining closing_prices after second peak: {closing_prices[second_peak:]}")
        # Check if there is a valley between the two peaks
        self.logger.info("Checking if there is a valley between the two peaks...")
        if first_peak >= second_peak:
            self.logger.info("First peak is not before the second peak. No valid double top pattern.")
            return -1
        if second_peak < len(closing_prices) - 1:
            if (np.min(closing_prices[first_peak:second_peak]) < np.min(closing_prices[:first_peak]) and
                np.min(closing_prices[first_peak:second_peak]) < np.min(closing_prices[second_peak:])):
                double_top = second_peak
            else:
                double_top = -1
        else:
            self.logger.info("Second peak is the last element in closing_prices. No valid double top pattern.")
            double_top = -1
        
        self.logger.info("Double Top: {}".format(double_top))
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Double Top calculation finished in {:0.4f} seconds".format(elapsed_time))

        return double_top
    
    def check_double_bottom(self, closing_prices):
        start_time = time.perf_counter()
        self.logger.info("Calculating Double Bottom...")
        self.logger.info("Finding the lowest close in the first half of the array...")
        first_valley = np.argmin(closing_prices[:len(closing_prices)//2])
        self.logger.info(f"First valley index: {first_valley}")
        self.logger.info(f"Second half of closing_prices: {closing_prices[first_valley:len(closing_prices)]}")
        if first_valley == len(closing_prices)//2 - 1:
            self.logger.info("First valley is the last element in the first half of closing_prices. No valid double bottom pattern.")
            return -1
        self.logger.info("Finding the lowest closing_prices in the second half of the array...")
        second_valley = np.argmin(closing_prices[first_valley:]) + first_valley
        self.logger.info(f"Second valley index: {second_valley}")
        self.logger.info(f"Remaining closing_prices after second valley: {closing_prices[second_valley:]}")
        # Check if there is a peak between the two valleys
        self.logger.info("Checking if there is a peak between the two valleys...")
        if first_valley >= second_valley:
            self.logger.info("First valley is not before the second valley. No valid double bottom pattern.")
            return -1
        if second_valley < len(closing_prices) - 1:
            if (np.max(closing_prices[first_valley:second_valley]) > np.max(closing_prices[:first_valley]) and
                np.max(closing_prices[first_valley:second_valley]) > np.max(closing_prices[second_valley:])):
                double_bottom = second_valley
            else:
                double_bottom = -1
        else:
            self.logger.info("Second valley is the last element in closing_prices. No valid double bottom pattern.")
            double_bottom = -1
        
        self.logger.info("Double Bottom: {}".format(double_bottom))
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Double Bottom calculation finished in {:0.4f} seconds".format(elapsed_time))
        
        return double_bottom

    def decide_signal(self, **cv_data): # Renamed data to cv_data for clarity
        double_top = cv_data.get('double_top')
        double_bottom = cv_data.get('double_bottom')

        # Check if results are None (e.g. if calculate could return None for some error, though current one doesn't)
        if double_top is None or double_bottom is None:
            self.logger.error("Missing calculation result for double_top or double_bottom.")
            return Constants.UNKNOWN_SIGNAL

        # Core logic based on -1 indicating no pattern found:
        signal = Constants.HOLD_SIGNAL # Default to HOLD
        if double_bottom != -1: # Double bottom detected
            self.logger.info(f"Double Bottom pattern detected at index {double_bottom}.")
            signal = Constants.BUY_SIGNAL
        elif double_top != -1: # Double top detected (and no double bottom)
            self.logger.info(f"Double Top pattern detected at index {double_top}.")
            signal = Constants.SELL_SIGNAL
        else: # No pattern detected (both are -1)
            self.logger.info("No Double Top or Double Bottom pattern detected.")
            # Signal remains HOLD as per default

        self.logger.info("Signal detected: {}".format(signal))
        return signal


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
