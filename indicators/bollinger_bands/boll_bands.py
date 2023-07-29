#!/usr/bin/env python3.5

import os
import argparse
import time
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger
import numpy as np


class BollingerBands:
    def __init__(self,  window_size=20, num_std=2, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.window_size = window_size
        self.num_std = num_std
    
    def calculate_bollinger_bands(self, closing_prices):
        if len(closing_prices) < self.window_size:
            raise ValueError("Not enough data points to calculate Bollinger Bands")
        start_time = time.perf_counter()
        self.logger.info("Calculating Bollinger Bands...")
        self.logger.info("Closing prices: {}".format(",".join(closing_prices)))
        self.logger.info("Window size: {}".format(self.window_size))
        self.logger.info("Number of STD: {}".format(self.num_std))

        rolling_mean = np.mean(closing_prices[-self.window_size:])
        self.logger.info("Rolling mean: {}".format(rolling_mean))
        rolling_std = np.std(closing_prices[-self.window_size:])
        self.logger.info("Rolling STD: {}".format(rolling_std))
        upper_band = rolling_mean + self.num_std * rolling_std
        self.logger.info("Upper Band: {}".format(upper_band))
        lower_band = rolling_mean - self.num_std * rolling_std
        self.logger.info("Lower Band: {}".format(lower_band))
        middle_band = rolling_mean
        self.logger.info("Middle Band: {}".format(middle_band))
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Bollinger Bands calculation finished in {:0.4f} seconds".format(elapsed_time))
 
        return upper_band, middle_band, lower_band
    
    def decide_buy_sell_hold_signals(self, closing_prices, upper_band, middle_band, lower_band):
        last_price = closing_prices[-1]
        last_upper_band = upper_band[-1]
        last_lower_band = lower_band[-1]
        if last_price < last_lower_band:
            self.logger.info("Possible buy signal. Last price: {}" % str(last_price))
            signal = Constants.BUY_SIGNAL
        elif last_price > last_upper_band:
            self.logger.info("Possible sell signal. Last price: {}" % str(last_price))
            signal = Constants.SELL_SIGNAL
        else:
            self.logger.info("Possible hold signal. Last price: {}" % str(last_price))
            signal = Constants.HOLD_SIGNAL

        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Bollinger Bands to determine buy or sell signals")
    parser.add_argument('-p', '--prices', type=list,
                        help='List of prices',
                        required=True)
    parser.add_argument('-w', '--window_size', type=int,
                        help='Window size',
                        required=False)
    parser.add_argument('-n', '--num_std', type=int,
                        help='Num std',
                        required=False)
    parser.add_argument('-s', '--symbol',
                        help='The symbol being plotted.',
                        required=False)
    args = parser.parse_args()

    bb_api = BollingerBands(args)
    upper_band, middle_band, lower_band = bb_api.calculate_bollinger_bands(args.prices)
    signals = bb_api.decide_buy_sell_hold_signals(args.prices, upper_band, middle_band, lower_band)