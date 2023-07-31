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
        self.interval = interval
        self.k_period = k_period
        self.d_period = d_period
        self.threshold = threshold / 100

    def calculate(self, **data):
        start_time = time.perf_counter()
        closing_prices = data.get('closing_prices')
        high_prices = data.get('high_prices')
        low_prices = data.get('low_prices')
        self.logger.info("Calculating Stochastic Oscillator...")
        self.logger.info("k_period {}".format(self.k_period))
        self.logger.info("d_period {}".format(self.d_period))

        # Convert to numpy arrays
        closing_prices = np.array(closing_prices)
        high_prices = np.array(high_prices)
        low_prices = np.array(low_prices)

        # Calculate highest high and lowest low over the k_period
        if len(high_prices) < self.k_period or len(low_prices) < self.k_period:
            self.logger.error("Not enough data to calculate Stochastic Oscillator.")
            return np.nan, np.nan

        highest_high = np.max(high_prices[-self.k_period:])
        lowest_low = np.min(low_prices[-self.k_period:])

        # Calculate %K
        if highest_high != lowest_low:
            K = 100 * ((closing_prices[-1] - lowest_low) / (highest_high - lowest_low))
        else:
            self.logger.error("Highest high and lowest low are equal. Cannot calculate %K.")
            return np.nan, np.nan

        # Calculate %D
        if len(closing_prices) >= self.d_period:
            D_values = []
            for i in range(-self.d_period, 0):
                if i-self.k_period+1 < i+1:
                    low_prices_slice = low_prices[i-self.k_period+1:i+1]
                    high_prices_slice = high_prices[i-self.k_period+1:i+1]
                    if len(low_prices_slice) > 0 and len(high_prices_slice) > 0:
                        D_value = 100 * ((closing_prices[i] - np.min(low_prices_slice)) / 
                                        (np.max(high_prices_slice) - np.min(low_prices_slice)))
                        D_values.append(D_value)
            D = np.mean(D_values) if D_values else np.nan
        else:
            D = np.nan

        self.logger.info("K: {}".format(K))
        self.logger.info("D: {}".format(D))
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Calculated Stochastic Oscillator in {:0.4f} seconds".format(elapsed_time))

        return K, D

    def decide_signal(self, **data):
        K, D = data.get("StochasticOscillator", {}).get("calculations", (np.nan, np.nan))
        if np.isnan(K) or np.isnan(D):
            self.logger.error("Missing required data. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        self.logger.info("Deciding Stochastic Oscillator buy/sell/hold signal...")
        self.logger.info("Threshold: {}".format(self.threshold))
       
        if K > D and K > 1 - self.threshold:
            signal = Constants.BUY_SIGNAL
        elif K < D and K < 1 - self.threshold:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal


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
