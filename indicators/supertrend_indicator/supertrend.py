#!/usr/bin/env python3.5

import os
import argparse
import time
import random
import talib
import pandas as pd
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class Supertrend(BaseIndicator):
    def __init__(self, lookback=10, multiplier=3, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.lookback = lookback
        self.multiplier = multiplier

    def supertrend(self, high_prices, low_prices, closing_prices, period, multiplier):
        df = pd.DataFrame({
            'high': high_prices,
            'low': low_prices,
            'close': closing_prices
        })

        hl2 = (df['high'] + df['low']) / 2
        df['atr'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=period)
        
        df['upper_band'] = hl2 + multiplier * df['atr']
        df['lower_band'] = hl2 - multiplier * df['atr']
        
        df['in_uptrend'] = True
        
        for current in range(1, len(df.index)):
            previous = current - 1
            
            if df['close'][current] > df['upper_band'][previous]:
                df['in_uptrend'][current] = True
            elif df['close'][current] < df['lower_band'][previous]:
                df['in_uptrend'][current] = False
            else:
                df.loc[current, 'in_uptrend'] = df.loc[previous, 'in_uptrend']
                
                if df['in_uptrend'][current] and df['lower_band'][current] < df['lower_band'][previous]:
                    df.loc[current, 'lower_band'] = df.loc[previous, 'lower_band']
                    
                if not df['in_uptrend'][current] and df['upper_band'][current] > df['upper_band'][previous]:
                    df['upper_band'][current] = df['upper_band'][previous]
                    
        return df

    def calculate(self, **data):
        start_time = time.perf_counter()
        high_prices = data.get("high_prices", [])
        low_prices = data.get("low_prices", [])
        closing_prices = data.get("closing_prices", [])
        self.logger.info("Determining Supertrend...")
        self.logger.info("Multiplier: {}".format(self.multiplier))
        self.logger.info("Lookback: {}".format(self.lookback))
        self.logger.info("Multiplier: {}".format(self.multiplier))

        st = self.supertrend(high_prices, low_prices, closing_prices, self.lookback, self.multiplier)
        self.logger.info("Supertrend:\n{}".format(st))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Determined Supertrend Indicator in {:0.4f} seconds".format(elapsed_time))
        
        return st

    def decide_signal(self, **data):
        st = data.get("Supertrend", {}).get("calculations", pd.DataFrame())
        closing_prices = data.get("closing_prices", [])
        if st.empty or not closing_prices:
            self.logger.error("Missing required data. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        self.logger.info("Deciding Supertrend Indicator buy/sell/hold signal...")        
        prev_st = st.shift(1)
        self.logger.info("Previous Supertrend:\n{}".format(prev_st))
        if closing_prices[-1] > st['upper_band'].iloc[-1] and prev_st['upper_band'].iloc[-1] <= closing_prices[-2]:
            signal = Constants.BUY_SIGNAL
        elif closing_prices[-1] < st['lower_band'].iloc[-1] and prev_st['lower_band'].iloc[-1] >= closing_prices[-2]:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Supertrend Indicator to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices', type=str,
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('-H', '--high_prices', type=str,
                        help='Comma-separated list of highest prices',
                        required=False)
    parser.add_argument('-L', '--low_prices', type=str,
                        help='Comma-separated list of lowest prices',
                        required=False)
    parser.add_argument("--lookback", type=int, default=10,
                        help="Lookback window for the Supertrend indicator. It is the number of periods used to calculate the average true range (ATR) that is used in the Supertrend calculation.")
    parser.add_argument('--multiplier', type=int, default=3,
                        help='Multiplier factor for the Supertrend indicator. It is the factor by which the ATR is multiplied to calculate the upper and lower bands of the Supertrend line.')
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    args = parser.parse_args()

    if args.use_mock:
        high_prices = [random.uniform(100, 200) for _ in range(100)]
        low_prices = [random.uniform(100, 200) for _ in range(100)]
        closing_prices = [random.uniform(100, 200) for _ in range(100)]
    else:
        if not args.high_prices or not args.low_prices or not args.closing_prices:
            raise ValueError("Missing required arguments: high_prices, low_prices, closing_prices")
        high_prices = [float(price) for price in args.high_prices.split(',')]
        low_prices = [float(price) for price in args.low_prices.split(',')]
        closing_prices = [float(price) for price in args.closing_prices.split(',')]

    st_api = Supertrend(lookback=args.lookback, multiplier=args.multiplier)
    st = st_api.calculate(high_prices=high_prices, low_prices=low_prices, closing_prices=closing_prices)
    signal = st_api.decide_signal(Supertrend={"calculations": st}, closing_prices=closing_prices)