#!/usr/bin/env python3.5

import os
import argparse
import time
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class VWAP:
    def __init__(self, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))

    def calculate_vwap(self, volumes, closing_prices):
        start_time = time.perf_counter()
        self.logger.info("Volumes: {}".format(", ".join(volumes)))
        self.logger.info("Closing Prices: {}".format(", ".join(closing_prices)))

        total_volume = sum(volumes)
        self.logger.info("Total Volume: {}".format(total_volume))
        total_value = (closing_prices * volumes).sum()
        self.logger.info("Total Value: {}".format(total_value))
        vwap = total_value / total_volume
        self.logger.info("Volume Weighted Average Price (VWAP): {}".format(vwap))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Calulated Volume Weighted Average Price (VWAP) in {:0.4f} seconds".format(elapsed_time))
        
        return vwap

    def decide_buy_sell_hold_signals(self, vwap, current_price):
        self.logger.info("Deciding Volume Weighted Average Price (VWAP) buy/sell/hold signal...")
        if current_price > vwap:
            signal = Constants.BUY_SIGNAL
        elif current_price < vwap:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Volume Weighted Average Price (VWAP) to determine buy or sell signals")
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

    vwap_api = VWAP()
    vwap = vwap_api.calculate_vwap(volumes, closing_prices)
    signal = vwap_api.decide_buy_sell_hold_signals(vwap, current_price)