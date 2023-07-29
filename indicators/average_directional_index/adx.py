#!/usr/bin/env python3.5

import os
import argparse
import time
import talib
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class ADX:
    def __init__(self, timeperiod=14, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.timeperiod = timeperiod

    def calculate_adx(self, high, low, close):
        start_time = time.perf_counter()
        self.logger.info("Calculating Average Directional Index (ADX)...")
        self.logger.info("Timeperiod: {}".format(self.timeperiod))

        adx = talib.ADX(high, low,close, timeperiod=self.timeperiod)
        self.logger.info("ADX: {}".format(adx))
 
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Average Directional Index (ADX) calculation finished in {:0.4f} seconds".format(elapsed_time))
 
        return adx
    
    def decide_buy_sell_hold_signals(self, adx):
        self.logger.info("Deciding ADX buy/sell/hold signal...")
        last_adx = adx.iloc[-1]
        if last_adx > 25:
            if adx[-2] < 25:
                signal = Constants.BUY_SIGNAL
            elif adx[-2] < last_adx:
                signal = Constants.HOLD_SIGNAL
            else:
                signal =  Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL

        self.logger.info("Signal detected: {}".format(signal))
        return signal
            
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Average Directional Index (ADX) to determine buy or sell signals")
    parser.add_argument('-H', '--high', type=float,
                        help='Highest price',
                        required=True)
    parser.add_argument('-L', '--low', type=float,
                        help='Lowest price',
                        required=True)
    parser.add_argument('-C', '--closing_price', type=float,
                        help='Closing price',
                        required=True)
    parser.add_argument("--timeperiod", type=int, default=14,
                        help="Time period")
    args = parser.parse_args()

    adx_api = ADX(args.timeperiod)
    adx = adx_api.calculate_adx(args.high, args.low, args.closing_price)
    signal = adx_api.decide_buy_sell_hold_signals(adx)