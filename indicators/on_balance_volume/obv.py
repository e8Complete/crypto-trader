#!/usr/bin/env python3.5

import os
import argparse
import time
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class OBV:
    def __init__(self, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))

    def calculate_obv(self, df):
        start_time = time.perf_counter()
        self.logger.info("Calculating On-Balance Volume (OBV)...")

        df['obv'] = 0
        df.loc[df['close'] > df['close'].shift(1), 'obv'] = df['taker_buy_base_asset_volume']
        df.loc[df['close'] < df['close'].shift(1), 'obv'] = -df['taker_buy_base_asset_volume']
        df['obv'] = df['obv'].cumsum()

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Calculated On-Balance Volume (OBV) in {:0.4f} seconds".format(elapsed_time))
       
        return df['obv']
    
    def decide_buy_sell_hold_signals(self, obv):
        self.logger.info("Deciding OBV buy/sell/hold signal...")
        if obv.iloc[-1] > obv.iloc[-2]:
            signal = Constants.BUY_SIGNAL
        elif obv.iloc[-1] < obv.iloc[-2]:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use On-Balance Volume (OBV) to determine buy or sell signals")
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

    obv_api = OBV()
    obv = obv_api.calculate_obv()
    signal = obv_api.decide_buy_sell_hold_signals(obv)