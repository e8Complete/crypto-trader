#!/usr/bin/env python3.5

import os
import sys
import time
import argparse
import pandas as pd
from multiprocessing import Pool, Manager
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from scripts.constants import Constants
from scripts.logger import setup_logger
from scripts.utils import get_timestamp, load_config, save_data_to_csv
from scripts.strategy_factory import StrategyFactory
from gpt.gpt import make_trade_decision
from gpt.bing import get_market_news


class TradingAPI(Client):     
    def __init__(self, config_path, timestamp=get_timestamp()):
        self.config = load_config(config_path)
        self.timestamp = timestamp
        self.logger = setup_logger(name=os.path.basename(os.path.dirname(os.path.realpath(__file__))),
                                   is_test=self.config['testnet'],
                                   timestamp=self.timestamp,
                                   )
        self.logger.info("Timestamp: {}".format(self.timestamp))
        self.logger.info("Testnet: {}".format(self.config["testnet"]))
        self.logger.info("Using symbols: {}".format(", ".join(self.config["symbols"])))
        self.logger.info("Kline interval: {}".format(self.config["kline_interval"]))
        self.logger.info("Kline start: {}".format(self.config["kline_start"]))
        self.data = {}
        self.logger.info("Initializing trading API...")
        try:
            self.client = Client(os.environ.get('BINANCE_KEY'),
                                 os.environ.get('BINANCE_SECRET'),
                                 testnet=self.config["testnet"])
        except (BinanceAPIException, BinanceRequestException) as e:
            self.logger.error(f"Failed to initialize Binance client: {e}")
            sys.exit(1)

        # Indicator APIs
        self.indicators = []
        for indicator_config in self.config["indicators"]:
            if indicator_config["enable"]:
                class_name = indicator_config["name"]
                params = indicator_config.get("parameters", {})
                instance = StrategyFactory.create_strategy(class_name, **params)
                self.indicators.append(instance)
        # Sentiment APIs
        self.sentiment_analyzers = []
        for sentiment_config in self.config["sentiment_analyzers"]:
            if sentiment_config["enable"]:
                class_name = sentiment_config["name"]
                params = sentiment_config.get("parameters", {})
                instance = StrategyFactory.create_strategy(class_name, **params)
                self.sentiment_analyzers.append(instance)

    def run(self):
        init_time = time.perf_counter()
        manager = Manager()
        self.data = manager.dict()
        self.logger.info("Fetching historical price data...")
        # Fetch data using multiprocessing
        fetch_results = {}
        with Pool() as pool:
            async_results = {sym: pool.apply_async(self.fetch_data, args=(sym,)) for sym in self.config["symbols"]}
            for sym, res in async_results.items():
                try:
                    fetch_results[sym] = res.get()  # Consider adding a timeout
                except Exception as e:
                    self.logger.error(f"Error fetching data for {sym} in parallel: {e}")
                    fetch_results[sym] = {}  # Store empty dict or error indicator
        self.data = manager.dict(fetch_results)

        self.logger.info("Processing data...")
        # Process data using multiprocessing
        # Keep a dictionary to store async results for processing tasks
        processing_async_results = {sym: {} for sym in self.config["symbols"]}

        with Pool() as pool:
            for sym in self.config["symbols"]:
                if sym not in self.data or not self.data[sym] or "klines" not in self.data[sym] or not self.data[sym]["klines"]:
                    self.logger.warning(f"Skipping processing for {sym} due to missing or incomplete data.")
                    continue

                # Sentiment analysis
                processing_async_results[sym]["sentiment"] = pool.apply_async(self.process_sentiment_analyzer, args=(sym,))
                # Indicator calculations
                # process_indicators expects the data for the symbol, so pass self.data[sym]
                processing_async_results[sym]["indicators"] = pool.apply_async(self.process_indicators, args=(self.data[sym],))
                # Bing's latest market news
                processing_async_results[sym]["market_news"] = pool.apply_async(get_market_news, args=(sym, self.logger))

            # Collect results from processing tasks
            for sym in self.config["symbols"]:
                if sym not in self.data or not self.data[sym] or "klines" not in self.data[sym] or not self.data[sym]["klines"]:
                    continue # Skip if initial data fetch failed or was incomplete

                try:
                    if "sentiment" in processing_async_results[sym]:
                        self.data[sym]["sentiment"] = processing_async_results[sym]["sentiment"].get()
                except Exception as e:
                    self.logger.error(f"Error processing sentiment for {sym}: {e}")
                    self.data[sym]["sentiment"] = {}

                try:
                    if "indicators" in processing_async_results[sym]:
                        self.data[sym]["indicators"] = processing_async_results[sym]["indicators"].get()
                except Exception as e:
                    self.logger.error(f"Error processing indicators for {sym}: {e}")
                    self.data[sym]["indicators"] = {}
                
                try:
                    if "market_news" in processing_async_results[sym]:
                        self.data[sym]["market_news"] = processing_async_results[sym]["market_news"].get()
                except Exception as e:
                    self.logger.error(f"Error fetching market news for {sym}: {e}")
                    self.data[sym]["market_news"] = Constants.STATUS_ERROR_FETCHING_NEWS


        # GPT trade decision and execution (sequential per symbol after parallel processing)
        for sym in self.config["symbols"]:
            if sym in self.data and self.data[sym] and "klines" in self.data[sym] and self.data[sym]["klines"]:
                # Ensure all necessary data components (like indicators, sentiment) are present before decision making
                # If any part failed, it might be an empty dict or an error string.
                # make_trade_decision should be robust enough to handle this or have checks here.
                self.data[sym]["decision"] = make_trade_decision(sym, self.data[sym])
                # Execute the trade based of decision
                if "decision" in self.data[sym] and self.data[sym]["decision"]:
                    # Pass the symbol and the decision data for that symbol
                    self.execute_trades(sym, self.data[sym]["decision"]) 
                else:
                    self.logger.info(f"No decision made for {sym}, skipping trade execution.")
            else:
                self.logger.info(f"Skipping trade decision and execution for {sym} due to missing prior data.")

        save_data_to_csv(self.data, self.config) # Pass self.config as the second argument

        app_shutdown = time.perf_counter()
        total_time = app_shutdown - init_time
        self.logger.info("Total time for app run: %.2f seconds" % total_time)
    
    def fetch_data(self, sym):
        data = {}
        self.logger.info("Loading % price data..." % sym)
        try:
            bars = self.client.get_historical_klines(sym, self.config["kline_interval"],
                                                        self.config["kline_start"])
            data["klines"] = bars
        except Exception as e:
            self.logger.error("Failed to fetch data for '%s'. Skipping. Error: %s", sym, str(e))
            return data # Return immediately if fetching klines failed

        # Check if klines were fetched successfully
        if "klines" not in data or not data["klines"]:
            self.logger.warning(f"No klines data fetched for {sym}. Skipping further processing in fetch_data.")
            return data

        df = self.convert_to_dataframe(data["klines"]) # Use local 'data' variable
        start_index = 0
        # Ensure DataFrame is not empty before proceeding
        if df.empty:
            self.logger.warning(f"DataFrame is empty for {sym} after conversion. Skipping further processing in fetch_data.")
            return data # Return data, which contains klines, but further processing is skipped.
        
        end_index = len(df) - 1

        self.logger.info("Fetching {} opening prices...".format(sym))
        opening_prices = df['open']
        opening_price = df.iloc[start_index]['open']
        self.logger.info("{} opening price: {}".format(sym, opening_price))
        data["opening_prices"] = opening_prices
        data["opening_price"] = opening_price

        self.logger.info("Fetching {} high prices...".format(sym))
        high_prices = df['high']
        # To get highest price over a specific period: high_prices.rolling(period_length).max().iloc[-1]
        highest_price = high_prices.max()
        self.logger.info("{} highest price: {}".format(sym, highest_price))
        data["high_prices"] = high_prices
        data["highest_price"] = highest_price
        
        self.logger.info("Fetching {} low prices...".format(sym))
        low_prices = df['low']
        lowest_price = low_prices.min()
        self.logger.info("{} lowest price: {}".format(sym, lowest_price))
        data["low_prices"] = low_prices
        data["lowest_price"] = lowest_price

        self.logger.info("Fetching {} closing prices...".format(sym))
        closing_prices = df['close']
        closing_price = closing_prices.iloc[-1]
        data["closing_prices"] = closing_prices
        self.logger.info("Latest {} closing price for interval: {}".format(sym, closing_price))
        data["closing_prices"] = closing_prices
        data["closing_price"] = closing_price

        # This should be the same as the last closing price
        self.logger.info("Fetching {} current price...".format(sym))
        current_price = self.client.get_symbol_ticker(sym)["price"]
        self.logger.info("Current {} price: {}".format(sym, current_price))
        data["current_price"] = current_price

        self.logger.info("Fetching {} volumes...".format(sym))
        volumes = df['volume']
        data["volumes"] = volumes

        self.logger.info("Fetching {} order book...".format(sym))
        order_book = self.client.get_order_book(symbol=sym, limit=Constants.DEFAULT_ORDERBOOK_DEPTH)
        data["order_book"] = order_book
        
        return data

    def convert_to_dataframe(self, klines):
        self.logger.info("Converting data to dataframe...")
        df = pd.DataFrame(klines,
                          columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignored'])
        df = df.drop(columns=['close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignored'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df

    def process_indicators(self, data):
        results = {}
        for indicator in self.indicators:
            try:
                # Store calculations
                calculations = indicator.calculate(data)
                results[indicator.name] = {"calculations": calculations}
                # Store signal, derived from the calculations
                results[indicator.name]["signal"] = indicator.decide_signal(calculations)
            except Exception as e:
                self.logger.error("Failed to calculate indicator '%s'. Error: %s", indicator.name, str(e))
                # Ensure there's an entry for the indicator even if it fails, to prevent KeyErrors later
                results[indicator.name] = {"calculations": None, "signal": Constants.SIGNAL_PROCESSING_ERROR}
        return results
    
    def process_sentiment_analyzer(self, symbol):
        results = {}
        for analyzer in self.sentiment_analyzers:
            try:
                # Store raw sentiment analysis
                sentiment_analysis_result = analyzer.analyze(symbol)
                results[analyzer.name] = {"sentiment": sentiment_analysis_result}
                # Store sentiment score, derived from the analysis result
                results[analyzer.name]["sentiment_score"] = analyzer.get_scores(sentiment_analysis_result)
            except Exception as e:
                self.logger.error("Failed to analyze sentiment for '%s' using '%s'. Error: %s", symbol, analyzer.name, str(e))
                # Ensure there's an entry for the analyzer even if it fails
                results[analyzer.name] = {"sentiment": None, "sentiment_score": Constants.SIGNAL_PROCESSING_ERROR}
        return results
    
    def execute_trades(self, symbol, decision_data): # New signature
        if not decision_data or "decision" not in decision_data or "quantity" not in decision_data:
            self.logger.warning(f"No valid decision data provided for {symbol}. Skipping trade.")
            return

        decision = decision_data["decision"]
        quantity = decision_data["quantity"]
        try:
            if decision == Constants.BUY_SIGNAL:
                # Ensure self.client is the actual Binance client instance
                order = self.client.order_market_buy(symbol=symbol, quantity=quantity) # Pass symbol here
            elif decision == Constants.SELL_SIGNAL:
                order = self.client.order_market_sell(symbol=symbol, quantity=quantity) # Pass symbol here
            else: # Assuming there could be a HOLD or other neutral decision
                self.logger.info(f"Decision for {symbol} is '{decision}'. No trade executed.")
                return # No order to place for HOLD or other decisions

            self.logger.info(f"Placed {decision} order for {quantity} of {symbol}: {order}")
        except Exception as e:
            self.logger.error("Failed to execute trade for '%s'. Decision data: %s. Error: %s", symbol, decision_data, str(e))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Binance Trading Bot API")
    parser.add_argument('-c', '--config', type=str, default=Constants.DEFAULT_CONFIG_FILENAME,
                        help='Path to config file to run',
                        required=False)
    args = parser.parse_args()

    api = TradingAPI(args.config)
    api.run()