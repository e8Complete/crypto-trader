#!/usr/bin/env python3.5

import os
import argparse
import time
from pytrends.request import TrendReq
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class GoogleTrends:
    def __init__(self, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.api = TrendReq()

    def fetch_google_trends(self, topic, start_date, end_date):
        start_time = time.perf_counter()
        
        # TODO: add args for start_date and end_date
        start_date = '2017-01-01'
        end_date = '2022-01-01'
        self.api.build_payload(kw_list=[topic], timeframe=f'{start_date} {end_date}')
        trends_data = self.api.interest_over_time()

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Fetched {} {} Google Trends  in {:0.4f} seconds".format(count, topic, elapsed_time))

        return trends_data

    def decide_buy_sell_hold_signals(self, topic, trends_data):
        self.logger.info("Deciding Google Trends buy/sell/hold signal for {}...".format(topic))

        current_value = trends_data[topic][-1]
        historical_average = trends_data[topic].mean()

        if current_value > historical_average:
            signal = Constants.BUY_SIGNAL
        elif current_value < historical_average:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL

        self.logger.info("Signal detected: {}".format(signal))
        return signal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch public Tweets and perform sentiment analysis on them")
    parser.add_argument('-t', '--topic', type=str, default="Bitcoin",
                        help='Topic to fetch tweets from',
                        required=True)
    args = parser.parse_args()

    google_trends_api = GoogleTrends(args)
    trends_data = google_trends_api.fetch_google_trends(args.topic, args.start_date, args.end_date)
    signal = google_trends_api.decide_buy_sell_hold_signals(args.topic, trends_data)