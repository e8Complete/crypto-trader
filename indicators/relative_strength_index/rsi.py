#!/usr/bin/env python3.5

import os
import time
import argparse
import numpy as np
import random
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger

class RSI(BaseIndicator):
    def __init__(self, period_length=Constants.DEFAULT_PERIOD_LENGTH, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.period_length = period_length

    def calculate(self, **data):
        start_time = time.perf_counter()
        closing_prices = data.get("closing_prices", "")
        self.logger.info("Calculating RSI...")
        self.logger.debug("Closing prices: {}".format(", ".join(map(str, closing_prices))))
        self.logger.debug("Period Length: {}".format(self.period_length))

        deltas = np.diff(closing_prices)
        seed = deltas[:self.period_length + 1]
        up = seed[seed >= 0].sum() / self.period_length
        down = -seed[seed < 0].sum() / self.period_length
        rs = up / down
        rsi = np.zeros_like(closing_prices)
        rsi[:self.period_length] = 100. - 100. / (1. + rs)

        for i in range(self.period_length, len(closing_prices)):
            delta = deltas[i - 1]  # cause the diff is 1 shorter
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up * (self.period_length - 1) + upval) / self.period_length
            down = (down * (self.period_length - 1) + downval) / self.period_length

            rs = up / down
            rsi[i] = 100. - 100. / (1. + rs)
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("RSI calculation finished in {:0.4f} seconds".format(elapsed_time))
        
        return rsi

    def decide_signal(self, **data):
        rsi = data.get("rsi", "")
        if rsi is None or len(rsi) < 2:
            self.logger.error("Missing required data. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        self.logger.info("Deciding RSI buy/sell/hold signal...")
        signals = []
        for i in range(len(rsi)):
            self.logger.info(f"RSI: {rsi[i]:.2f}")
            if rsi[i] < Constants.RSI_BUY_THRESHOLD:
                self.logger.info("Possible buy signal on period %s" % str(i))
                signals.append(Constants.BUY_SIGNAL)
            elif rsi[i] > Constants.RSI_SELL_THRESHOLD:
                self.logger.info("Possible sell signal on period %s" % str(i))
                signals.append(Constants.SELL_SIGNAL)
            else:
                self.logger.info("Possible hold signal on period %s" % str(i))
                signals.append(Constants.HOLD_SIGNAL)
        
        self.logger.info("RSI signal at final period:")
        self.logger.info("Signal detected: {}".format(signals[-1]))
        return signals


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use RSI to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    parser.add_argument('-n', '--period_length', type=int, default=Constants.DEFAULT_PERIOD_LENGTH,
                        help='Length of period. Defaults to {} if not provided.'.format(Constants.DEFAULT_PERIOD_LENGTH),
                        required=False)
    args = parser.parse_args()

    if args.use_mock:
        closing_prices = [random.uniform(100, 200) for _ in range(100)]
    else:
        if not args.closing_prices:
            raise ValueError("Missing required argument: prices")
        closing_prices = [float(price) for price in args.closing_prices.split(',')]

    rsi_api = RSI(period_length=args.period_length)
    rsi = rsi_api.calculate(closing_prices=closing_prices)
    signals = rsi_api.decide_signal(rsi=rsi)
