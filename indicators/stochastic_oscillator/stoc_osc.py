#!/usr/bin/env python3.5

import os
import argparse
import time
import numpy as np
from utilities.constants import Constants
from utilities.utils import get_timestamp
from utilities.logger import setup_logger


class StochasticOscillator:
    def __init__(self, interval="1d", k_period=14, d_period=3, threshold=20, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.interval = interval
        self.k_period = k_period
        self.d_period = d_period
        self.threshold = threshold / 100

    def stochastic_oscillator(self, high, low, close):
        start_time = time.perf_counter()
        self.logger.info("Calculating Stochastic Oscillator...")
        self.logger.info("high {}".format(self.d_period))
        self.logger.info("low {}".format(self.d_period))
        self.logger.info("close {}".format(self.d_period))
        self.logger.info("k_period {}".format(self.k_period))
        self.logger.info("d_period {}".format(self.d_period))

        highest_high = np.max(high[-self.k_period:])
        lowest_low = np.min(low[-self.k_period:])
        K = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        D = np.mean(K[-self.d_period:])
        
        self.logger.info("K: {}".format(K))
        self.logger.info("D: {}".format(D))
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Calculated Stochastic Oscillator in {:0.4f} seconds".format(elapsed_time))

        return K, D

    def decide_buy_sell_hold_signals(self, K, D):
        self.logger.info("Deciding Stochastic Oscillator buy/sell/hold signal...")
        self.logger.info("Threshold: {}".format(self.threshold))
       
        if K[-1] > D[-1] and K[-1] > 1 - self.threshold:
            signal = Constants.BUY_SIGNAL
        elif K[-1] < D[-1] and K[-1] < 1 - self.threshold:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Stochastic Oscillator to determine buy or sell signals")
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

    stoc_osc_api = StochasticOscillator(args.interval, args.k_period, args.d_period, args.threshold)
    K, D = stoc_osc_api.stochastic_oscillator(args.high, args.low, args.closing_price)
    signal = stoc_osc_api.decide_buy_sell_hold_signals(K, D)