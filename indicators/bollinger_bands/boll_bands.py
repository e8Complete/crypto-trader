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


class BollingerBands(BaseIndicator):
    def __init__(self,  window_size=20, num_std=2, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.window_size = window_size
        self.num_std = num_std

    def calculate(self, **data):
        closing_prices = data.get('closing_prices')
        np_closing_prices = np.array(closing_prices)
        if len(np_closing_prices) < self.window_size:
            raise ValueError("Not enough data points to calculate Bollinger Bands")
        start_time = time.perf_counter()
        self.logger.info("Calculating Bollinger Bands...")
        self.logger.info("Closing prices: {}".format(",".join(map(str, np_closing_prices))))
        self.logger.info("Window size: {}".format(self.window_size))
        self.logger.info("Number of STD: {}".format(self.num_std))
        result = {}
        rolling_mean = np.mean(np_closing_prices[-self.window_size:])
        self.logger.info("Rolling mean: {}".format(rolling_mean))
        rolling_std = np.std(np_closing_prices[-self.window_size:])
        self.logger.info("Rolling STD: {}".format(rolling_std))
        result["upper_band"] = rolling_mean + self.num_std * rolling_std
        self.logger.info("Upper Band: {}".format(result["upper_band"]))
        result["middle_band"] = rolling_mean
        self.logger.info("Middle Band: {}".format(result["middle_band"]))
        result["lower_band"] = rolling_mean - self.num_std * rolling_std
        self.logger.info("Lower Band: {}".format(result["lower_band"]))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Bollinger Bands calculation finished in {:0.4f} seconds".format(elapsed_time))

        return result

    def decide_signal(self, **data):
        closing_price = data.get('closing_price')
        upper = data.get('upper_band')
        middle = data.get('middle_band')
        lower = data.get('lower_band')
        if not closing_price or not upper or not lower:
            self.logger.error("Missing required data. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        if closing_price < lower:
            self.logger.info(f"Possible buy signal. Last price: {closing_price}")
            signal = Constants.BUY_SIGNAL
        elif closing_price > upper:
            self.logger.info(f"Possible sell signal. Last price: {closing_price}")
            signal = Constants.SELL_SIGNAL
        else:
            self.logger.info(f"Possible hold signal. Last price: {closing_price}")
            signal = Constants.HOLD_SIGNAL

        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Bollinger Bands to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('-w', '--window_size', type=int, default=20,
                        help='Window size')
    parser.add_argument('-n', '--num_std', type=float, default=2,
                        help='Num std')
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example')
    args = parser.parse_args()

    if args.use_mock:
        base_price = 100
        closing_prices = [base_price + random.uniform(-50, 50) for _ in range(100)]
        for i in range(1, len(closing_prices)):
            closing_prices[i] += closing_prices[i-1]
    else:
        if not args.closing_prices:
            raise ValueError("Missing required argument: prices")
        closing_prices = [float(price) for price in args.closing_prices.split(',')]

    bb_api = BollingerBands(window_size=args.window_size, num_std=args.num_std)
    data = bb_api.calculate(closing_prices=closing_prices)
    signals = bb_api.decide_signal(closing_price=closing_prices[-1], **data)

