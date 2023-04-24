#!/usr/bin/env python3.5

import os
import time
import argparse
import numpy as np
from utilities.constants import Constants
from utilities.utils import get_timestamp
from utilities.logger import setup_logger
# Could also just use talib library
# https://hexdocs.pm/talib/TAlib.Indicators.RSI.html#content
# import talib
# rsi = talib.RSI(df['close'].values, timeperiod=14)
# last_rsi = rsi[-1]

class RSI():
    def __init__(self, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))

    def calculate_rsi(self, prices, period_length):
        start_time = time.perf_counter()
        self.logger.info("Calculating RSI...")
        self.logger.debug("Prices: {}}".format(", ".join(prices)))
        self.logger.debug("Period Length: {}".format(period_length))

        deltas = np.diff(prices)
        seed = deltas[:period_length + 1]
        up = seed[seed >= 0].sum() / period_length
        down = -seed[seed < 0].sum() / period_length
        rs = up / down
        rsi = np.zeros_like(prices)
        rsi[:period_length] = 100. - 100. / (1. + rs)

        for i in range(period_length, len(prices)):
            delta = deltas[i - 1]  # cause the diff is 1 shorter
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up * (period_length - 1) + upval) / period_length
            down = (down * (period_length - 1) + downval) / period_length

            rs = up / down
            rsi[i] = 100. - 100. / (1. + rs)
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("RSI calculation finished in {:0.4f} seconds".format(elapsed_time))
        
        return rsi

    def decide_buy_sell_hold_signals(self, rsi):
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
    parser.add_argument('-p', '--prices', type=list,
                        help='List of prices',
                        required=True)
    parser.add_argument('-n', '--period_length', type=int, default=Constants.DEFAULT_PERIOD_LENGTH,
                        help='Length of period. Defaults to {} if not provided.'.format(Constants.DEFAULT_PERIOD_LENGTH),
                        required=False)
    args = parser.parse_args()

    rsi_api = RSI()
    rsi = rsi_api.calculate_rsi(args.prices, args.period_length)
    signals = rsi_api.decide_buy_sell_hold_signals(rsi)