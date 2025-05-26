#!/usr/bin/env python3.5

import os
import argparse
import time
import random
from binance.client import Client
from indicators.base_indicator import BaseIndicator
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger
import matplotlib.pyplot as plt # Added for plotting
# import pandas as pd # Not strictly needed for this indicator as it works with dicts/lists


class OBA(BaseIndicator):
    def __init__(self, is_test=True,
                 timestamp=get_timestamp(precision="day", separator="-")):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        self.logger.info("Initialized OBA (Order Book Analysis) indicator.")

    def calculate(self, **data):
        order_book = data.get("order_book") # In main.py, order_book is passed as data[sym]['order_book']
                                          # So this should be data.get("order_book_data") or similar if OBA is called like other indicators.
                                          # However, if OBA is a special case and main.py calls it with `calculate(order_book=self.data[sym]['order_book'])`, then this is fine.
                                          # For now, assuming the structure passed by main.py is directly `data={'order_book': actual_order_book_dict}`
                                          # Or that if process_indicators calls it, it passes the order book under the key 'order_book' within the **data dict.

        if not order_book or 'bids' not in order_book or 'asks' not in order_book or \
           not order_book['bids'] or not order_book['asks']: # Check if lists are empty
            self.logger.warning("Order book data is missing, incomplete, or bids/asks are empty. Skipping OBA calculation.")
            return {"bid_sum": 0, "ask_sum": 0, "bid_ask_spread": None, "bid_ask_ratio": None, "top_bids": [], "top_asks": []}

        start_time = time.perf_counter()
        self.logger.info(f"Calculating Order Book Analysis for {len(order_book['bids'])} bid levels and {len(order_book['asks'])} ask levels...")

        bids = order_book['bids'] # List of [price_str, quantity_str]
        asks = order_book['asks']

        # Convert to float and sum quantities
        try:
            bid_quantities = [float(bid[1]) for bid in bids]
            ask_quantities = [float(ask[1]) for ask in asks]
            bid_sum = sum(bid_quantities)
            ask_sum = sum(ask_quantities)

            # Best bid (highest price bid) and best ask (lowest price ask)
            best_bid_price = float(bids[0][0])
            best_ask_price = float(asks[0][0])
            spread = best_ask_price - best_bid_price # Can be negative if order book crossed, though unlikely in snapshots
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error converting order book data to float: {e}. Bids: {bids[:3]}, Asks: {asks[:3]}")
            return {"bid_sum": 0, "ask_sum": 0, "bid_ask_spread": None, "bid_ask_ratio": None, "top_bids": [], "top_asks": []}


        ratio = bid_sum / ask_sum if ask_sum > 0 else (bid_sum if bid_sum > 0 else None) # Avoid division by zero

        self.logger.info(f"Total Bid Volume: {bid_sum:.2f}, Total Ask Volume: {ask_sum:.2f}")
        self.logger.info(f"Best Bid: {best_bid_price:.2f}, Best Ask: {best_ask_price:.2f}, Spread: {spread:.2f}")
        self.logger.info(f"Bid/Ask Ratio (Volume): {ratio if ratio is not None else 'N/A':.2f}")
        
        elapsed_time = time.perf_counter() - start_time
        self.logger.info(f"Order Book Analysis calculation finished in {elapsed_time:.4f} seconds.")

        return {
            "bid_sum": bid_sum, "ask_sum": ask_sum, 
            "bid_ask_spread": spread, "bid_ask_ratio": ratio,
            "top_bids": bids[:3], # Store price and quantity strings
            "top_asks": asks[:3]
        }

    def decide_signal(self, **cv_data): # cv_data is the output from calculate()
        # Note: main.py process_indicators stores the output of calculate() under the 'calculations' key.
        # So, if called by process_indicators, cv_data here will be {'calculations': result_of_calculate_method}
        # If OBA is a special case and not called via process_indicators standard loop, then cv_data might be the direct dict.
        # Assuming for now it's called like other indicators from process_indicators.
        
        # Therefore, we need to extract from 'calculations' key if it exists, otherwise assume cv_data is the direct data.
        actual_calculations = cv_data.get("calculations")
        if actual_calculations is None: # Fallback if 'calculations' key is not found (e.g. direct call or different structure)
            actual_calculations = cv_data 

        bid_sum = actual_calculations.get("bid_sum")
        ask_sum = actual_calculations.get("ask_sum")

        if bid_sum is None or ask_sum is None:
            self.logger.error("Missing OBA calculation data (bid_sum or ask_sum). Cannot decide signal.")
            return Constants.UNKNOWN_SIGNAL

        self.logger.info(f"Making OBA signal decision based on: Bid Sum={bid_sum:.2f}, Ask Sum={ask_sum:.2f}")
        
        signal = Constants.HOLD_SIGNAL
        if bid_sum > ask_sum: # More demand
            signal = Constants.BUY_SIGNAL
        elif ask_sum > bid_sum: # More supply
            signal = Constants.SELL_SIGNAL
        
        self.logger.info(f"OBA Signal detected: {signal}")
        return signal

    def plot(self, calculated_data, prices_df, output_path_prefix):
        """
        Plots the total bid and ask volumes from the order book analysis.
        calculated_data: Dict from calculate() -> e.g., {"bid_sum": ..., "ask_sum": ...}.
        prices_df: Pandas DataFrame (not directly used for this plot but part of std signature).
        output_path_prefix: Prefix for the output plot file name.
        """
        try:
            # Assuming calculated_data is the direct output of self.calculate()
            # If called from a context where it's nested under 'calculations', need to adjust:
            actual_plot_data = calculated_data.get("calculations") if "calculations" in calculated_data and isinstance(calculated_data.get("calculations"), dict) else calculated_data

            bid_sum = actual_plot_data.get("bid_sum")
            ask_sum = actual_plot_data.get("ask_sum")
            bid_ask_ratio = actual_plot_data.get("bid_ask_ratio")
            bid_ask_spread = actual_plot_data.get("bid_ask_spread")

            if bid_sum is None or ask_sum is None:
                self.logger.warning("OBA data (bid_sum/ask_sum) is None, skipping plot.")
                return

            fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
            
            categories = ['Total Bid Volume', 'Total Ask Volume']
            values = [bid_sum, ask_sum]
            colors = ['green', 'red']

            ax.bar(categories, values, color=colors)
            
            title = f'Order Book Analysis - Bid/Ask Volume Summary'
            if bid_ask_ratio is not None:
                title += f'\nRatio (Bid/Ask): {bid_ask_ratio:.2f}'
            if bid_ask_spread is not None:
                title += f' | Spread: {bid_ask_spread:.2f}' 
            
            ax.set_title(title)
            ax.set_ylabel('Total Volume')
            
            # Add text labels for values on bars
            for i, v in enumerate(values):
                ax.text(i, v + 0.01 * max(values), f"{v:.2f}", ha='center', va='bottom')

            plot_filename = f"{output_path_prefix}oba_summary_plot.png"
            plt.tight_layout()
            plt.savefig(plot_filename)
            plt.close(fig)
            self.logger.info(f"OBA plot saved to {plot_filename}")

        except Exception as e:
            self.logger.error(f"Error generating OBA plot: {e}", exc_info=True)
            if 'fig' in locals() and fig is not None:
                plt.close(fig)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use Order Book Analysis to determine buy or sell signals")
    parser.add_argument('-s', '--symbol', type=str, default='BTCUSDT',
                        help='Symbol to fetch order book for',
                        required=False)
    parser.add_argument("--depth", type=int, default=Constants.DEFAULT_ORDERBOOK_DEPTH,
                        help="Setting the depth to a higher number will include more price levels in the order book data, providing a more detailed view of the market. However, it can also increase the amount of data that needs to be processed, which may affect the performance of your script or application.")
    parser.add_argument('--use_mock', action='store_true', default=False,
                        help='Add this argument to run mock example',
                        required=False)
    args = parser.parse_args()

    if args.use_mock:
        order_book = {'bids': [[i, random.uniform(1, 10)] for i in range(10)],
                      'asks': [[i, random.uniform(1, 10)] for i in range(10)]}
    else:
        if not args.symbol:
            raise ValueError("Missing required argument: symbol")
        order_book = Client().get_order_book(symbol=args.symbol, limit=args.depth)

    oba_api = OBA()
    signal = oba_api.decide_signal(order_book=order_book)