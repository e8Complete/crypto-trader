#!/usr/bin/env python3.5

import os
import argparse
import time
from ta.volatility import supertrend
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class Supertrend:
    def __init__(self, lookback=10, multiplier=3, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.lookback = lookback
        self.multiplier = multiplier

    def calculate_supertrend(self, high_prices, low_prices, closing_prices):
        start_time = time.perf_counter()
        self.logger.info("Determining Supertrend...")
        self.logger.info("High Prices: {}".format(", ".join(high_prices)))
        self.logger.info("Low Prices: {}".format(", ".join(low_prices)))
        self.logger.info("Closing Prices: {}".format(", ".join(closing_prices)))
        self.logger.info("Multiplier: {}".format(self.multiplier))
        self.logger.info("Lookback: {}".format(self.lookback))
        self.logger.info("Multiplier: {}".format(self.multiplier))

        st = supertrend(high_prices, low_prices, closing_prices, self.lookback, self.multiplier)
        self.logger.info("Supertrend: {}".format(st))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Determined Supertrend Indicator in {:0.4f} seconds".format(elapsed_time))
        
        return st

    def decide_buy_sell_hold_signals(self, st, closing_prices):
        self.logger.info("Deciding Supertrend Indicator buy/sell/hold signal...")
        
        prev_st = st.shift(1)
        self.logger.info("Previous Supertrend: {}".format(prev_st))
        if closing_prices > st and prev_st <= closing_prices:
            signal = Constants.BUY_SIGNAL
        elif closing_prices < st and prev_st >= closing_prices:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Supertrend Indicator to determine buy or sell signals")
    parser.add_argument('-H', '--high', type=float,
                        help='Highest price',
                        required=True)
    parser.add_argument('-L', '--low', type=float,
                        help='Lowest price',
                        required=True)
    parser.add_argument('-C', '--closing_price', type=float,
                        help='Closing price',
                        required=True)
    parser.add_argument("--lookback", type=int, default=10,
                        help="Lookback window for the Supertrend indicator. It is the number of periods used to calculate the average true range (ATR) that is used in the Supertrend calculation.")
    parser.add_argument('--multiplier', type=int, default=3,
                        help='Multiplier factor for the Supertrend indicator. It is the factor by which the ATR is multiplied to calculate the upper and lower bands of the Supertrend line.')
    args = parser.parse_args()

    st_api = Supertrend()
    st = st_api.calculate_supertrend(high_prices, low_prices, closing_prices)
    signal = st_api.decide_buy_sell_hold_signals(st, closing_prices)