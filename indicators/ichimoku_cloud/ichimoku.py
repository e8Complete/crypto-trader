#!/usr/bin/env python3.5

import os
import argparse
import time
import ta
import random
import pandas as pd
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class IchimokuCloud(BaseIndicator):
    def __init__(self, tenkan_sen_n1=9, kijun_sen_n2=26,
                 senkou_span_b_n2=52, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.tenkan_sen_n1 = tenkan_sen_n1
        self.kijun_sen_n2 = kijun_sen_n2
        self.senkou_span_b_n2 = senkou_span_b_n2

    def calculate(self, **data):
        start_time = time.perf_counter()
        high_prices = pd.Series(data.get("high_prices", []))
        low_prices = pd.Series(data.get("low_prices", []))
        self.logger.info("Calculating Ichimoku Cloud Values...")
        tenkan_sen = (high_prices.rolling(window=self.tenkan_sen_n1).max() + 
                    low_prices.rolling(window=self.tenkan_sen_n1).min()) / 2
        kijun_sen = (high_prices.rolling(window=self.kijun_sen_n2).max() + 
                    low_prices.rolling(window=self.kijun_sen_n2).min()) / 2
        senkou_span_a = (tenkan_sen + kijun_sen) / 2
        senkou_span_b = (high_prices.rolling(window=self.senkou_span_b_n2).max() + 
                        low_prices.rolling(window=self.senkou_span_b_n2).min()) / 2
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info(f"tenkan_sen: {tenkan_sen}")
        self.logger.info(f"kijun_sen:\n{kijun_sen}")
        self.logger.info(f"senkou_span_a:\n{senkou_span_a}")
        self.logger.info(f"senkou_span_b:\n{senkou_span_b}")
        self.logger.info("Calculated Ichimoku Cloud Values in {:0.4f} seconds".format(elapsed_time))

        return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b

    def decide_signal(self, **data):
        current_price = data.get('current_price', '')
        calculations = data.get("IchimokuCloud", {}).get("calculations", [])
        if not calculations:
            self.logger.error("Missing required data. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL
        
        tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b = calculations
        if senkou_span_a.empty or senkou_span_b.empty:
            self.logger.error("Missing required data. Cannot decide signal.")
            signal = Constants.UNKNOWN_SIGNAL

        self.logger.info("Deciding Ichimoku Cloud buy/sell/hold signal...")
        if not senkou_span_a.empty and not senkou_span_b.empty:
            if current_price > max(senkou_span_a.iloc[-1], senkou_span_b.iloc[-1]):
                signal = Constants.BUY_SIGNAL
            elif current_price < min(senkou_span_a.iloc[-1], senkou_span_b.iloc[-1]):
                signal = Constants.SELL_SIGNAL
            else:
                signal = Constants.HOLD_SIGNAL

        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Ichimoku Cloud to determine buy or sell signals")
    parser.add_argument('-H', '--high_prices', type=str,
                        help='Comma-separated list of highest prices',
                        required=False)
    parser.add_argument('-L', '--low_prices', type=str,
                        help='Comma-separated list of lowest prices',
                        required=False)
    parser.add_argument('--tenkan_sen_n1', type=int, default=9,
                        help='Number of periods for Tenkan Sen calculation.')
    parser.add_argument('--kijun_sen_n2', type=int, default=26,
                        help='Number of periods for Kijun Sen calculation.')
    parser.add_argument('--senkou_span_b_n2', type=int, default=52,
                        help='Number of periods for Senkou Span B calculation.')
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    args = parser.parse_args()

    if args.use_mock:
        high_prices = [random.uniform(100, 200) for _ in range(100)]
        low_prices = [random.uniform(100, 200) for _ in range(100)]
        current_price = random.uniform(100, 200)
    else:
        if not args.high_prices or not args.low_prices:
            raise ValueError("Missing required arguments: high_prices, low_prices")
        high_prices = [float(price) for price in args.high_prices.split(',')]
        low_prices = [float(price) for price in args.low_prices.split(',')]
        current_price = high_prices[-1]  # Assuming the current price is the last high price

    ichimoku_api = IchimokuCloud(tenkan_sen_n1=args.tenkan_sen_n1, kijun_sen_n2=args.kijun_sen_n2,
                                 senkou_span_b_n2=args.senkou_span_b_n2)
    calculations = ichimoku_api.calculate(high_prices=high_prices, low_prices=low_prices)
    signal = ichimoku_api.decide_signal(IchimokuCloud={"calculations": calculations}, current_price=current_price)
