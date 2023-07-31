#!/usr/bin/env python3.5

import os
import argparse
import time
import random
import pandas as pd
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class HeadAndShoulders(BaseIndicator):
    def __init__(self, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-"),
                 window_size=5):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.window_size = window_size
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))

    def find_head_and_shoulders(self, data):
        maxima = data[data == data.rolling(window=self.window_size, center=True).max()]
        minima = data[data == data.rolling(window=self.window_size, center=True).min()]
        maxima = maxima.dropna()
        minima = minima.dropna()
        pattern = []
        for i in range(self.window_size, len(maxima) - self.window_size):
            window = maxima.iloc[i - self.window_size: i + self.window_size]
            if window.iloc[self.window_size] == window.max():
                pattern.append(window.index[self.window_size])
        return pattern

    def find_inverted_head_and_shoulders(self, data):
        maxima = data[data == data.rolling(window=self.window_size, center=True).max()]
        minima = data[data == data.rolling(window=self.window_size, center=True).min()]
        maxima = maxima.dropna()
        minima = minima.dropna()
        pattern = []
        for i in range(self.window_size, len(minima) - self.window_size):
            window = minima.iloc[i - self.window_size: i + self.window_size]
            if window.iloc[self.window_size] == window.min():
                pattern.append(window.index[self.window_size])
        return pattern

    def calculate(self, **data):
        start_time = time.perf_counter()
        closing_prices = data.get("closing_prices", "")
        self.logger.info("Determining Head and Shoulders...")
        cdl_head_shoulders = self.find_head_and_shoulders(pd.Series(closing_prices))
        cdl_head_shoulders_inverted = self.find_inverted_head_and_shoulders(pd.Series(closing_prices))
        self.logger.info(f"cdl_head_shoulders {cdl_head_shoulders}")
        self.logger.info(f"cdl_head_shoulders_inverted {cdl_head_shoulders_inverted}")
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Head and Shoulders calculation finished in {:0.4f} seconds".format(elapsed_time))

        return cdl_head_shoulders, cdl_head_shoulders_inverted

    def decide_signal(self, **data):
        cdl_head_shoulders, cdl_head_shoulders_inverted = data.get("HeadAndShoulders", {}).get("calculations", [])
        if not cdl_head_shoulders or not cdl_head_shoulders_inverted:
            self.logger.error("Missing required data. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        self.logger.info("Deciding Head and Shoulders buy/sell/hold signal...")
        if len(cdl_head_shoulders) > 0 and cdl_head_shoulders[-1] == max(cdl_head_shoulders):
            signal = Constants.BUY_SIGNAL
        elif len(cdl_head_shoulders_inverted) > 0 and cdl_head_shoulders_inverted[-1] == min(cdl_head_shoulders_inverted):
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Head and Shoulrders to determine buy or sell signals")
    parser.add_argument('-O', '--opening_prices', type=float,
                        help='Comma-separated list of opening prices',
                        required=False)
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('-H', '--high_prices', type=str,
                        help='Comma-separated list of highest prices',
                        required=False)
    parser.add_argument('-L', '--low_prices', type=str,
                        help='Comma-separated list of lowest prices',
                        required=False)
    parser.add_argument('-w', '--window_size', type=int, default=5,
                        help='Window size')
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    args = parser.parse_args()
    if args.use_mock:
        opening_prices = [random.uniform(100, 200) for _ in range(100)]
        high_prices = [random.uniform(100, 200) for _ in range(100)]
        low_prices = [random.uniform(100, 200) for _ in range(100)]
        closing_prices = [random.uniform(100, 200) for _ in range(100)]
    else:
        if not args.opening_prices or not args.closing_prices or not args.high_prices or not args.low_prices:
            raise ValueError("Missing required arguments: opening_prices, closing_prices, high_prices, low_prices")
        opening_prices = [float(price) for price in args.opening_prices.split(',')]
        high_prices = [float(price) for price in args.high_prices.split(',')]
        low_prices = [float(price) for price in args.low_prices.split(',')]
        closing_prices = [float(price) for price in args.closing_prices.split(',')]

    head_n_shoulders_api = HeadAndShoulders(window_size=args.window_size)
    calculations = head_n_shoulders_api.calculate(opening_prices=opening_prices,
                                                  high_prices=high_prices,
                                                  low_prices=low_prices,
                                                  closing_prices=closing_prices)
    signal = head_n_shoulders_api.decide_signal(HeadAndShoulders={"calculations": calculations})

