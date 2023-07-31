#!/usr/bin/env python3.5

import os
import argparse
import time
import random
import numpy as np
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class VWAP(BaseIndicator):
    def __init__(self, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))

    def calculate(self, **data):
        volumes = np.array(data.get('volumes'))
        closing_prices = np.array(data.get('closing_prices'))
        start_time = time.perf_counter()
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

    def decide_signal(self, **data):
        vwap = data.get("VWAP", {}).get("calculations", {})
        current_price = data.get("current_price", "")
        if not vwap or not current_price:
            self.logger.error("Missing required data. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

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
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('-V', '--volumes', type=str,
                        help='Comma-separated list of volumes',
                        required=False)
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    args = parser.parse_args()

    if args.use_mock:
        volumes = [random.uniform(100, 200) for _ in range(100)]
        closing_prices = [random.uniform(100, 200) for _ in range(100)]
    else:
        if not args.volumes or not args.closing_prices:
            raise ValueError("Missing required arguments: volumes, closing_prices")
        volumes = [float(volume) for volume in args.volumes.split(',')]
        closing_prices = [float(price) for price in args.closing_prices.split(',')]

    vwap_api = VWAP()
    vwap = vwap_api.calculate(volumes=volumes, closing_prices=closing_prices)
    signal = vwap_api.decide_signal(VWAP={"calculations": vwap}, current_price=closing_prices[-1])
