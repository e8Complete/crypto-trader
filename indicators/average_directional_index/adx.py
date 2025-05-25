#!/usr/bin/env python3.5

import os
import argparse
import time
import talib
import numpy as np
import random
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class ADX(BaseIndicator):
    def __init__(self, timeperiod=14, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.timeperiod = timeperiod

    def calculate(self, **data):
        high_prices = data.get('high_prices')
        low_prices = data.get('low_prices')
        closing_prices = data.get('closing_prices')
        np_high_prices = np.array(high_prices)
        np_low_prices = np.array(low_prices)
        np_close_prices = np.array(closing_prices)

        start_time = time.perf_counter()
        self.logger.info("Calculating Average Directional Index (ADX)...")
        self.logger.info("Timeperiod: {}".format(self.timeperiod))

        try:
            adx = talib.ADX(np_high_prices, np_low_prices, np_close_prices, timeperiod=self.timeperiod)
        except Exception as e:
            self.logger.error(f"Failed to calculate ADX: {e}")
            return None

        if adx is not None:
            self.logger.info("ADX: {}".format(adx))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Average Directional Index (ADX) calculation finished in {:0.4f} seconds".format(elapsed_time))
        return adx

    def decide_signal(self, **data):
        # Retrieve the ADX series passed by main.py under the "calculations" key
        adx_series = data.get("calculations") 
        
        # Check if adx_series is None or not long enough
        if adx_series is None or len(adx_series) < 2:
            self.logger.error("Missing required ADX calculation data or data too short. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        self.logger.info("Deciding ADX buy/sell/hold signal...")
        last_adx = adx_series[-1]
        prev_adx = adx_series[-2] # Store previous ADX value for clarity

        if last_adx > 25:
            # Condition for BUY: ADX crosses above 25
            if prev_adx < 25:
                signal = Constants.BUY_SIGNAL
            # Condition for HOLD (when ADX is above 25 and still rising)
            elif prev_adx < last_adx: 
                signal = Constants.HOLD_SIGNAL
            # Condition for SELL (when ADX is above 25 but starts falling)
            else:
                signal = Constants.SELL_SIGNAL
        else:
            # If ADX is below 25, it's considered a weak or non-trending market
            signal = Constants.HOLD_SIGNAL

        self.logger.info(f"Signal detected: {signal}")
        return signal

        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Average Directional Index (ADX) to determine buy or sell signals")
    parser.add_argument('-H', '--high_prices', type=str,
                        help='Comma-separated list of highest prices',
                        required=False)
    parser.add_argument('-L', '--low_prices', type=str,
                        help='Comma-separated list of lowest prices',
                        required=False)
    parser.add_argument('-C', '--close_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    parser.add_argument("--timeperiod", type=int, default=14,
                        help="Time period")
    args = parser.parse_args()

    if args.use_mock:
        high_prices = [random.uniform(100, 200) for _ in range(100)]
        low_prices = [random.uniform(50, 100) for _ in range(100)]
        close_prices = [random.uniform(75, 125) for _ in range(100)]
    else:
        if not args.high_prices or not args.low_prices or not args.close_prices:
            raise ValueError("Missing required arguments: high_prices, low_prices, close_prices")

        high_prices = [float(price) for price in args.high_prices.split(',')]
        low_prices = [float(price) for price in args.low_prices.split(',')]
        close_prices = [float(price) for price in args.close_prices.split(',')]
    
    adx_api = ADX(args.timeperiod)
    data = adx_api.calculate(high_prices=high_prices, low_prices=low_prices, closing_prices=close_prices)
    adx_api.decide_signal(adx=data)