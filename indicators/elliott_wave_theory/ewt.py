#!/usr/bin/env python3.5

import os
import argparse
import time
import numpy as np
import talib
from utilities.constants import Constants
from utilities.utils import get_timestamp
from utilities.logger import setup_logger


class EWT:
    def __init__(self, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))

    def identify_wave_patterns(self, closing_prices):
        start_time = time.perf_counter()
        self.logger.info("Caclulating Elliott Wave Theory Values...")
        self.logger.info("Closing prices: {}".format(", ".join(closing_prices)))

        self.logger.info("Identifying Elliott waves...")
        waves = []
        for i in range(1, len(closing_prices)):
            if closing_prices[i] > closing_prices[i-1]:
                waves.append(1)
            elif closing_prices[i] < closing_prices[i-1]:
                waves.append(-1)
            else:
                waves.append(0)
        self.logger.info("Elliott waves: {}".format(", ".join(waves)))

        self.logger.info("Identifying Elliott wave patterns...")
        if waves[-2:] == [1, -1]:
            ew_pattern = 1
        elif waves[-2:] == [-1, 1]:
            ew_pattern = -1
        self.logger.info("Elliott wave patterns: {}".format(ew_pattern))
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Elliott wave pattern calculation finished in {:0.4f} seconds".format(elapsed_time))

        return ew_pattern
    
    def get_moving_average(self, closing_prices, timeperiod):
        start_time = time.perf_counter()
        self.logger.info("Calculating moving average...")
        self.logger.info("Timeperiod: {}".format(timeperiod))
        self.logger.info("Closing prices: {}".format(", ".join(closing_prices)))

        sma = talib.SMA(np.array(closing_prices), timeperiod=timeperiod)
        self.logger.info("Moving Average: {}".format(sma))
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Calulated Moving Average in {:0.4f} seconds".format(elapsed_time))

        return sma

    def decide_buy_sell_hold_signals(self, closing_prices, ew_pattern, rsi, sma1, sma2):
        self.logger.info("Deciding Elliott Wave Theory buy/sell/hold signal...")
        if ew_pattern == 1 and rsi[-1] < 30 and closing_prices[-1] > sma1[-1] and closing_prices[-1] > sma2[-1]:
            signal = Constants.BUY_SIGNAL
        elif ew_pattern == -1 and rsi[-1] > 70 and closing_prices[-1] < sma1[-1] and closing_prices[-1] < sma2[-1]:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Elliott Wave Theory to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices',
                        help='Closing price',
                        required=True)
    parser.add_argument('-n', '--period_length', type=int, default=Constants.DEFAULT_PERIOD_LENGTH,
                        help='Length of period. Defaults to {} if not provided.'.format(Constants.DEFAULT_PERIOD_LENGTH),
                        required=False)
    parser.add_argument('-t1', '--timeperiod1', type=int, default=20,
                        help="Time period for moving avarage 1")
    parser.add_argument('-t2', '--timeperiod2', type=int, default=50,
                        help='Time period for moving avarage 2')
    args = parser.parse_args()

    # Fetch RSI
    from indicators.relative_strength_index.rsi import RSI
    rsi_api = RSI()
    rsi = rsi_api.calculate_rsi(args.closing_prices, args.period_length)
    
    # Decide EWT signal
    ewt_api = EWT()
    ewt_pattern = ewt_api.identify_wave_patterns(args.closing_prices)
    sma1 = ewt_api.get_moving_average(args.timeperiod1)
    sma2 = ewt_api.get_moving_average(args.timeperiod2)
    signal = ewt_api.decide_buy_sell_hold_signals(args.closing_prices, ewt_pattern, rsi, sma1, sma2)