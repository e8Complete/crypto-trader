#!/usr/bin/env python3.5

import os
import argparse
import time
import numpy as np
import talib
import random
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class EWT(BaseIndicator):
    def __init__(self, timeperiod1=20, timeperiod2=50, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.timeperiod1 = timeperiod1
        self.timeperiod2 = timeperiod2

    def calculate(self, **data):
        closing_prices = data.get('closing_prices', '')
        start_time = time.perf_counter()
        self.logger.info("Calculating Elliott Wave Theory Values...")
        self.logger.info("Closing prices: {}".format(", ".join(map(str, closing_prices))))

        self.logger.info("Identifying Elliott waves...")
        waves = []
        for i in range(1, len(closing_prices)):
            if closing_prices[i] > closing_prices[i-1]:
                waves.append(1)
            elif closing_prices[i] < closing_prices[i-1]:
                waves.append(-1)
            else:
                waves.append(0)
        self.logger.info("Elliott waves: {}".format(", ".join(map(str, waves))))

        self.logger.info("Identifying Elliott wave patterns...")
        if waves[-2:] == [1, -1]:
            ew_pattern = 1
        elif waves[-2:] == [-1, 1]:
            ew_pattern = -1
        else:
            ew_pattern = 0
        self.logger.info("Elliott wave patterns: {}".format(ew_pattern))
        
        sma1 = talib.SMA(np.array(closing_prices), timeperiod=self.timeperiod1)
        sma2 = talib.SMA(np.array(closing_prices), timeperiod=self.timeperiod2)
        
        result = {
            "ew_pattern": ew_pattern,
            "sma1": sma1,
            "sma2": sma2
        }

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Elliott wave pattern calculation finished in {:0.4f} seconds".format(elapsed_time))

        return result

    def decide_signal(self, **data):
        closing_prices = data.get('closing_prices', '')
        rsi = data.get('RSI', {}).get("calculations", "")
        ew_pattern = data.get('ew_pattern', '')
        sma1 = data.get('sma1', '')
        sma2 = data.get('sma2', '')
        if (not closing_prices or rsi is None or len(rsi) < 2 or not ew_pattern
            or sma1 is None or sma2 is None):
            self.logger.error("Missing required data. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL
    
        self.logger.info("Deciding Elliott Wave Theory buy/sell/hold signal...")
        last_closing = closing_prices[-1]
        last_rsi = rsi[-1]
        last_sma1 = sma1[-1]
        last_sma2 = sma2[-1]
        self.logger.info(f"Last closing price: {last_closing}")
        self.logger.info(f"Last RSI: {last_rsi}")
        self.logger.info(f"Last last_sma1: {last_sma1}")
        self.logger.info(f"Last last_sma2: {last_sma2}")
        if ew_pattern == 1 and last_rsi < 30 and last_closing > last_sma1 and last_closing > last_sma2:
            signal = Constants.BUY_SIGNAL
        elif ew_pattern == -1 and last_rsi > 70 and last_closing < last_sma1 and last_closing < last_sma2:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Elliott Wave Theory to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    parser.add_argument('-n', '--period_length', type=int, default=Constants.DEFAULT_PERIOD_LENGTH,
                        help='Length of period. Defaults to {} if not provided.'.format(Constants.DEFAULT_PERIOD_LENGTH),
                        required=False)
    parser.add_argument('-t1', '--timeperiod1', type=int, default=20,
                        help="Time period for moving average 1")
    parser.add_argument('-t2', '--timeperiod2', type=int, default=50,
                        help='Time period for moving average 2')
    args = parser.parse_args()

    if args.use_mock:
        closing_prices = [random.uniform(100, 200) for _ in range(100)]
    else:
        if not args.closing_prices:
            raise ValueError("Missing required argument: closing_prices")
        closing_prices = [float(price) for price in args.closing_prices.split(',')]

    # Fetch RSI
    from indicators.relative_strength_index.rsi import RSI
    rsi_api = RSI(period_length=args.period_length)
    rsi = rsi_api.calculate(closing_prices=closing_prices)

    # Decide EWT signal
    ewt_api = EWT(timeperiod1=args.timeperiod1, timeperiod2=args.timeperiod2)
    ewt_data = ewt_api.calculate(closing_prices=closing_prices)
    signal = ewt_api.decide_signal(closing_prices=closing_prices,
                                   RSI={"calculations": rsi}, **ewt_data)
