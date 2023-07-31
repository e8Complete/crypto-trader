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
        # Fetch data
        for sym in self.config["symbols"]:
            with Pool() as pool:
                self.data[sym] = pool.apply(self.fetch_data, args=(sym, ))
                
        with Pool() as p:
            for sym in self.config["symbols"]:
                if sym not in self.data:
                    continue
                
                # Sentiment analysis
                self.data[sym]["sentiment"] = p.apply_async(self.process_sentiment_analyzer, args=(sym,)).get()
                # Indicator calculations, signal detection
                self.data[sym]["indicators"] = p.apply(self.process_indicators, args=(self.data[sym],))
                # Bing's latest market news
                self.data[sym]["market_news"] = get_market_news(sym, self.logger)
                # GPT trade decision
                self.data[sym]["decision"] = make_trade_decision(sym, self.data[sym])
                # Execute the trade based of decision
                self.execute_trades(self.data[sym]["decision"])
        
        save_data_to_csv(self.data)

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
            return data
        
        df = self.convert_to_dataframe(self.data[sym]["klines"])
        start_index = 0 
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
                results[indicator.name] = {"calculations": indicator.calculate(data) }
                results[indicator.name] = {"signal": indicator.decide_signal(results[indicator.name]["calculations"]) }
            except Exception as e:
                self.logger.error("Failed to calculate indicator '%s'. Error: %s", indicator.name, str(e))
        return results
    
    def process_sentiment_analyzer(self, symbol):
        results = {}
        for analyzer in self.sentiment_analyzers:
            try:
                results[analyzer.name] = { "sentiment": analyzer.analyze(symbol) }
                results[analyzer.name] = { "sentiment_score": analyzer.get_scores(results[analyzer.name]["sentiment"]) }
            except Exception as e:
                self.logger.error("Failed to analyze sentiment for '%s'. Error: %s", analyzer.name, str(e))
        return results
    
    def execute_trades(self, decision_dict):
        for symbol, data in decision_dict.items():
            decision = data["decision"]
            quantity = data["quantity"]
            try:
                if decision == Constants.BUY:
                    order = self.client.order_market_buy(symbol, quantity=quantity)
                elif decision == Constants.SELL:
                    order = self.client.order_market_sell(symbol, quantity=quantity)
                self.logger.info(f"Placed {decision} order for {symbol}: {order}")
            except Exception as e:
                self.logger.error("Failed to execute trade for '%s'. Error: %s", symbol, str(e))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Binance Trading Bot API")
    parser.add_argument('-c', '--config', type=str, default="config.yaml",
                        help='Path to config file to run',
                        required=False)
    args = parser.parse_args()

    api = TradingAPI(args.config)
    api.run()