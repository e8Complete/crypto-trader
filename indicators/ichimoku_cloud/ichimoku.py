#!/usr/bin/env python3.5

import os
import argparse
import time
import ta
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class IchimokuCloud:
    def __init__(self, tenkan_sen_n1=9, tenkan_sen_n2=26, kijun_sen_n2=26,
                 senkou_span_b_n2=52, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.tenkan_sen_n1 = tenkan_sen_n1
        self.tenkan_sen_n2 = tenkan_sen_n2
        self.kijun_sen_n2 = kijun_sen_n2
        self.senkou_span_b_n2 = senkou_span_b_n2

    def calculate_ichimoku_values(self, high_prices, low_prices):
        start_time = time.perf_counter()
        self.logger.info("Calculating Ichimoku Cloud Values...")
        self.logger.info("High prices: {}".format(", ".join(high_prices)))
        self.logger.info("Low prices: {}".format(", ".join(low_prices)))
        self.logger.info("tenkan_sen_n1: {}".format(self.tenkan_sen_n1))
        self.logger.info("tenkan_sen_n2: {}".format(self.tenkan_sen_n2))
        self.logger.info("kijun_sen_n2: {}".format(self.kijun_sen_n2))
        self.logger.info("senkou_span_b_n2: {}".format(self.senkou_span_b_n2))

        tenkan_sen = ta.trend.ichimoku_a(high=high_prices, low=low_prices,
                                    n1=self.tenkan_sen_n1, n2=self.tenkan_sen_n2)
        self.logger.info("tenkan_sen: {}".format(tenkan_sen))
        kijun_sen = ta.trend.ichimoku_b(high=high_prices, low=low_prices,
                                                            n2=self.kijun_sen_n2)
        self.logger.info("kijun_sen: {}".format(kijun_sen))
        senkou_span_a = (tenkan_sen + kijun_sen) / 2
        self.logger.info("senkou_span_a: {}".format(senkou_span_a))
        senkou_span_b = ta.trend.ichimoku_b(high=high_prices, low=low_prices,
                                                        n2=self.senkou_span_b_n2)
        self.logger.info("senkou_span_b: {}".format(senkou_span_b))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Calculated Ichimoku Cloud Values in {:0.4f} seconds".format(elapsed_time))

        return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b

    def decide_buy_sell_hold_signals(self, senkou_span_a, senkou_span_b, current_price):
        self.logger.info("Deciding Ichimoku Cloud buy/sell/hold signal...")
        if current_price > senkou_span_a[-1] and current_price > senkou_span_b[-1]:
            signal = Constants.BUY_SIGNAL
        elif current_price < senkou_span_a[-1] and current_price < senkou_span_b[-1]:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Ichimoku Cloud to determine buy or sell signals")
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

    ichimoku_api = IchimokuCloud()
    (tenkan_sen,
     kijun_sen,
     senkou_span_a,
     senkou_span_b) = ichimoku_api.calculate_ichimoku_values(high_prices, low_prices)
    signal = ichimoku_api.decide_buy_sell_hold_signals(senkou_span_a, senkou_span_b, current_price)

