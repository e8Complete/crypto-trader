#!/usr/bin/env python3.5

import os
import argparse
import time
import numpy as np
import pandas as pd
import talib
import random
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class MACD(BaseIndicator):
    def __init__(self, fast_period=12, slow_period=26, signal_period=9, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def calculate(self, **data):
        closing_prices = data.get("closing_prices", [])
        start_time = time.perf_counter()
        self.logger.info("Calculating MACD...")
        self.logger.info("Fast Period: {}".format(self.fast_period))
        self.logger.info("Slow Period: {}".format(self.slow_period))
        self.logger.info("Signal Period: {}".format(self.signal_period))

        macd_line, signal_line, histogram = talib.MACD(np.array(closing_prices),
                    fastperiod=self.fast_period, slowperiod=self.slow_period,
                    signalperiod=self.signal_period)
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Calculated MACD in {:0.4f} seconds".format(elapsed_time))
 
        return macd_line, signal_line, histogram

    def decide_signal(self, **data):
        macd_line, signal_line, _ = data.get("MACD", {}).get("calculations", [])
        if macd_line.size == 0 or signal_line.size == 0:
            self.logger.error("Missing required data. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        self.logger.info("Deciding MACD buy/sell/hold signal...")
        data = pd.DataFrame({'MACD': macd_line, 'Signal Line': signal_line})
        last_row = data.iloc[-1]
        prev_row = data.iloc[-2]
        if last_row['MACD'] > last_row['Signal Line'] and prev_row['MACD'] <= prev_row['Signal Line']:
            signal = Constants.BUY_SIGNAL
        elif last_row['MACD'] < last_row['Signal Line'] and prev_row['MACD'] >= prev_row['Signal Line']:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use MACD to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('-f', '--fast_period', type=int, default=12,
                        help='Fast period',
                        required=False)
    parser.add_argument('-sl', '--slow_period', type=int, default=26,
                        help='Slow period',
                        required=False)
    parser.add_argument('-sig', '--signal_period', type=int, default=9,
                        help='Signal period',
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
        closing_prices = [float(price) for price in args.closing_prices.split(",")]

    macd_api = MACD(args.fast_period, args.slow_period, args.signal_period)
    calculations = macd_api.calculate(closing_prices=closing_prices)
    signal = macd_api.decide_signal(MACD={"calculations": calculations})