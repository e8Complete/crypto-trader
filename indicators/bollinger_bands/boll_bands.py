#!/usr/bin/env python3.5

import os
import argparse
import time
import numpy as np
import random
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class BollingerBands(BaseIndicator):
    def __init__(self,  window_size=20, num_std=2, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
import talib # Ensure talib is imported

class BollingerBands(BaseIndicator):
    def __init__(self,  window_size=20, num_std=2, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.window_size = window_size
        self.num_std = num_std

    def calculate(self, **data):
        closing_prices = data.get('closing_prices')
        if closing_prices is None:
            self.logger.error("Closing prices are missing.")
            return {"upper_band": None, "middle_band": None, "lower_band": None}

        np_closing_prices = np.array(closing_prices)
        if len(np_closing_prices) < self.window_size:
            self.logger.warning("Not enough data points to calculate Bollinger Bands accurately for window size {}. Data length: {}".format(self.window_size, len(np_closing_prices)))
            return {"upper_band": None, "middle_band": None, "lower_band": None} 

        start_time = time.perf_counter()
        self.logger.info("Calculating Bollinger Bands using TA-Lib...")
        self.logger.info("Window size: {}".format(self.window_size))
        self.logger.info("Number of STD: {}".format(self.num_std))

        try:
            upper, middle, lower = talib.BBANDS(np_closing_prices, 
                                                timeperiod=self.window_size,
                                                nbdevup=self.num_std,
                                                nbdevdn=self.num_std,
                                                matype=0) # Using SMA as default
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands with TA-Lib: {e}")
            return {"upper_band": None, "middle_band": None, "lower_band": None}

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Bollinger Bands TA-Lib calculation finished in {:0.4f} seconds".format(elapsed_time))

        return {"upper_band": upper, "middle_band": middle, "lower_band": lower}

    def decide_signal(self, current_closing_price=None, **cv_data): # cv_data is the output from calculate()
        if current_closing_price is None:
            self.logger.error("Current closing price not provided. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        upper_band_series = cv_data.get('upper_band')
        # middle_band_series = cv_data.get('middle_band') # Fetched but not used in original logic
        lower_band_series = cv_data.get('lower_band')

        if upper_band_series is None or lower_band_series is None or \
           len(upper_band_series) == 0 or len(lower_band_series) == 0:
            self.logger.error("Bollinger Bands data is missing or empty. Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        # Get the latest band values
        latest_upper_band = upper_band_series[-1]
        latest_lower_band = lower_band_series[-1]
           
        # Check for NaN values which can occur at the beginning of TA-Lib results
        if np.isnan(latest_upper_band) or np.isnan(latest_lower_band):
            self.logger.warning("Latest Bollinger Band values are NaN (insufficient data for period). Holding.")
            return Constants.HOLD_SIGNAL

        signal = Constants.HOLD_SIGNAL # Default to hold
        if current_closing_price < latest_lower_band:
            self.logger.info(f"Possible buy signal. Last price: {current_closing_price}, Lower band: {latest_lower_band}")
            signal = Constants.BUY_SIGNAL
        elif current_closing_price > latest_upper_band:
            self.logger.info(f"Possible sell signal. Last price: {current_closing_price}, Upper band: {latest_upper_band}")
            signal = Constants.SELL_SIGNAL
        else:
            self.logger.info(f"Possible hold signal. Last price: {current_closing_price} is between bands {latest_lower_band} and {latest_upper_band}.")
            
        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Bollinger Bands to determine buy or sell signals")
    parser.add_argument('-C', '--closing_prices_str', type=str,  # Renamed to avoid conflict with internal var name
                        help='Comma-separated list of closing prices',
                        required=False)
    parser.add_argument('-w', '--window_size', type=int, default=20,
                        help='Window size')
    parser.add_argument('-n', '--num_std', type=float, default=2,
                        help='Num std')
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example')
    args = parser.parse_args()

    closing_prices_data = [] # Initialize with an empty list

    if args.use_mock:
        base_price = 100
        # Generate more realistic mock data for BBands
        closing_prices_data = [base_price + random.uniform(-5, 5) for _ in range(100)]
        for i in range(1, len(closing_prices_data)):
            movement = random.uniform(-2, 2)
            closing_prices_data[i] = max(10, closing_prices_data[i-1] + movement) # Ensure prices stay positive
    else:
        if not args.closing_prices_str:
            raise ValueError("Missing required argument: --closing_prices_str")
        closing_prices_data = [float(price) for price in args.closing_prices_str.split(',')]

    bb_api = BollingerBands(window_size=args.window_size, num_std=args.num_std)
    
    # Calculate Bollinger Bands
    # The 'calculate' method expects a dictionary with 'closing_prices' key
    calculated_data = bb_api.calculate(closing_prices=closing_prices_data) 
    
    # Decide signal
    # The 'decide_signal' method expects current_closing_price and the output of calculate (cv_data)
    if closing_prices_data and calculated_data.get("upper_band") is not None : # Ensure there's data to decide upon
        current_price_for_signal = closing_prices_data[-1]
        signal = bb_api.decide_signal(current_closing_price=current_price_for_signal, **calculated_data)
        print(f"Calculated Bands (last 5 values):")
        if calculated_data["upper_band"] is not None:
             print(f"Upper: {calculated_data['upper_band'][-5:]}")
        if calculated_data["middle_band"] is not None:
            print(f"Middle: {calculated_data['middle_band'][-5:]}")
        if calculated_data["lower_band"] is not None:
            print(f"Lower: {calculated_data['lower_band'][-5:]}")
        print(f"Current Price: {current_price_for_signal}")
        print(f"Signal: {signal}")
    else:
        print("Could not generate signal due to insufficient data or calculation error.")
