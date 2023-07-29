#!/usr/bin/env python3.5

import os
import argparse
import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import talib
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class MACD:
    def __init__(self, fast_period=12, slow_period=26, signal_period=9, is_test=True, timestamp=get_timestamp()):
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
    
    def calculate_macd(self, closing_prices):
        start_time = time.perf_counter()
        self.logger.info("Calculating MACD...")
        self.logger.info("Closing Prices: {}".format(", ".join(closing_prices)))
        self.logger.info("Fast Period: {}".format(self.fast_period))
        self.logger.info("Slow Period: {}".format(self.slow_period))
        self.logger.info("Signal Period: {}".format(self.signal_period))

        macd_line, signal_line, histogram = talib.MACD(closing_prices, fastperiod=self.fast_period, 
                                    slowperiod=self.slow_period, signalperiod=self.signal_period)
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Calculated MACD in {:0.4f} seconds".format(elapsed_time))
 
        return macd_line, signal_line, histogram

    def plot_macd(self, closing_prices, macd_line, signal_line, histogram):
        plt.figure(figsize=(12,8))
        plt.plot(closing_prices.index, macd_line, label='MACD Line')
        plt.plot(closing_prices.index, signal_line, label='Signal Line')
        plt.bar(closing_prices.index, histogram, label='Histogram', alpha=0.3)
        plt.legend()
        plt.show()

    def decide_buy_sell_hold_signals(self, macd_line, signal_line):
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
    parser.add_argument('-p', '--prices', type=float, nargs='+',
                        help='List of prices',
                        required=True)
    parser.add_argument('-f', '--fast_period', type=int,
                        help='Fast period',
                        required=False)
    parser.add_argument('-sl', '--slow_period', type=int,
                        help='Slow period',
                        required=False)
    parser.add_argument('-sig', '--signal_period', type=int,
                        help='Signal period',
                        required=False)
    parser.add_argument('-s', '--symbol',
                        help='The symbol being plotted.',
                        required=False)
    args = parser.parse_args()

    prices = np.array(args.prices)
    macd_api = MACD(args.fast_period, args.slow_period, args.signal_period)
    macd_line, signal_line, histogram = macd_api.calculate_macd(prices)
    macd_api.plot_macd(prices, macd_line, signal_line, histogram)
    signals = macd_api.decide_buy_sell_hold_signals(macd_line, signal_line)