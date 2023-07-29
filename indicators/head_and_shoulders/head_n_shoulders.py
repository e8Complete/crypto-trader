#!/usr/bin/env python3.5

import os
import argparse
import time
import ta
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class HeadAndShoulders:
    def __init__(self, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))

    def caclulate_head_and_shoulders(self, open, high, low, close):
        start_time = time.perf_counter()
        self.logger.info("Determining Head and Shoulders...")
        self.logger.info("Opening Prices: {}".format(open))
        self.logger.info("Closing prices: {}".format(", ".join(closing_prices)))
        self.logger.info("Opening Prices: {}".format(open))
        self.logger.info("Opening Prices: {}".format(open))

        cdl_head_shoulders = ta.patterns.CDLHEADANDSHOULDERS(open,high, low, close)
        cdl_head_shoulders_inverted = ta.patterns.CDLHEADANDSHOULDERSINVERTED(open,high, low, close)

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Head and Shoulders calculation finished in {:0.4f} seconds".format(elapsed_time))

        return cdl_head_shoulders, cdl_head_shoulders_inverted

    def decide_buy_sell_hold_signals(self, cdl_head_shoulders, cdl_head_shoulders_inverted):
        self.logger.info("Deciding Head and Shoulders buy/sell/hold signal...")
        if cdl_head_shoulders.iloc[-1] > 0:
            signal = Constants.BUY_SIGNAL
        elif cdl_head_shoulders_inverted.iloc[-1] > 0:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Head and Shoulrders to determine buy or sell signals")
    parser.add_argument('-O', '--open', type=float,
                        help='Highest price',
                        required=True)
    parser.add_argument('-H', '--high', type=float,
                        help='Highest price',
                        required=True)
    parser.add_argument('-L', '--low', type=float,
                        help='Lowest price',
                        required=True)
    parser.add_argument('-C', '--closing_price', type=float,
                        help='Closing price',
                        required=True)
    args = parser.parse_args()

    head_n_shoulders_api = HeadAndShoulders()
    cdl_head_shoulders, cdl_head_shoulders_inverted = head_n_shoulders_api.caclulate_head_and_shoulders(args.open, args.high, args.low, args.closing_price)
    signal = head_n_shoulders_api.decide_buy_sell_hold_signals(cdl_head_shoulders, cdl_head_shoulders_inverted)

