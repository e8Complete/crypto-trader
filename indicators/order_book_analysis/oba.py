#!/usr/bin/env python3.5

import os
import argparse
import time
from binance.client import Client
from utilities.constants import Constants
from utilities.utils import get_timestamp
from utilities.logger import setup_logger


class OBA:
    def __init__(self, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))

    def decide_buy_sell_hold_signals(self, order_book):
        start_time = time.perf_counter()
        self.logger.info("Deciding Order Book Analysis buy/sell/hold signal...")
        
        bids = order_book['bids']
        asks = order_book['asks']
        bid_sum = sum([float(bid[1]) for bid in bids])
        self.logger.info("Bid Sum: {}".format(bid_sum))
        ask_sum = sum([float(ask[1]) for ask in asks])
        self.logger.info("Ask Sum: {}".format(ask_sum))

        if bid_sum > ask_sum:
            signal = Constants.BUY_SIGNAL
        elif ask_sum > bid_sum:
            signal = Constants.SELL_SIGNAL
        else:
            signal = Constants.HOLD_SIGNAL
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Performed Order Book Analysis in {:0.4f} seconds".format(elapsed_time))
        
        self.logger.info("Signal detected: {}".format(signal))

        return signal 


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Order Book Analysis to determine buy or sell signals")
    parser.add_argument('-s', '--symbol', type=str, default='BTCUSDT',
                        help='Symbol to fetch order book for',
                        required=True)
    parser.add_argument("--depth", type=int, default=Constants.DEFAULT_ORDERBOOK_DEPTH,
                        help="Setting the depth to a higher number will include more price levels in the order book data, providing a more detailed view of the market. However, it can also increase the amount of data that needs to be processed, which may affect the performance of your script or application.")
    args = parser.parse_args()

    order_book = Client().get_order_book(symbol=args.symbol, limit=args.depth)
    oba_api = OBA()
    signal = oba_api.decide_buy_sell_hold_signals(order_book)