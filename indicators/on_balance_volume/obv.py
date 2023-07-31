#!/usr/bin/env python3.5

import os
import argparse
import time
import random
import pandas as pd
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class OBV(BaseIndicator):
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
        start_time = time.perf_counter()
        self.logger.info("Calculating On-Balance Volume (OBV)...")

        closing_prices = data.get("closing_prices", [])
        volume = data.get("volume", [])

        df = pd.DataFrame({
            'close': closing_prices,
            'volume': volume
        })

        df['obv'] = 0
        df.loc[df['close'] > df['close'].shift(1), 'obv'] = df['volume']
        df.loc[df['close'] < df['close'].shift(1), 'obv'] = -df['volume']
        df['obv'] = df['obv'].cumsum()
        self.logger.info(f"On-Balance Volume:\n{df['obv']}")
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Calculated On-Balance Volume (OBV) in {:0.4f} seconds".format(elapsed_time))
       
        return df['obv']
    
    def decide_signal(self, **data):
        obv = data.get("OBV", {}).get("calculations", [])
        if obv.empty:
            self.logger.error("Missing required data. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

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
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('-V', '--volume', type=str,
                        help='Comma-separated list of volumes',
                        required=False)
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    args = parser.parse_args()

    if args.use_mock:
        closing_prices = [random.uniform(100, 200) for _ in range(100)]
        volume = [random.randint(1000, 5000) for _ in range(100)]
    else:
        if not args.closing_prices or not args.volume:
            raise ValueError("Missing required arguments: closing_prices, volume")
        closing_prices = [float(price) for price in args.closing_prices.split(',')]
        volume = [float(vol) for vol in args.volume.split(',')]

    obv_api = OBV()
    obv = obv_api.calculate(closing_prices=closing_prices, volume=volume)
    signal = obv_api.decide_signal(OBV={"calculations": obv})